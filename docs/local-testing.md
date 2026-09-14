# Local hardware testing — 2026-09-13

Checkout: `67b78b5` plus the local fixes described below.

## Machine

- Omarchy `4.0.3-1`, Arch Linux `7.2.3-arch1-3`, Hyprland `0.56.2`.
- AMD Radeon 890M, RADV/Mesa `26.2.2`, Vulkan device API `1.4.354`.
- Internal 2880×1920 display at 120 Hz, scale 2.
- No pre-existing Affinity prefix or Wine/winetricks installation.

## Verified

- All 18 originally available checks passed. With ShellCheck and the new regressions, all 22 checks pass. `test/affinity` itself also passes ShellCheck 0.11.0.
- The pinned Wine 11.12 archive downloaded and matched SHA-256 `44a99f2a90356790936f08620ccca573581c0bb006b9bed6899dd4ed465986aa`.
- The Affinity download returned HTTP 200 and a complete 662,137,928-byte Windows installer.
- Installed Arch packages: Wine `11.17-1`, winetricks `20260125-2`, cabextract `1.11-3`, and the Wine dependency `ntsync-autoload`. The application prefix uses the vendored Wine `11.12`, not system Wine.
- The real prefix was created successfully after correcting the data path.
- All nine winetricks steps completed: `dotnet48 corefonts vcrun2022 msxml3 msxml6 tahoma dxvk renderer=vulkan win11`. DXVK installed version `3.1`.
- Registry initialization completed and the stored DPI is 192. The vendor wizard renders through DXVK on the AMD Radeon 890M.
- The live display helper returns 192 DPI, and the AMD renderer helper sets the expected DXVK configuration.
- The installed Omarchy menu parser preserves both Affinity actions and their `when` conditions.
- The three commands work through symlinks in `~/.local/bin`.
- The Affinity Lua rules load in the live compositor; `hyprctl reload` succeeds and `hyprctl configerrors` is empty.
- The user completed the vendor wizard, `Affinity.exe` appeared at the expected path, and the installer exited successfully. The cached Affinity installer was removed.
- The installed desktop entry validates, all four file types resolve to `affinity.desktop`, and menu parsing preserves the existing HEY entry alongside the Affinity entries.
- A real installer rerun completed in 0.441 seconds with the final changes, without running Wine setup, winetricks, or the vendor wizard again.
- `omarchy-launch-affinity --verbose` opens Affinity 3. The main `affinity.exe` window tiles; its untitled start dialog floats. Both use XWayland. The app's own log detects the Radeon 890M through DXGI.
- The first application session later closed with process exit code 0 and an `Exit` entry in Affinity's log. Its log also records successful progress through Direct3D device creation, but drawing/save/export results still need user confirmation.

## Fixes found through local testing

1. **User data targeted a root-owned directory.** `~/.local/share/omarchy` is a symlink to `/usr/share/omarchy` on this machine. Installation failed with `Permission denied` before unpacking Wine. Affinity now uses `${XDG_DATA_HOME:-$HOME/.local/share}/omarchy-affinity`; the menu conditions and documentation use the same location. A test recreates the read-only Omarchy symlink.
2. **The menu parser ignores `disabled`.** The install entry now uses the supported `when` condition and disappears when Affinity is installed. Both menu conditions honor the data/root overrides. Tests evaluate visibility before installation, after installation, and after removal.
3. **The test harness inherited real paths.** The mocked removal test now clears caller overrides that could otherwise target an actual Affinity installation or cache.
4. **The installer window class differed from the draft.** The live wizard is `setupui.exe`, title `Affinity`, on XWayland. It floated automatically but inherited desktop translucency. A title-scoped rule keeps this installer opaque, floating, and centred.
5. **Winetricks bypassed the environment-only menu-builder restriction.** Its .NET installation replaces `WINEDLLOVERRIDES` with `fusion=b`, and ten `wine-extension-*.desktop` files were created for this prefix. The installer now disables `winemenubuilder.exe` in the prefix registry before running winetricks. With the environment override cleared, attempting to run that executable exits 53 (disabled). The ten generated files referencing this prefix were moved to the local testing backup directory and the desktop database refreshed. A second full .NET installation has not been run to verify the entire prevention path.

## Vendor warning and remaining application checks

The vendor wizard opened with “Setup is not recommended” / “A native installer exists for this CPU type” and **Ignore** / **Close** buttons. This occurred with the vendor's x64 download on x86_64 hardware using the WoW64 Wine runner. The cause of that warning is not yet established. Continuing allowed the user to complete installation, and the application launches.

The application log reports missing WebView2 and unimplemented Windows color-profile APIs (`WcsGetUsePerUserProfiles`, `WcsEnumColorProfilesSize`, and related profile failures). These did not prevent launch; sign-in/help and color-managed output remain unverified. The log also reports Wintab initialization failure; tablet support has not been tested.

The user was asked to create a document, draw a stroke or shape, save, export a PNG, and assess interface sizing. Those results are pending. Cold-launch timing was not measured precisely enough to claim the checklist's 15-second target.

## Local artifacts

- Main install log: `~/.local/state/omarchy-native-testing/install.log`.
- Real rerun and verbose launch logs: `~/.local/state/omarchy-native-testing/{rerun,launch}.log`.
- Per-step Wine logs and markers: `~/.local/share/omarchy-affinity/state/`.
- Backups of the original Hyprland, menu, and MIME configuration: `~/.local/state/omarchy-native-testing/*.before`.
- ShellCheck was downloaded into `~/.local/state/omarchy-native-testing/tools/`; it was not installed system-wide.
- Disk usage after installation: about 4.4 GB for Affinity and its prefix/runner, 107 MB for the Wine archive, and 1.1 GB in the shared winetricks cache.

Document editing/export, clipboard, perceived HiDPI quality, and a real uninstall are not yet verified. Removal remains covered by the mocked suite; the working local installation is left available for interactive testing.

## Follow-up: menus and tool hover

The user reported menus/tools were nearly impossible to select. Live pointer replay reproduced the fault: the rule that centred every floating Affinity window also caught menus and tool flyouts. Wine reports ordinary menu windows with an empty title and the X11 `DIALOG` type; a dialog-type match alone cannot distinguish them from real dialogs.

Removed the blanket floating-window centring rule, keeping the existing title-specific dialog rules. No global display scaling, mouse settings, Wine DPI, renderer, or window-focus policy was changed.

- Before: File label at `[789,53]`; menu moved to `[567,164]`. Pointer replay failed either because the menu was detached or because it disappeared.
- After: File menu at `[771,64]`, immediately below its label; three consecutive runs passed.
- Hovering File > Studios opens the child menu at `[1071,89]`, beside its parent. Moving into the submenu keeps it open.
- Holding the Node tool button opens the Node/Point Transform flyout at `[765,231]`, beside the tool. Hovering Point Transform highlights the correct row and clicking selects it.
- `test/affinity-interactions` retains the live regression. The 22 static/mocked checks continue to pass, and Hyprland reports no configuration errors.
- Logs, geometry snapshots, and screenshots from diagnosis are under `~/.local/state/omarchy-native-testing/hover/`.

A separate file-opening failure was discovered during this testing: passing a document to the launcher while Affinity was already running terminated the existing process with exit 82. The log contains `System.TypeLoadException: Could not find Windows Runtime type 'Windows.ApplicationModel.DataTransfer.SharedStorageAccessManager'` in `Serif.Affinity.Application.ProcessCommandLineArguments`. The static launcher test did not exercise this Windows Runtime path. This remains unresolved; desktop-file validation and MIME registration alone do not establish that opening files from the file manager works.

Theo's [2026-08-19 reply to DHH](https://x.com/theo/status/2090170229758558534) specifically names Affinity Photo. It does not identify a Linux Wine/Proton runner. This project installs the unified Affinity 3 app, including its Pixel image-editing workspace.
