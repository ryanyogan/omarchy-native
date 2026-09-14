# Affinity on Omarchy

This installs Canva's unified Affinity 3 application in a private Wine prefix.
The Vector, Pixel, and Layout workspaces are part of that application. It is
still a Windows application: Hyprland manages its XWayland windows.

## Commands

| Command | Behavior |
|---|---|
| `omarchy-setup-affinity` | Opens a themed Omarchy terminal with install/repair and uninstall choices. |
| `omarchy-setup-affinity --install` | Opens the installer directly. |
| `omarchy-install-affinity` | Runs in the current terminal; useful for installation logs and automation. |
| `omarchy-launch-affinity` | Launches the private Wine/DXVK application. |
| `omarchy-launch-affinity --winecfg` | Opens settings for this prefix only. |
| `omarchy-launch-affinity --verbose` | Keeps diagnostic Wine output on the terminal. |
| `omarchy-launch-affinity --desktop` | Experimental contained Wine desktop, 1440×900; not the default. |
| `omarchy-remove-affinity --dry-run` | Shows the paths and removable, recorded packages without changing anything. |
| `omarchy-setup-affinity --uninstall` | Presents the removal plan, then backs up data and uninstalls. |
| `omarchy-remove-affinity --yes` | Runs the same removal without the interactive confirmation. |

Menu-bar integration is deferred. The old menu fragment remains in the repo for
future work; the installer no longer edits the Omarchy menu.

**Document handoff is temporarily guarded.** Passing a file from the file manager
can crash the running application in its Windows Runtime command-line handler.
The launcher explains this instead of sending that command. Use **File > Open**
inside Affinity. The installer registers `.af`, `.afphoto`, `.afdesign`, `.afpub`
and PSD support but does not take over their default applications. It restores
any defaults taken by the old installer when a previous association is recorded.
Developers can opt into the failing path with `--experimental-file-open`.

## Installation and progress

The terminal uses Omarchy's `xdg-terminal-exec`, `org.omarchy.terminal` window
class, current gum theme, and gum choices. A single progress bar counts completed
setup stages; it is not an estimate of remaining time. .NET setup can take ten
minutes or longer. Wine, download, and package output goes into a private log;
failures show the log location and an actionable final line.

The vendor's Affinity setup wizard still requires interaction. Keep its default
installation location. On the tested x64/WoW64 system it warned that a native CPU
installer exists; continuing with Ignore allowed installation. We have not
established why the vendor displays that warning.

Stages resume from the Wine version marker, completed winetricks verbs, and the
installed application. Failed downloads never become completed installer files.
The vendor URL is unversioned, so vendor downloads restart instead of combining
potentially different releases. Wine and winetricks downloads are checksum-pinned.

System package authentication happens in the visible terminal. Setup and removal
have an exclusive operation lock; launches hold a shared lock. Removal also
checks for Wine processes using the prefix and asks you to close the app. It
never uses a prefix-wide kill to dispose of unsaved work.

## Runtime and efficiency

- ElementalWarrior Wine 11.12 is downloaded from the pinned
  [Affinity-Wine-Builder release](https://github.com/ryzendew/Affinity-Wine-Builder/releases/tag/11.12).
  It is a WoW64 build and does not need lib32 packages.
- The installer reads Arch Wine's mandatory dependencies from the local package
  repository database and adds the libraries in
  [`runtime-packages`](../default/affinity/runtime-packages). It **does not install
  a duplicate system Wine**. GPU drivers remain Omarchy's responsibility.
- [Winetricks 20260125](https://github.com/Winetricks/winetricks/tree/20260125)
  is checksum-pinned and kept privately in the application state directory.
  `OMARCHY_AFFINITY_WINETRICKS` can select another executable for development.
- Setup installs `dotnet48 corefonts vcrun2022 msxml3 msxml6 tahoma dxvk
  renderer=vulkan win11`. Successful setup deletes private winetricks downloads,
  Wine development headers, and import libraries. Runtime DLLs remain intact.
- XWayland is the default. Wine uses the focused monitor's scale to choose DPI;
  on the tested 2× monitor this is 192 DPI. The cached value avoids starting Wine
  just to write an unchanged registry setting on each launch.
- DXVK renders through Vulkan. The existing upstream AMD workaround remains;
  we have not established that changing it improves this workload. OpenCL is
  not configured or verified by this installer.

These changes save disk space. Removing unloaded DLLs or development headers
does not inherently reduce application memory or improve drawing latency. See
[the audit](audit.md) for measurements and remaining work.

## Files and ownership

```
~/.local/share/omarchy-affinity/
  wine/       patched runtime, without development headers/import libraries
  prefix/     private Windows environment; never ~/.wine
  state/      ownership.json, private winetricks, settings, backups and logs
~/.cache/omarchy/affinity/              private downloads
~/.local/share/applications/affinity.desktop
~/.local/share/icons/hicolor/scalable/apps/affinity.svg
~/.local/share/mime/packages/omarchy-affinity.xml
~/.config/hypr/affinity.lua
~/Affinity Backups/                    verified recovery data after removal
```

`XDG_DATA_HOME`, `XDG_CACHE_HOME`, and `XDG_CONFIG_HOME` are honored.
`OMARCHY_AFFINITY_ROOT` overrides the private installation root. Use the same
values for all commands. Shared roots, overlapping install/cache roots, and
symlinked installation directories are refused before mutation. The packaged
Omarchy directory, `/usr/share/omarchy`, is never modified.

An ownership manifest records added system packages, previous desktop assets,
previous MIME defaults, and installed asset hashes. Private pacman transaction
logs recover package ownership after an interrupted installation. Existing
packages are not claimed. Concurrent unrelated package transactions cannot be
mistaken for ours because each installation transaction has its own log.

## Uninstall and recovery

1. Check the operation lock, active processes, paths, and package dependencies.
2. Copy data into a private timestamped directory under `~/Affinity Backups/`.
   Preserve the registry, user data, unexpected files, and changes to inventoried
   runtime files. Copy Wine's links to Documents/Desktop/Z: as links without
   following them. Verify copied regular files before removing the originals.
3. Remove only packages recorded as added by this installer, excluding packages
   now required by another app. Use pacman's normal dependency checks; never
   recursively remove global orphans or use `--nodeps`.
4. Restore prior desktop assets where appropriate, preserve later custom edits,
   remove this application's integration, then remove its private root/cache.

A fresh install inventories disposable runtime files; unchanged copies are not
included in the recovery backup. A legacy install has no trustworthy original
inventory, so its **entire prefix** is preserved. That backup includes Windows
runtime files and is larger, deliberately. It is recovery data, separate from
the removed active installation.

User documents outside the prefix remain in place. The manager commands and
this repository remain available for reinstalling. Shared preexisting caches
(such as an old `~/.cache/winetricks`) are not deleted without ownership evidence.
An incomplete backup or package-check failure leaves the installation in place.

To restore after reinstalling, close Affinity and copy the saved prefix contents
into the new prefix. Review the backup's README and registry before restoring
across application versions; Wine/app data migration is not guaranteed.

## Window behavior

The main document window tiles. Affinity windows are opaque for color work;
known named dialogs float and center. **Menus and tool flyouts retain their
application-requested positions.** A broad center-all-floating rule caused the
original nearly unusable hover behavior. An empty title or X11 `DIALOG` type is
not enough to distinguish a menu from a dialog.

Untitled floating windows now avoid initial focus, pointer-follow focus, and
compositor animations/decorations. Live tooltips stayed anchored without stealing
editor focus. Welcome is also untitled and currently shares those rules: its
independent sizing, centering, and focus handling remain unfinished. The intended
layout is **floating Welcome, tiled editor**.

The launcher scales the inherited Xcursor size to Wine DPI without changing the
desktop theme or global settings: 24 desktop pixels become 48 physical pixels
at 192 DPI. `OMARCHY_AFFINITY_CURSOR_SIZE` overrides the physical size (1–256).
Restart Affinity to apply launcher environment changes.

Hyprland already manages native Wayland, native Linux X11, and Wine windows.
Changing Wine's driver or using a Wine desktop does not turn Affinity into a
Linux executable. XWayland remains the verified path. Native Wine Wayland and
contained-desktop behavior need separate real-document regression testing.

## Known limits and diagnostics

- File-manager document handoff is guarded pending a complete WinRT fix.
- Canva sign-in and embedded Help/WebView2 have not passed testing.
- Color-profile APIs report unimplemented operations. Color-critical output
  needs validation; opacity alone does not establish accurate color management.
- Tablet/Wintab support, panel undocking, preference persistence, large PSDs,
  export fidelity, and prolonged editing sessions remain unverified.
- The launcher assumes Omarchy's XWayland zero-scaling configuration. Use
  `OMARCHY_AFFINITY_DPI` to pin DPI for a different setup.

Use `omarchy-launch-affinity --verbose` for diagnostics, `test/affinity-profile`
for a read-only CPU/PSS sample, and `test/affinity-interactions` for the documented
live menu regression. `test/affinity` runs static validation and isolated lifecycle
regressions without Wine or a desktop.
`test/affinity-ux` checks live tooltip focus, placement, and cursor dimensions with
the Vector studio visible on the documented single 2× display. These live scripts
temporarily move the pointer; dismiss Welcome and dialogs before running them.
The latest menu rerun failed on its second opening; see
[session history](session-history.md) for the checkpoint and remaining work.

Affinity is proprietary and downloaded from Canva; its terms and account
requirements apply. Wine is LGPL; winetricks has its own LGPL license. The
experimental WinRT investigation is documented under
[`experiments/winrt`](../experiments/winrt/README.md) and is not installed.
