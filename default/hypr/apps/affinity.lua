-- Affinity (Canva's unified v3 app) runs under Wine on XWayland, so every one
-- of its windows carries the class affinity.exe; the installer wizard runs as
-- "affinity x64.exe". Wine flags its splash, progress, and modal dialog windows
-- as transient, which Hyprland floats on its own: the document window is the
-- only one that opens tiled.

-- The current vendor bootstrap opens setupui.exe, title "Affinity" (observed
-- on Wine 11.12). Match the title too so unrelated installers are unaffected.
o.window({ class = "^setupui\\.exe$", title = "^Affinity$" }, {
  tag = "-default-opacity",
  opacity = "1 1",
  float = true,
  center = true,
  focus_on_activate = false,
})

-- Colour work: keep it fully opaque, same as DaVinci Resolve.
o.window("^affinity( x64)?\\.exe$", { tag = "-default-opacity", opacity = "1 1" })

-- Wine also exposes menus and tool flyouts as floating windows. Preserve their
-- app-requested positions: centring all floating windows detaches popups from
-- their controls and makes pointer navigation unreliable.
o.window({ class = "^affinity\\.exe$", title = "^$", float = true }, {
  no_initial_focus = true,
  no_follow_mouse = true,
  no_anim = true,
  no_blur = true,
  no_shadow = true,
  border_size = 0,
  rounding = 0,
})

-- Belt and braces for dialogs Wine forgets to mark transient.
o.window({
  class = "^affinity\\.exe$",
  title = "^(Open|Save.*|Export.*|Import.*|Place.*|Print.*|New Document|Document Setup|Preferences|Settings|About Affinity|Colou?r.*|Select.*)$",
}, { float = true, center = true })

-- A save dialog or progress popup appearing while you work elsewhere should
-- not yank focus across workspaces.
o.window("^affinity\\.exe$", { focus_on_activate = false })
