#!/usr/bin/env python3
"""Filesystem ownership and recovery for the Affinity terminal commands."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

HOME = Path.home().resolve()
DATA = Path(os.environ.get('XDG_DATA_HOME', HOME / '.local/share')).absolute()
CONFIG = Path(os.environ.get('XDG_CONFIG_HOME', HOME / '.config')).absolute()
ROOT = Path(os.environ.get('OMARCHY_AFFINITY_ROOT', DATA / 'omarchy-affinity')).absolute()
CACHE = Path(os.environ.get('XDG_CACHE_HOME', HOME / '.cache')) / 'omarchy/affinity'
STATE = ROOT / 'state'
MANIFEST = STATE / 'ownership.json'
REPO = Path(__file__).resolve().parents[1]
ASSETS = {
    'desktop': (DATA / 'applications/affinity.desktop', REPO / 'default/applications/affinity.desktop'),
    'icon': (DATA / 'icons/hicolor/scalable/apps/affinity.svg', REPO / 'default/applications/icons/affinity.svg'),
    'mime': (DATA / 'mime/packages/omarchy-affinity.xml', REPO / 'default/mime/omarchy-affinity.xml'),
    'hypr': (CONFIG / 'hypr/affinity.lua', REPO / 'default/hypr/apps/affinity.lua'),
}
MIMES = ['application/x-affinity', 'application/x-affinity-photo', 'application/x-affinity-designer',
         'application/x-affinity-publisher', 'image/vnd.adobe.photoshop']


def run(*args, **kw):
    return subprocess.run(args, check=True, text=True, **kw)


def digest(path):
    with path.open('rb') as stream:
        result = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
        return result.hexdigest()


def read_manifest():
    if MANIFEST.exists():
        value = json.loads(MANIFEST.read_text())
        if value.get('root') != str(ROOT.resolve()):
            raise RuntimeError('Installation manifest belongs to another location.')
        # Recover ownership after an interrupted package stage, even if the
        # worker died before it could update the JSON manifest.
        for log in STATE.glob('packages-*.log'):
            added = re.findall(r'\[ALPM\] installed ([a-zA-Z0-9@._+\-]+) ', log.read_text())
            value['packages'] = sorted(set(value['packages']) | set(added))
        return value
    return {'version': 1, 'root': str(ROOT.resolve()), 'packages': [], 'assets': {}}


def save(value):
    STATE.mkdir(parents=True, exist_ok=True)
    temp = MANIFEST.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(MANIFEST)


def validate():
    recovery = HOME / 'Affinity Backups'
    if recovery.resolve() != recovery:
        raise RuntimeError('Recovery directory must not traverse symlinks.')
    # These are private directories, never arbitrary shared roots or symlink aliases.
    protected = {HOME, DATA.resolve(), CONFIG.resolve(), Path('/'), Path('/usr'), Path('/tmp'),
                 Path(os.environ.get('XDG_CACHE_HOME', HOME / '.cache')).resolve(),
                 (HOME / '.local').resolve(), (HOME / 'Affinity Backups').resolve(), REPO}
    for path in [ROOT, CACHE]:
        actual = path.resolve()
        if not path.is_absolute() or actual in protected or any(actual in p.parents for p in protected):
            raise RuntimeError(f'Unsafe installation directory: {path}')
        if path != actual:
            raise RuntimeError(f'Installation directories must not traverse symlinks: {path}')
    for path in [STATE, ROOT / 'prefix', ROOT / 'wine']:
        if path.is_symlink():
            raise RuntimeError(f'Private installation directory is a symlink: {path}')
    if ROOT == CACHE or ROOT in CACHE.parents or CACHE in ROOT.parents:
        raise RuntimeError('Installation and cache directories must be separate.')
    if ROOT.exists() and not MANIFEST.exists() and not (ROOT / 'prefix/system.reg').exists():
        if any(ROOT.iterdir()):
            raise RuntimeError('Unrecognized nonempty installation directory; refusing to adopt it.')


def running():
    found = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            environment = (proc / 'environ').read_bytes().split(b'\0')
            if os.fsencode('WINEPREFIX=' + str(ROOT / 'prefix')) not in environment:
                continue
            command = (proc / 'comm').read_text().strip()
            if any(word in command.lower() for word in ['wine', 'affinity', '.exe']):
                found.append(f'{command} ({proc.name})')
        except (OSError, ProcessLookupError):
            continue
    return found


def check_idle():
    active = running()
    if active:
        raise RuntimeError('Close Affinity and its Wine dialogs, then retry. Running: ' + ', '.join(active))


def required_packages():
    # Use the distro's dependency metadata without installing a duplicate Wine.
    info = run('pacman', '-Si', 'wine', capture_output=True,
               env={**os.environ, 'LC_ALL': 'C'}).stdout
    match = re.search(r'^Depends On\s*:\s*(.*(?:\n[ \t]+.*)*)', info, re.MULTILINE)
    if not match:
        raise RuntimeError('Cannot read Wine runtime dependencies from the package database.')
    required = match[1].split()
    required.extend(line.strip() for line in (REPO / 'default/affinity/runtime-packages').read_text().splitlines()
                    if line.strip() and not line.startswith('#'))
    return sorted(set(required) - {'None'})


def missing_packages():
    requirements = required_packages()
    result = subprocess.run(['pacman', '-T', *requirements], capture_output=True, text=True)
    if result.returncode not in {0, 127}:
        raise RuntimeError('Could not check system runtime dependencies: ' + result.stderr)
    missing = [re.split(r'[<>=]', line, maxsplit=1)[0] for line in result.stdout.splitlines() if line.strip()]
    if any(not re.fullmatch(r'[a-zA-Z0-9@_+][a-zA-Z0-9@._+\-]*', name) for name in missing):
        raise RuntimeError('Package database returned an invalid dependency name.')
    return sorted(set(missing))


def packages():
    installed = set(run('pacman', '-Qq', capture_output=True).stdout.splitlines())
    missing = missing_packages()
    if not missing:
        return
    manifest = read_manifest()
    # A dedicated pacman log identifies this transaction's added dependencies,
    # including partial failures. Never infer ownership from global orphans.
    log = STATE / f'packages-{time.time_ns()}.log'
    STATE.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(['sudo', '-n', 'pacman', '--logfile', str(log),
                             '-S', '--noconfirm', '--needed', *missing])
    if log.exists():
        added = re.findall(r'\[ALPM\] installed ([a-zA-Z0-9@._+\-]+) ', log.read_text())
        manifest['packages'] = sorted(set(manifest['packages']) | (set(added) - installed))
        save(manifest)
    if result.returncode:
        raise RuntimeError('Package installation failed. Its completed additions are recorded for removal.')


def capture():
    manifest = read_manifest()
    fresh = not (ROOT / 'prefix/system.reg').exists()
    desktop = ASSETS['desktop'][0]
    legacy_owned = not MANIFEST.exists() and not fresh and desktop.is_file() and 'Exec=omarchy-launch-affinity' in desktop.read_text()
    manifest.setdefault('fresh', fresh)
    for name, (target, _) in ASSETS.items():
        if name in manifest['assets']:
            entry = manifest['assets'][name]
            if target.is_symlink():
                raise RuntimeError(f'Refusing to overwrite symlink: {target}')
            if target.exists() and entry.get('installed_hash') and digest(target) != entry['installed_hash']:
                backup = STATE / 'previous' / name
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                entry['previous'] = name
            entry['installed_hash'] = digest(ASSETS[name][1])
            continue
        if target.is_symlink():
            raise RuntimeError(f'Refusing to overwrite symlink: {target}')
        entry = {'path': str(target), 'previous': None, 'installed_hash': digest(ASSETS[name][1])}
        if target.exists():
            backup = STATE / ('legacy-assets' if legacy_owned else 'previous') / name
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, backup)
            if not legacy_owned:
                entry['previous'] = name
        manifest['assets'][name] = entry
    config = CONFIG / 'hypr/hyprland.lua'
    if config.exists() and 'hypr_config_before' not in manifest:
        previous = STATE / 'previous/hyprland.lua'
        previous.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(config, previous)
        manifest['hypr_config_before'] = True
    if 'mime_defaults' not in manifest:
        manifest['mime_defaults'] = {mime: run('xdg-mime', 'query', 'default', mime, capture_output=True).stdout.strip() for mime in MIMES}
    save(manifest)


def seal():
    manifest = read_manifest()
    for name, (target, _) in ASSETS.items():
        if target.exists():
            manifest['assets'][name]['installed_hash'] = digest(target)
    # Only a fresh installation can establish which files are disposable runtime.
    # Existing installations may contain user work anywhere; retain it all.
    if manifest.get('fresh') and 'runtime' not in manifest:
        runtime = {}
        prefix = ROOT / 'prefix'
        documents = {'.af', '.afphoto', '.afdesign', '.afpub', '.psd', '.svg', '.pdf', '.png', '.jpg', '.jpeg', '.tif', '.tiff'}
        for folder in ['drive_c/windows', 'drive_c/Program Files', 'drive_c/Program Files (x86)']:
            for base, dirs, files in os.walk(prefix / folder, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
                for filename in files:
                    path = Path(base) / filename
                    if path.is_file() and not path.is_symlink() and path.suffix.lower() not in documents:
                        runtime[str(path.relative_to(prefix))] = digest(path)
        manifest['runtime'] = runtime
    save(manifest)


def removable_packages(owned):
    candidates = list(owned)
    while candidates:
        try:
            run('pacman', '-R', '--print', '--print-format', '%n', *candidates,
                capture_output=True, env={**os.environ, 'LC_ALL': 'C'})
            return candidates
        except subprocess.CalledProcessError as error:
            required = set(re.findall(r"removing ([a-zA-Z0-9@._+\-]+) breaks dependency", error.stderr or ''))
            if not required.intersection(candidates):
                raise RuntimeError('Could not verify dependency removal: ' + (error.stderr or str(error))) from error
            candidates = [name for name in candidates if name not in required]
    return []


def removal_plan(manifest):
    installed = set(run('pacman', '-Qq', capture_output=True).stdout.splitlines())
    owned = sorted(installed.intersection(manifest['packages']))
    print(f'Installation: {ROOT}\nPrivate cache: {CACHE}\nRecovery: {HOME / "Affinity Backups"}')
    removable = removable_packages(owned)
    retained = sorted(set(owned) - set(removable))
    print('Packages still needed by other apps: ' + ', '.join(retained)) if retained else None
    print('Recorded packages: ' + (', '.join(owned) or 'none (preexisting or untracked packages are kept)'))
    print('App data, saved files, registry and changed runtime files will be preserved.')
    if not manifest.get('runtime'):
        print('Legacy installation: the complete prefix will be preserved because no original file inventory exists.')
    return removable


def restore_integrations(manifest):
    for name, entry in manifest.get('assets', {}).items():
        target = ASSETS[name][0]
        if str(target) != entry['path']:
            raise RuntimeError('Desktop locations changed since installation; restore the original XDG paths.')
        if target.is_symlink():
            continue
        if target.exists() and digest(target) != entry.get('installed_hash'):
            print(f'Keeping customized integration: {target}')
            continue
        if entry['previous']:
            shutil.copy2(STATE / 'previous' / name, target)
        else:
            target.unlink(missing_ok=True)
    config = CONFIG / 'hypr/hyprland.lua'
    if config.exists():
        text = config.read_text()
        config.write_text(''.join(line for line in text.splitlines(True) if line.rstrip() != 'require("default.hypr.require_optional").module("hypr.affinity") -- omarchy-affinity'))
    restore_mime_defaults(manifest)
    # Compatibility cleanup for the former installer. Leave shared Creative parents.
    menu = CONFIG / 'omarchy/extensions/omarchy-menu.jsonc'
    if menu.exists():
        menu.write_text(''.join(line for line in menu.read_text().splitlines(True)
                               if not re.match(r'\s*"(?:install|remove)\.creative\.affinity"\s*:', line)))


def restore_mime_defaults(manifest):
    # Remove just this desktop id from MIME association lists, retaining other
    # applications and unrelated sections. Restore old defaults only if still ours.
    for mimefile in [CONFIG / 'mimeapps.list', DATA / 'applications/mimeapps.list']:
        if not mimefile.exists():
            continue
        lines = []
        section = ''
        for line in mimefile.read_text().splitlines(True):
            if line.startswith('['):
                section = line.strip()
            if '=' in line and not line.lstrip().startswith('#'):
                key, value = line.rstrip('\n').split('=', 1)
                entries = value.split(';')
                if 'affinity.desktop' in entries:
                    entries = [v for v in entries if v and v != 'affinity.desktop']
                    previous = manifest.get('mime_defaults', {}).get(key)
                    if section == '[Default Applications]' and value.startswith('affinity.desktop') and previous and previous != 'affinity.desktop':
                        entries.insert(0, previous)
                    if not entries:
                        continue
                    line = key + '=' + ';'.join(dict.fromkeys(entries)) + ';\n'
            lines.append(line)
        mimefile.write_text(''.join(lines))


def remove(dry_run=False):
    validate()
    manifest = read_manifest()
    owned = removal_plan(manifest)
    if dry_run:
        return
    check_idle()
    if ROOT.exists() and not MANIFEST.exists():
        raise RuntimeError('Run the installer once to record this legacy installation before removing it.')
    for name, entry in manifest.get('assets', {}).items():
        if str(ASSETS[name][0]) != entry['path']:
            raise RuntimeError('Desktop locations changed since installation; restore the original XDG paths.')
    # pacman's normal -R dependency check is authoritative. -Rs/-Rns could remove
    # dependencies that predate this installer, so we never use them.
    recovery = HOME / 'Affinity Backups' / time.strftime('%Y-%m-%d_%H-%M-%S')
    if recovery.parent.is_symlink() or recovery.parent.resolve() != recovery.parent:
        raise RuntimeError('Recovery directory must not traverse a symlink.')
    if ROOT.exists():
        recovery.mkdir(parents=True, mode=0o700, exist_ok=False)
        prefix = ROOT / 'prefix'
        # Copy without following Wine's links to Documents, Desktop, or Z:.
        # Verify every preserved regular file before any source directory deletion.
        runtime = manifest.get('runtime', {})
        if prefix.exists():
            def ignore(base, names):
                excluded = []
                for name in names:
                    path = Path(base) / name
                    relative = str(path.relative_to(prefix))
                    if relative in runtime and not path.is_symlink() and path.is_file() and digest(path) == runtime[relative]:
                        excluded.append(name)
                return excluded
            shutil.copytree(prefix, recovery / 'prefix', symlinks=True, ignore=ignore)
            for base, _, files in os.walk(recovery / 'prefix', followlinks=False):
                for name in files:
                    target = Path(base) / name
                    if not target.is_symlink() and digest(target) != digest(prefix / target.relative_to(recovery / 'prefix')):
                        raise RuntimeError(f'Recovery verification failed: {target}')
        for child in ROOT.iterdir():
            if child.name not in {'prefix', 'wine', 'state'}:
                destination = recovery / 'extra' / child.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                if child.is_symlink():
                    destination.symlink_to(os.readlink(child))
                elif child.is_dir():
                    shutil.copytree(child, destination, symlinks=True)
                else:
                    shutil.copy2(child, destination)
                if not destination.is_symlink():
                    pairs = [(child, destination)] if destination.is_file() else [
                        (child / path.relative_to(destination), path)
                        for base, _, files in os.walk(destination, followlinks=False)
                        for path in [Path(base) / name for name in files] if not path.is_symlink()]
                    for origin, target in pairs:
                        if digest(origin) != digest(target):
                            raise RuntimeError(f'Recovery verification failed: {target}')
        if STATE.exists():
            shutil.copytree(STATE, recovery / 'state', symlinks=True)
        # Confirm all copied files, including state and unexpected root folders.
        for origin, destination in [(STATE, recovery / 'state')]:
            if destination.exists():
                for base, _, files in os.walk(destination, followlinks=False):
                    for filename in files:
                        target = Path(base) / filename
                        if not target.is_symlink() and digest(target) != digest(origin / target.relative_to(destination)):
                            raise RuntimeError(f'Recovery verification failed: {target}')
        (recovery / 'README.txt').write_text('Affinity recovery data. Wine symlinks were not followed.\nDocuments saved outside Wine remain in their original locations.\nCopy the contents of prefix into a new Affinity prefix to restore settings/files.\nUnchanged runtime files from a fresh install were omitted and must be reinstalled.\n')
    # Recheck after copying: never delete data beneath a newly opened application.
    check_idle()
    if owned:
        run('sudo', '-n', 'pacman', '-R', '--noconfirm', *owned)
    restore_integrations(manifest)
    for path in [ROOT, CACHE]:
        if path.exists():
            shutil.rmtree(path)
    print(f'Removed Affinity. Recovery data: {recovery}' if recovery.exists() else 'Affinity is not installed.')


def prune_runtime():
    wine = ROOT / 'wine'
    reclaimed = 0
    headers = wine / 'include'
    if headers.exists() and not headers.is_symlink():
        reclaimed += sum(path.stat().st_size for path in headers.rglob('*') if path.is_file() and not path.is_symlink())
        shutil.rmtree(headers)
    for base, dirs, files in os.walk(wine / 'lib', followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(base) / name).is_symlink()]
        for name in files:
            path = Path(base) / name
            if path.suffix == '.a':
                if not path.is_symlink():
                    reclaimed += path.stat().st_size
                path.unlink()
    private_downloads = CACHE / 'winetricks'
    if private_downloads.is_dir() and not private_downloads.is_symlink():
        shutil.rmtree(private_downloads)
    print(f'Removed {reclaimed / 1024 / 1024:.1f} MiB of development headers/import libraries and cleared private setup downloads.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'idle', 'packages', 'needs-packages', 'capture', 'seal', 'remove', 'plan', 'prune-runtime', 'restore-mime'])
    args = parser.parse_args()
    validate()
    if args.action == 'check':
        return
    if args.action == 'idle':
        check_idle()
    elif args.action == 'needs-packages':
        sys.exit(0 if missing_packages() else 1)
    elif args.action == 'packages':
        packages()
    elif args.action == 'capture':
        capture()
    elif args.action == 'seal':
        seal()
    elif args.action == 'restore-mime':
        restore_mime_defaults(read_manifest())
    elif args.action == 'prune-runtime':
        prune_runtime()
    else:
        remove(dry_run=args.action == 'plan')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f'Affinity: {error}', file=sys.stderr)
        sys.exit(1)
