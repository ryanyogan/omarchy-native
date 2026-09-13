-- Affinity (Canva's unified v3 app) runs under Wine on XWayland, so every one
-- of its windows carries the class affinity.exe; the installer wizard runs as
-- "affinity x64.exe". Wine flags its splash, progress, and modal dialog windows
-- as transient, which Hyprland floats on its own: the document window is the
-- only one that opens tiled.

-- Colour work: keep it fully opaque, same as DaVinci Resolve.
o.window("^affinity( x64)?\\.exe$", { tag = "-default-opacity", opacity = "1 1" })

-- Splash and dialogs already float; centre them.
o.window({ class = "^affinity( x64)?\\.exe$", float = true }, { center = true })

-- Belt and braces for dialogs Wine forgets to mark transient.
o.window({
  class = "^affinity\\.exe$",
  title = "^(Open|Save.*|Export.*|Import.*|Place.*|Print.*|New Document|Document Setup|Preferences|Settings|About Affinity|Colou?r.*|Select.*)$",
}, { float = true, center = true })

-- A save dialog or progress popup appearing while you work elsewhere should
-- not yank focus across workspaces.
o.window("^affinity\\.exe$", { focus_on_activate = false })
