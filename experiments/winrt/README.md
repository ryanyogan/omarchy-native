# WinRT namespace experiment (not installed)

`namespace.c` supplies a metadata path for Windows namespaces while forwarding
all other exports to the original `wintypes` DLL. The forwarding table matches
Wine 11.12. This is diagnostic code, not a complete namespace resolver; package
graph directories and other namespace sources are intentionally unimplemented.

Build with an untrimmed Wine 11.12 SDK and clang/lld:

```sh
/path/to/wine/bin/winegcc -b x86_64-windows -shared -o /tmp/wintypes.dll \
  experiments/winrt/namespace.c experiments/winrt/wintypes.spec -lole32 -lcombase
```

Local tracing established three separate problems with the normal command-line
file-opening path:

1. Wine 11.12's `RoResolveNamespace` is a stub.
2. Current windows-rs metadata lacks projected static class methods used by .NET.
   Version 0.58.0 includes them. The Microsoft MIT-licensed source is
   https://github.com/microsoft/windows-rs/tree/0.58.0.
3. Winetricks installs .NET 4.8 under a Windows 7 compatibility setting, leaving
   out `System.Runtime.WindowsRuntime.dll`. NuGet substitutes are not compatible
   with framework assembly unification. The proper version 4.0.0.0 assembly is
   present in Microsoft's already-downloaded .NET 4.8 installer, inside its
   Windows 8 x64 update cabinet.

The combination advances startup to Canva sign-in. It has **not** passed a full
sign-in/document-opening/Studio licensing regression and is therefore not part
of the production installer. Do not substitute upstream shims that replace the
other activation exports with stubs: those exports also serve licensing and
other application features.
