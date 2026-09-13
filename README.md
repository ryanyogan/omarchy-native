# omarchy-native

Run the Windows builds of Mac-refugee creative apps on [Omarchy](https://omarchy.org) and make them feel native in Hyprland. Phase 1: the Affinity suite.

```
omarchy-install-affinity     # patched Wine + DXVK prefix, launcher, .afphoto/.afdesign/.afpub/.psd, Hyprland rules, menu rows
omarchy-launch-affinity      # what the launcher entry runs; accepts files
omarchy-remove-affinity      # everything gone again
```

Read [`docs/affinity.md`](docs/affinity.md) first: what gets installed, the runner decision, what is Wine-fragile, how to report bugs, and the licence situation. [`NOTES.md`](NOTES.md) is the inventory of what upstream AffinityOnLinux does that the installer was drafted from.

## Using this repo

The tree mirrors Omarchy's (`bin/`, `default/applications`, `default/hypr/apps`, `default/omarchy`) so files can move into `basecamp/omarchy` unchanged. Until then, put `bin/` on your PATH or symlink the three commands into `~/.local/bin`; the commands find the rest of the repo relative to themselves (`OMARCHY_NATIVE_PATH` overrides that).

```
git clone https://github.com/ryanyogan/omarchy-native ~/.local/share/omarchy-native
ln -s ~/.local/share/omarchy-native/bin/omarchy-*-affinity ~/.local/bin/
omarchy-install-affinity
```

`test/affinity` runs the static checks (no Wine or Hyprland needed).
