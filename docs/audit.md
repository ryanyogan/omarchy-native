# Local application audit — 2026-09-13

The installer and lifecycle are substantially improved. Affinity is usable on
this desktop, but it has not earned a claim of full native-app reliability.
Document handoff, account integration, color management, and extended creative
workflows remain release blockers or unverified areas.

## Environment and measured results

Omarchy 4.0.3, Hyprland 0.56.2, AMD Radeon 890M/RADV, a 2880×1920 panel at 2×
scale and 120 Hz, Wine 11.12, DXVK 3.1, Affinity 3. The main window was tiled and
a previously recovered test document was open during the idle sample.

| Measurement | Result | Interpretation |
|---|---:|---|
| Bundled runner allocated size | 786 → 609 MiB | Development headers/import libraries removed; runtime DLLs retained. |
| Removed development file contents | 172.7 MiB | Measured by summing removed files, rather than allocated disk blocks. |
| Redundant system Wine + winetricks | 600.48 MiB removed | Runtime libraries remain installed; private winetricks adds about 0.8 MiB. |
| Combined packaging saving | Approximately 770 MiB | Excludes cleanup of temporary audit artifacts. |
| Initial main-window mapping | 13.101 s | One launch before packaging changes. |
| Main-window mapping after changes | 9.045 s | One launch after removing system Wine; filesystem caches were warm. |
| Idle CPU, ten-second sample | 1.8% of one core | 1.1% Affinity, 0.7% wineserver; not a brush/large-document benchmark. |
| Proportional memory, entire prefix | 1,864.8 MiB | About 1.82 GiB; Affinity itself accounts for 1,730.7 MiB. |

The startup samples do **not** establish a causal speedup. Development headers
and a duplicate Wine installation occupy disk but are not loaded into Affinity.
Further meaningful memory/latency improvements need profiling of the app's
.NET/WPF rendering, document caches, and actual creative workloads. The Wine
support processes account for only about 134 MiB in this sample.

## Completed changes and verification

| Area | Change | Evidence |
|---|---|---|
| Menus and tool flyouts | Preserve app-requested popup positions; center only named dialogs. | Live File-menu placement repeated three times; nested Studios submenu stayed attached and selectable. Earlier held-tool flyout test also passed. |
| Installer presentation | Omarchy terminal, current theme, one progress bar, concise errors, private logs. | Launched the real installer in a floating `org.omarchy.terminal` window and inspected its display. |
| Installation recovery | Complete-download markers, pinned Wine/winetricks checksums, resumable verbs, operation lock. | Isolated download failure/resume and install/repair regression tests. Real repair succeeded. |
| Runtime size | Remove SDK headers/import archives, use private winetricks and direct runtime dependencies. | ELF dependency inspection; package transaction removed only the duplicate executables; actual app launched afterwards. |
| Uninstall | Verified backup, package ownership journal, dependency checks, original integration recovery. | Real temporary-file tests exercise preserved documents, changed runtime, external links, failed backup, shared dependencies, and MIME restoration. |
| Running-app protection | Exclusive setup/removal lock; shared launch lock; process check. | Real removal attempt while Affinity was open exited 1 before changing its files. |
| Native formats | Register unified `.af` alongside legacy formats. | MIME/XML and desktop-file validation; native file picker identified a saved `.af` as an Affinity document. |
| File handoff failure | Refuse unsafe handoff, notify the user, restore prior default handlers. | Regression verifies that guarded file arguments do not invoke Wine. Root cause reproduced separately. |
| Native file picker | Retain Wine's GTK portal support. | File > Open displayed a centered GTK picker. An SVG fixture opened and rendered its rectangle/circle as expected. |
| Hyprland config | User fragment only; no broad popup centering or global input changes. | Reload and `hyprctl configerrors` returned no errors. |

The automated suite combines static shell/desktop/MIME/Lua checks with 13
filesystem/ownership regressions and 5 installer/launcher regressions. It stubs
external Wine/download/package commands but performs real filesystem operations.
It is not a substitute for a full installation of every Windows component.
The working installation was not destroyed for an end-to-end uninstall; its
removal plan was inspected and the live running-app refusal was verified.

## Priority findings

### P0 — Document handoff can terminate the running app

The direct command-line path enters
`Serif.Affinity.Application.ProcessCommandLineArguments` and fails while loading
`Windows.ApplicationModel.DataTransfer.SharedStorageAccessManager`.

Tracing and reflection identified a chain of separate dependencies:

- Wine 11.12's namespace resolver is still a stub. Generated `.winmd` files alone
  do not supply this functionality.
- Current Microsoft windows-rs metadata omits static class methods expected by
  .NET. The 0.58.0 metadata includes those methods.
- Winetricks uses a Windows 7 setting for .NET 4.8 setup. This omits the framework's
  Windows Runtime assembly. NuGet replacements are not equivalent because of
  framework assembly unification. The correct assembly exists in the Windows 8
  update cabinet inside the official .NET 4.8 installer already downloaded.

A small resolver forwarding shim plus the compatible metadata/framework assembly
advanced startup to Canva sign-in. That account flow and subsequent file opening
were not completed, so the experiment was rolled back. Source and reproduction
notes are in [`experiments/winrt`](../experiments/winrt/README.md). The production
launcher guards the crashing handoff; File > Open is the verified alternative.

### P1 — Account, color, persistence, and device integration

Canva sign-in and embedded WebView2 Help are unverified. Color-profile operations
report unimplemented Wine APIs. Tablet/Wintab support is unverified. Upstream's
[WineFix documentation](https://github.com/noahc3/AffinityPluginLoader/tree/main/WineFix)
lists additional preference persistence, font enumeration, path preview, and
Wayland color-picker fixes; introducing it requires its own regression pass.

Next acceptance work should cover save/reopen and export fidelity for `.af`,
legacy Affinity formats and PSD; undo/redo; large brushes and layers; clipboard
exchange; detached panels; pen pressure; ICC-managed display/export; and account
features. A simple SVG render does not establish those workflows.

### P2 — Window backend and workload performance

The hover fault was caused by our window rules. It does not justify switching
the whole application to another backend. Keep XWayland as the tested default.
The `--desktop` option is an experimental containment fallback. Direct Wine
Wayland and a Wine desktop still need complete input, DPI, popup, and document
regressions; neither produces a native Linux Affinity executable.

Keep runtime DLL pruning, forced allocator limits, arbitrary CPU-affinity settings,
and new synchronization flags out of the default until a workload establishes a
benefit. A small file/import trace cannot prove that a DLL is unnecessary for
printing, export, a different Studio, or a later app update.

## Evidence and sources

Local logs/screenshots are under `~/.local/state/omarchy-native-testing/`, including
`optimized-startup.json`, `optimized-idle.json`, `remove-while-running.log`,
`installer-ui-single.png`, and `document-open-success.png`. The eight crash dumps
created by this audit and the temporary .NET extraction directory were removed;
the diagnostic text logs and original-file backups remain.

Primary source references:

- [Wine 11.12 namespace resolver](https://github.com/wine-mirror/wine/blob/wine-11.12/dlls/wintypes/main.c)
- [Microsoft windows-rs 0.58.0](https://github.com/microsoft/windows-rs/tree/0.58.0)
- [Pinned winetricks .NET setup](https://github.com/Winetricks/winetricks/blob/20260125/src/winetricks)
- [Affinity Wine build patches](https://github.com/ryzendew/Affinity-Wine-Builder/tree/main/patches/wine-11.12)
- [Omarchy utilities](https://github.com/basecamp/omarchy/tree/master/bin), also read from this machine's packaged installation
