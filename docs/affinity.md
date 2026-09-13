# Affinity on Omarchy

`omarchy-install-affinity` puts Canva's unified Affinity app (Photo, Designer and Publisher personas; v3, free tier) on an Omarchy box under a patched Wine, with DXVK doing the rendering, and wires it into Hyprland like any other app: launcher entry, file associations for `.afphoto`/`.afdesign`/`.afpub`/`.psd`, window rules, HiDPI, menu rows. This page covers what it does, what it decided and why, what is fragile, how to report problems, and the licence situation. The raw inventory of what upstream AffinityOnLinux does is in [`NOTES.md`](../NOTES.md).

## Commands

| Command | What it does |
|---|---|
| `omarchy-install-affinity` | Installs packages, the patched Wine, the prefix, the app, and every integration point. Rerunnable: each step checks its own marker and skips. |
| `omarchy-launch-affinity [files...]` | Launches Affinity with the DXVK environment; files are mapped to `Z:` paths. `--winecfg` opens winecfg for this prefix, `--verbose` keeps Wine's errors on the terminal. |
| `omarchy-remove-affinity` | Kills the prefix's wineserver, deletes the prefix, Wine, cache, launcher, icon, MIME entries, Hyprland fragment and menu rows. Offers to drop winetricks/cabextract. |

Menu: **Install > Creative > Affinity** and **Remove > Creative > Affinity**.

## Where things live

```
~/.local/share/omarchy/affinity/
  wine/      ElementalWarrior Wine 11.12 (vendored per user; .omarchy-version marks it)
  prefix/    WINEPREFIX; never ~/.wine
  state/     dpi, registry-done, per-step logs (winetricks-*.log, affinity-setup.log)
~/.cache/omarchy/affinity/   downloads (Wine tarball kept; installer .exe deleted after use)
~/.local/share/applications/affinity.desktop
~/.local/share/icons/hicolor/scalable/apps/affinity.svg
~/.local/share/mime/packages/omarchy-affinity.xml
~/.config/hypr/affinity.lua              + one require line appended to ~/.config/hypr/hyprland.lua
~/.config/omarchy/extensions/omarchy-menu.jsonc   four rows appended
```

The repo mirrors Omarchy's own tree (`bin/`, `default/applications`, `default/hypr/apps`, `default/omarchy`) so the files can be moved into `basecamp/omarchy` verbatim later; until then the installer copies them into the user's home.

## Runner decision

Three options were on the table. The choice is **3: ElementalWarrior's Wine fork, prebuilt, vendored per user**, with DXVK from winetricks.

1. **umu-launcher + unmodified GE-Proton.** Rejected for now, not verified. GE-Proton11-6 (2026-08-28) release notes say nothing about WinRT, winmd or Affinity; the umu database has no Affinity entry; umu-protonfixes has no Affinity fix. The upstream project's stock-Wine path (`AffinityWine10.17.sh`) needs a wintypes shim plus a merged `Windows.winmd` from the windows-rs project, and upstream's own known-issues page documents that this combination fails Publisher's `Windows.Services.Store` licence check. Nothing in that picture suggests stock Proton runs the full v3 suite, and no box with a GPU was available to test it in this pass. Worth re-testing when Wine's own generated winmd files (shipped since 10.x) mature.
2. **umu-launcher + an Affinity-patched Proton.** `Arecsu/proton-affinity` exists (22 patches on proton-cachyos, including XDG portal file dialogs and Wayland fixes) but ships no binaries and its packaging script is marked broken. Building Proton in the SteamRT SDK from an installer is not an end-user experience.
3. **ElementalWarrior Wine.** Known good; what every working guide and installer uses. No AUR package packages this fork (web search found `affinity-appimage-bin` and `affinity-bin`, which wrap upstream's AppImage/GUI installer, not the runner; aur.archlinux.org was unreachable from the authoring session, so re-check). Building from source takes 30+ minutes and a large toolchain, so the installer downloads the tarball that upstream's own installer downloads (`ryzendew/Affinity-Wine-Builder` release 11.12, 111 MB) and verifies a pinned sha256.

Trade-off: portability lost (glibc >= 2.38 required, fine on Arch), simplicity for end users gained. Bumping Wine means changing three values in `bin/omarchy-affinity-env`; the installer replaces the vendored build when the version differs.

Why the prebuilt matters, concretely: the 11.12 build is WoW64 (no lib32 packages needed), ships its own `share/wine/winmd/*.winmd` files and a patched `wintypes.dll`, so the WinMetadata download that older guides require is unnecessary. Those WinMetadata archives are Microsoft-copyrighted files lifted from a Windows install with no redistribution licence; not downloading them is also the licence-sane answer. The archive's checksum is recorded in `NOTES.md` in case a future Wine drop regresses.

## What the prefix gets

- Arch packages: `wine` (runtime-library carrier for the vendored build; skipped when `wine-staging` from Lutris is present), `winetricks`, `cabextract`, `unzip`, `vulkan-icd-loader`. GPU Vulkan drivers come from Omarchy's own hardware setup.
- `wineboot` with Mono and Gecko disabled (no dialogs), then winetricks `dotnet48 corefonts vcrun2022 msxml3 msxml6 tahoma dxvk renderer=vulkan win11`, unattended, one log per verb under `state/`. `dotnet48` is the slow one (5-10 minutes).
- Registry: `Drivers\Graphics=x11` (stay on XWayland; the Hyprland rules and upstream testing assume it), the AffinityOnLinux dark theme for Win32 dialogs, and `Control Panel\Desktop\LogPixels` set from the focused monitor's Hyprland scale (2x monitor gives 192 DPI). The launcher re-applies DPI when the scale changes; `OMARCHY_AFFINITY_DPI=144` pins it.
- Launch env: `WINEDEBUG=-all`, `winemenubuilder.exe=d` (Wine does not get to write launcher or MIME entries), `DXVK_ASYNC=0`, `DXVK_LOG_LEVEL=none`, and upstream's `DXVK_CONFIG` on AMD GPUs.
- OpenCL is off by omission: no vkd3d-proton, no `d3d12` overrides, no OpenCL ICD. Affinity then has nothing to accelerate with and stays on DXVK. Leave **Preferences > Performance > Hardware Acceleration** unticked.

Not carried over from upstream, on purpose: WebView2 (broken under Wine regardless; only in-app Help and Canva sign-in use it), AffinityPluginLoader/WineFix (a candidate follow-up: it fixes "preferences not saving"), the local `mscms.dll` shim, the JPEG XL profile quarantine.

## Hyprland integration

`default/hypr/apps/affinity.lua`: every Affinity window has the XWayland class `affinity.exe` (the installer wizard: `affinity x64.exe`). Wine marks splash, progress and modal dialogs as transient and Hyprland floats those itself; the rules centre anything floating, opt the app out of Omarchy's default translucency (colour work), float a list of dialog titles as a fallback, and set `focus_on_activate=false` so a late dialog does not drag focus across workspaces. The document window tiles. `Super+Q` sends a close request that Affinity answers with its own save prompt.

The window classes and titles were taken from upstream's `StartupWMClass` and Wine's naming convention, not captured with `hyprctl clients` on a live install. If a dialog tiles or a splash sits off-centre, run `hyprctl clients -j | jq '.[] | select(.class | test("affinity"))'` while it is open and add the title to the fallback list.

## Wine-fragile

- **The vendor installer.** It is a normal Windows wizard with no silent switch; the only clicking in the whole install. Upstream warns that a spurious error at the end should be answered "No" so it does not roll back. `state/affinity-setup.log` has Wine's output.
- **winetricks.** `dotnet48` and `dxvk` download from Microsoft and GitHub; both can fail on flaky networks. Reruns resume from the failed verb because winetricks logs finished verbs in `prefix/winetricks.log`.
- **Undocking panels.** Upstream's known-issues page: dragging UI panels out of the main window can crash Affinity, a Wine window-management limitation. Keep panels docked or import a Studio layout.
- **Sign-in and Help.** Both need WebView2, which does not work under Wine. The app works offline without an account on the free tier.
- **The download URL.** `https://downloads.affinity.studio/Affinity%20x64.exe` is what upstream fetches; it was not reachable from the authoring session, so it is unverified here. If Canva moves it, `AFFINITY_INSTALLER_URL` in `bin/omarchy-affinity-env` is the one line to change; dropping an installer at `~/.cache/omarchy/affinity/Affinity-x64.exe` also works.
- **DPI.** Assumes Omarchy's `xwayland.force_zero_scaling = true`. With that off, halve the DPI via `OMARCHY_AFFINITY_DPI`.

## Reporting bugs

Run `omarchy-launch-affinity --verbose` from a terminal and attach the output, plus `state/affinity-setup.log` or the failing `state/winetricks-*.log`, the GPU (`omarchy-hw-nvidia; lspci | grep -i vga`), `hyprctl monitors`, and the Wine version (`~/.local/share/omarchy/affinity/wine/bin/wine --version`). Say whether the same document misbehaves in the upstream AffinityOnLinux installer; if it does, the bug belongs there (or in ElementalWarrior's Wine), not in this installer.

## Licence

This repo ships an installer, window rules, a desktop entry, and a MIME definition. It does not ship Affinity. Affinity is proprietary software from Canva/Serif; the installer downloads it from Canva's own server and the user accepts Canva's terms in the wizard. The free tier is what gets installed; paid features are Canva's business. The Affinity icon is Canva's trademark, vendored from AffinityOnLinux the same way upstream ships it, for the launcher entry only. The patched Wine is LGPL (Wine) plus ElementalWarrior's patches, downloaded as a release tarball from `ryzendew/Affinity-Wine-Builder`. No Windows system files are downloaded.

## Test checklist

Run on 2026-09-13 from a remote container: no Arch, no Wine, no GPU, no Hyprland, and `downloads.affinity.studio` blocked by the network policy. Nothing below was exercised on real hardware; what did run is the static suite in `test/affinity` (bash syntax, metadata, desktop/MIME/JSONC validity, the launcher's not-installed path, remove on an empty home, and the menu append/remove round trip). Every unchecked item needs a real Omarchy box; results go here.

- [ ] Fresh Omarchy VM/box: installer completes with no prompts beyond sudo and the vendor wizard
- [ ] App launches in < 15 s cold, no dead splash
- [ ] Open, edit, export a `.afphoto` and a `.psd`
- [ ] Vulkan renderer active (Preferences > Performance shows the GPU under DXVK); brushes don't lag
- [ ] Save/Open dialogs float, main window tiles, Super+Q closes cleanly
- [ ] Clipboard copy/paste to and from a native Wayland app
- [ ] HiDPI: text isn't tiny on a 2x display
- [ ] Rerun installer: no-op; uninstall: prefix and entries gone
- [x] Static: `test/affinity` passes
