# Session history and handoff — 2026-09-13

Stopped at the user's request to save and commit for tomorrow. This is a working
checkpoint, not a declaration that all Affinity UX issues are resolved.

## User decisions

- Improve menus, tooltips, pointer size, and interaction fluidity on this machine.
- **Welcome should float; the Affinity document editor should tile.** A temporary
  floating-editor experiment was removed and the live editor restored to tiling.
- Finish the installer/uninstaller and audit, with menu-bar integration deferred.
- Optimize against measured creative workflows before changing Wine/platform code.
- Commit and push the earlier baseline first: completed as `044d231`,
  `Add recoverable Affinity installer and local workflow diagnostics`.

## Earlier work preserved in the baseline

The vendor installation completed. Fixed root-owned data paths and integration,
then reproduced displaced menus caused by blanket floating-window centering.
Removed that rule; menus and flyouts must retain application-requested positions.

Added a themed terminal installer, resumable setup, pinned private Wine/winetricks,
package ownership tracking, verified uninstall recovery, and running-app protection.
Packaging changes saved approximately 770 MiB; they do not prove lower drawing
latency or memory use. See [audit](audit.md) and [local testing](local-testing.md).

Command-line document handoff can crash the app in a missing WinRT API. The
launcher guards that path; use File > Open. A resolver/metadata experiment reached
Canva sign-in but was rolled back without completing acceptance tests. Sources
remain under `experiments/winrt`; the experiment is not deployed.

Theo's cited X reply names Affinity Photo, not a specific Linux runner. Our app
is unified Affinity 3; its Pixel workspace is the relevant image-editing path.
[Creator workflow](creator-workflow.md) records sources and proposed acceptance work.

## This checkpoint's changes and observations

Testing moved to an Apple Studio Display: DP-5, 5120×2880 at 60 Hz, scale 2,
logical 2560×1440. Omarchy 4.0.3, Hyprland 0.56.2, Wine 11.12, Mesa 26.2.2;
Wine DPI 192 and XWayland `force_zero_scaling=true`. Earlier 120 Hz laptop
measurements are not directly comparable.

- Rich tooltips stole Hyprland focus while the pointer remained over their tool.
  Untitled floating Affinity windows now suppress initial/follow-mouse focus,
  animation, blur, shadow, borders, and rounding. Placement remains app-controlled.
- XFixes measured a 24×24 physical cursor at 2× scale. The launcher now supplies
  48×48, preserving the inherited theme and global cursor settings. Isolated
  tests cover 96/144/192 DPI and an explicit physical-size override.
- `test/affinity-ux` exercises Artboard, Node, and Corner tooltips with pointer
  motion and checks focus, placement, stability, compositor properties, and cursor.
- Menu regression now dismisses menus by clicking their label. Synthetic Escape
  was unreliable in this session; keyboard automation results are not conclusive.
- Welcome retained stale editor bounds after moving/resizing the editor. It
  already floats but has no finished independent size/center/focus treatment.
  Welcome shares its blank title/class with menus and tooltips; the current popup
  rule also affects it. Do not introduce another blanket blank-title center rule.
- Win32 and X11 geometry probes agreed. No pointer-coordinate root cause was
  established for the remaining Welcome/Settings oddities.
- A long probing session produced a black canvas. A clean restart and reopening
  our SVG fixture rendered correctly; cause and long-session reliability remain
  unresolved. Tablet input was restored to High Precision after an accidental
  automation change. No intentional application preference change remains.

## Final verification before stopping

| Check | Result |
|---|---|
| `test/affinity`, with ShellCheck 0.11.0 | Passed static checks, 13 lifecycle tests, 6 installer/launcher tests. |
| `test/affinity-ux`, editor tiled | Passed all three tooltip checks and 48×48 cursor check. Appearance 0.426–0.463 s; dismissal about 0.513–0.514 s between tools. |
| `test/affinity-interactions` | Earlier run passed all three openings and nested Studios navigation. Final tiled-editor rerun opened/dismissed once, then failed `File menu stays open, attempt 2`. Cause unresolved; do not call this consistently green. |
| `hyprctl configerrors` | Empty. |

The live editor was left tiled with the synthetic creator SVG used during testing.
Welcome was dismissed at the final check. No Wine restart or document closure is
needed merely to resume the investigation.

## Start here tomorrow

1. Reproduce the second-opening menu failure with timestamped client/focus/pointer
   observations. Separate test timing from application behavior before changing it.
2. Identify Welcome reliably, then give only Welcome a centered floating size
   and appropriate focus behavior. Keep the editor tiled and menu/tooltip geometry
   untouched. Reopen Welcome after editor resizing to check stale bounds.
3. Recheck tooltips, nested menus, Welcome controls, pointer size, and keyboard
   interactions with the user. Mixed-monitor scaling is not yet tested.
4. Run the creator save/reopen/export workflow, then profile real pan/zoom/brush
   activity. Account integration, ICC fidelity, pen input, persistence, detached
   panels, and large-document reliability remain open; avoid speculative DLL pruning.

```sh
cd ~/code/omarchy-native
PATH="$HOME/.local/state/omarchy-native-testing/tools/shellcheck-v0.11.0:$PATH" test/affinity
# Single 2× display at origin, English UI, Vector studio, Welcome/dialogs closed;
# these move the pointer and must run sequentially while it is left alone.
test/affinity-interactions
test/affinity-ux
hyprctl configerrors
```

Private evidence and diagnostic helpers remain under
`~/.local/state/omarchy-native-testing/`, outside Git:

- `ux-checkpoint-suite.log`, `ux-checkpoint-menus.log`,
  `ux-checkpoint-tooltips.log`: final results above.
- `ux-menus-after.log`, `ux-floating-after.log`: earlier passing runs.
- `ux-before.log`, `ux-focus-only.log`, `ux-effects.log`: incremental diagnosis.
- `affinity-before-ux.lua`: original installed window-rule backup.
- `floating-welcome.png`, `ux-reopen-fixture.png`: stale Welcome/render evidence.
- `hover-probe.py`, `creator-input.py`, `x-geometry`, `WindowProbe.exe`:
  experimental local input/cursor/geometry probes, not shipped dependencies.

The shipped Hyprland fragment is `default/hypr/apps/affinity.lua`; its installed
copy is `~/.config/hypr/affinity.lua`. Launcher links in `~/.local/bin` point into
this checkout. Screenshots, logs, Wine state, and user documents are not committed.
