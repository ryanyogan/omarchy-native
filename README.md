# omarchy-native

Affinity on Omarchy, with a private Wine runtime, correct Hyprland popup behavior,
and a terminal installer that follows your desktop theme.

```sh
git clone https://github.com/ryanyogan/omarchy-native ~/.local/share/omarchy-native
mkdir -p ~/.local/bin
ln -s ~/.local/share/omarchy-native/bin/omarchy-*-affinity ~/.local/bin/
omarchy-setup-affinity
```

`omarchy-setup-affinity` opens an Omarchy terminal with **Install / repair** and
**Uninstall** options. Progress follows completed setup steps; detailed output
is saved to a private log. The Affinity vendor wizard still needs your clicks.
Menu-bar integration is deferred.

```sh
omarchy-setup-affinity --install     # open the installer terminal
omarchy-launch-affinity              # launch the app
omarchy-remove-affinity --dry-run    # inspect removal and dependency ownership
omarchy-setup-affinity --uninstall   # back up data and remove the installation
```

Removal verifies a backup under `~/Affinity Backups/` before deleting the app's
private directories. It removes only recorded package additions, retaining any
that other installed applications still require. Documents outside the Wine
prefix stay where you saved them. Older installations retain their entire prefix
in the recovery backup because their original runtime files were not inventoried.

See [installation and compatibility](docs/affinity.md), the
[local audit](docs/audit.md), and [earlier testing](docs/local-testing.md).
The [creator workflow](docs/creator-workflow.md) connects Theo's public thumbnail
examples to our acceptance tests and performance priorities.

Run `test/affinity` for static checks and isolated installer/removal regressions.
`test/affinity-interactions` exercises real menus on the documented desktop
fixture; `test/affinity-profile` samples the running prefix's CPU and memory.
Use `test/affinity-profile --seconds 30 --label baseline-pan-01` to record a
named workload with monitor/runtime context and a timeline of CPU/memory samples.
