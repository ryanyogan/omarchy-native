# Creator workflow and performance direction

Research checked September 13, 2026. The first product target is a dependable
thumbnail editor on Omarchy. This is a workload derived from Theo's public
examples, not a claim that he uses our build or has endorsed this project.

## What Theo actually uses

- In [his October 30, 2025 post](https://x.com/theo/status/1983967377726566443),
  Theo says his channel's thumbnails were made with Affinity Photo.
- [His February 2, 2024 example](https://x.com/theo/status/1753391134574006499)
  identifies a specific thumbnail made with Photo. The
  [follow-up](https://x.com/theo/status/1753391359267066359) reports 673 thumbnails
  over two years.
- In [his Raycast demonstration](https://www.youtube.com/watch?v=dQwJQnOxyVk),
  published January 10, 2025, he searches for Raycast and TypeScript logos through
  SVGL and pastes them into an Affinity thumbnail project. He also demonstrates
  dedicated application hotkeys and uploading an image from the clipboard.
- In [the Omarchy discussion](https://x.com/theo/status/2090170229758558534),
  he identifies Affinity Photo as a remaining creative-software obstacle to
  leaving macOS. He does not specify a Wine implementation there. In the
  [preceding post](https://x.com/theo/status/2090155293317751105), he says he uses
  CachyOS for Linux development.

Our installation is unified Affinity 3, with Pixel and Vector tools. That covers
the intended category of work, but older Photo documents, fonts, and editing
behavior need migration tests. We have no evidence of Theo's exact presets,
document dimensions, plugins, layer counts, or current Affinity version.

## A practical daily workflow

Keep a reusable local project containing the background, editable headline,
image placeholders, and recurring graphic elements. Duplicate it per video.
Use Pixel for raster editing and Vector for logo/text work. Keep downloaded
assets beside the project, with exports in a separate folder.

For now, launch Affinity normally and use **File > Open**. Use **File > Place**
for adding saved assets once its acceptance check passes. External document
handoff remains guarded because it can crash the application. Do not enable it
just to reduce clicks.

The next desktop convenience should be a small local asset picker that remembers
recent SVGs/PNGs and focuses Affinity. Before building its clipboard bridge,
establish which SVG, PNG and file-list MIME representations actually arrive
correctly through Wayland → XWayland → Wine. A PNG fallback may preserve
appearance while losing vector editability; it must be explicit. Merely copying
SVG text with `wl-copy` does not prove an editable paste works.

Use Omarchy's existing launcher and screenshot/clipboard utilities. Add a
dedicated Affinity focus shortcut only after checking the user's existing
bindings. Publishing/uploading is a separate explicit user action.

## Repeatable acceptance run

The repository provides an original synthetic 1280×720 SVG with editable text,
vector shapes and solid color patches at
[`test/fixtures/creator-thumbnail.svg`](../test/fixtures/creator-thumbnail.svg).
Its dimensions are our test choice, not a reported Theo setting. The fixture
does not represent complex photo editing or validate photographic color fidelity.

Create a new local run directory, then operate only on copies:

```sh
run=$(mktemp -d "$HOME/affinity-creator-test.XXXXXX")
cp test/fixtures/creator-thumbnail.svg "$run/source.svg"
printf '%s\n' "$run"
omarchy-launch-affinity
```

| Step | Action | Required result |
|---|---|---|
| Import | File > Open `source.svg` | Correct 1280×720 canvas, separate editable objects, no missing glyphs. |
| Compose | Edit headline, move/resize graphic, duplicate a layer, undo then redo | Correct selection, transforms and history; no stuck modifier or displaced flyout. |
| Raster | Place a local PNG, add a mask, make repeated brush strokes | Correct alpha, mask and stroke position at 100% and 200% zoom. |
| Clipboard | Paste PNG from a Linux app, then SVG; copy an image back | Correct appearance and dimensions; record whether SVG stays editable. Preserve original clipboard contents where practical. |
| Persist | Save As `thumbnail.af`, close that document, reopen via File > Open | Edits, layers, masks and fonts preserved; clean save state. |
| Export | File > Export, PNG and JPEG, 1280×720, sRGB | Both files decode in a native Linux viewer; dimensions, text, transparency/flattening and colors correct. |
| Repeat | Reopen the `.af`, change headline, export a second version | Output reflects the new text, original project still opens. |
| Soak | Edit a placed/embedded SVG for 20 minutes, switch windows, save/reopen | No crash, lost focus, disappearing preview or lost work. |

Record each row as pass, fail or untested with the input hash, output filenames,
application/runtime versions, and screenshot or reproduction steps. A created
file alone is not a fidelity pass. Compare sRGB exports in a native viewer;
compare with the same document exported on supported Windows/macOS before making
a cross-platform fidelity claim. Test one real legacy `.afphoto`/PSD separately.

### Current verification status

The earlier audit verified a simple SVG import and live menu/submenu placement.
This research pass verified launch on the 5120×2880 Studio Display at 2×/60 Hz,
the revised profiler against a real running prefix, and isolated sampler checks
for an absent app and an app exiting during a sample. The existing 13 lifecycle
and 5 installer tests pass. A three-second empty-document sample is a tooling
smoke check, not a creative-workload performance baseline.

The complete thumbnail acceptance run is still unverified. The native GTK open
dialog accepted the fixture path, but synthetic submission events did not open
it during this pass. That is an automation limitation, not sufficient evidence
of a physical-keyboard or app import defect. Save/reopen, raster/clipboard and
export checks must not be reported as passing until their outputs are inspected.

## Measure the work before tuning

Run labeled samples from a second terminal while performing one prescribed task:

```sh
test/affinity-profile --seconds 30 --label baseline-idle-01 > "$run/idle-01.json"
test/affinity-profile --seconds 30 --label baseline-pan-01 > "$run/pan-01.json"
test/affinity-profile --seconds 30 --label baseline-brush-01 > "$run/brush-01.json"
```

The profiler samples prefix processes each second, records CPU/PSS, sampled peak
PSS, Wine/kernel/package versions and monitor resolution/refresh/scale. It fails
if Affinity is absent at startup or absent at a later sample. Short-lived
processes and peaks between samples can be missed. Its CPU figure is a percent
of **one core**. It does not measure pointer latency, GPU memory, export time or
fidelity. Record the app version and document hash separately.

Use five repetitions per candidate, alternate baseline/candidate order, and keep
the document, zoom, window size, monitor, power profile and background workload
the same. Record cold startup separately from warm startup; window mapping is
not document readiness. Measure open/save/export from initiating the action to
the UI becoming usable/file completion, excluding time spent choosing a path.
Report median and range for these small samples, not a confident p95.

For rendering investigation, the [DXVK HUD](https://github.com/doitsujin/dxvk#hud)
can expose frame times, compiler activity and GPU allocations. Start a separate
diagnostic launch after normally closing Affinity:

```sh
DXVK_HUD=devinfo,frametimes,memory,compiler omarchy-launch-affinity
```

The HUD is optional instrumentation and must be verified to attach to the
relevant rendering path. Frame rate is not input-to-photon latency; screen
capture adds overhead. Use the same instrumentation on both candidates. At
120 Hz the display interval is 8.3 ms; at 60 Hz it is 16.7 ms. Those are display
intervals, not measured Affinity performance or universal pass thresholds.

Proposed promotion rule: all correctness rows pass, no new crash in the soak,
and any claimed improvement repeats beyond baseline variation. Flag a >10%
regression in median operation time or sampled memory for investigation; do not
silently trade fidelity or reliability for the faster number.

## Where our updates belong

| Priority | Work | Appropriate component | Evidence before promotion |
|---|---|---|---|
| 1 | Safe document opening and save/reopen/export | Wine WinRT and launcher integration | Small failing API reproduction, then complete document/account workflow. |
| 2 | PNG/SVG clipboard and local asset picker | Omarchy integration plus Wine clipboard handling | Linux↔Affinity round trip with alpha, dimensions and editable SVG checked. |
| 3 | Preference/font/path-preview fixes | Evaluate targeted WineFix patches | Pin a revision; test each patch in a disposable prefix against the creator run. |
| 4 | Actual brush/pan/export bottleneck | Profile Affinity/.NET, Wine or DXVK as evidence indicates | Repeated operation timings, CPU stacks/frame data and unchanged output. |
| 5 | Alternative window backend | Wine Wayland/Hyprland only for a reproduced backend defect | Same input, popup, clipboard, DPI and document tests on both backends. |

Keep our Omarchy integration small. Wine is already open source: inspect and
patch the failing API with an upstream regression test rather than reconstructing
an entire compatibility layer. Keep a pinned runner and a short documented patch
series. Affinity's application source is proprietary; improvements to its own
engine require vendor involvement or a separately evaluated plugin mechanism.

[WineFix](https://github.com/noahc3/AffinityPluginLoader/tree/main/WineFix)
currently documents preference persistence, vector preview and font enumeration
patches, but also lists an embedded-SVG editor crash. It includes a temporary
Canva sign-in suppression patch; this is not evidence that our legitimate account
flow works, and should not be bundled as a substitute for fixing that flow.
Do not automatically install the whole plugin set as a performance optimization.

Keep new runner/plugin versions in an isolated test installation with copies of
documents. Pin downloads, record patch provenance, preserve a working rollback,
run lifecycle checks and this workflow, then explicitly promote the candidate.
No upstream issue/PR or vendor message is sent without user authorization.

The previous audit found only about 134 MiB of Wine support-process PSS versus
1,731 MiB in Affinity. That makes indiscriminate Wine DLL pruning a poor first
memory target. Keep disk footprint, idle memory, editing latency and export time
as separate results. See [the measured audit](audit.md) for the existing baseline.
