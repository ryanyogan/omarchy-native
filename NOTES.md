# NOTES: what AffinityOnLinux actually does

Extracted from a read of `ryzendew/AffinityOnLinux` (`AffinityScripts/AffinityLinuxInstaller.py`, 19.5k lines; `Affinityv3.sh`; `AffinityWine10.17.sh`; `AffinityUbuntuLauncher.sh`; `docs/*.md`) on 2026-09-13. This is the raw inventory that `bin/omarchy-install-affinity` was drafted against. The decisions taken from it are in `docs/affinity.md`.

## Runners upstream offers

| Choice | Source | Notes |
|---|---|---|
| Wine 11.12 (default) | `https://github.com/ryzendew/Affinity-Wine-Builder/releases/download/11.12/ElementalWarrior-wine-11.12.tar.xz` | ElementalWarrior patches on Wine 11.12, "AMD GPU and OpenCL patches". 111 MB. sha256 `44a99f2a90356790936f08620ccca573581c0bb006b9bed6899dd4ed465986aa` (computed 2026-09-13). |
| Wine 11.12 v4 | same release, `ElementalWarrior-wine-11.12-v4.tar.xz` | AVX-512 / Zen 4-5 build. Not used. |
| Wine 10.10 | `.../Affinity-Wine-Builder/releases/download/10.10/ElementalWarrior-wine-10.10.tar.xz` | Previous stable. Still needs WinMetadata + wintypes shim. |
| Wine 9.14 (legacy) | `https://github.com/seapear/AffinityOnLinux/releases/download/Legacy/ElementalWarriorWine-x86_64.tar.gz` | Legacy fallback. |
| Stock Wine >= 10.17 (`AffinityWine10.17.sh`) | distro wine | Uses `wintypes_shim.dll.so` from `ElementalWarrior/wine-wintypes.dll-for-affinity` plus the merged `Windows.winmd` from `microsoft/windows-rs`. Upstream `Known-issues.md` documents that this path breaks Publisher's `Windows.Services.Store` licence check (`StoreLicense.get_IsActive` missing), so it is not a full-suite path. |
| wine-tkg (Kron4ek) | `https://github.com/Kron4ek/Wine-Builds/releases/download/<ver>/wine-<ver>-staging-tkg-amd64-wow64.tar.xz` | Only used by the GUI to run winetricks on distros whose system Wine is broken; never runs Affinity. |

Wine 11.12 tarball contents (verified by extraction):

- Layout: `ElementalWarrior-wine-11.12/{bin,lib,include,share}`; `bin/{wine,wineserver,winecfg,wineboot,regedit,winepath,msiexec,...}`. No `wine64`, no `lib/wine/i386-unix/`: it is a WoW64 build, so no lib32 packages are needed.
- Ships its own WinRT metadata: `share/wine/winmd/windows.{applicationmodel,globalization,graphics,media,networking,perception,storage,system,ui,ui.xaml}.winmd` and a patched `wintypes.dll`. Upstream's installer skips WinMetadata and the wintypes shim for 11.12+ ("not needed").
- Includes `winex11.drv` and `winewayland.drv`; `d3d12.dll`/`d3d12core.dll` builtins; `winevulkan.dll`.
- Dynamic deps (`readelf -d` over `bin/*` and `lib/wine/x86_64-unix/*.so`): glibc >= 2.38, libm, libresolv, libgcc_s, libxkbcommon + libxkbregistry, wayland-client + wayland-egl, libusb-1.0, libudev, libsane, libpulse, gstreamer + gst-plugins-base-libs, glib2/gobject, libX11, libXext, libOpenCL. Everything else (freetype, fontconfig, gnutls, GL, vulkan loader, Xrandr/Xi/Xcursor/Xcomposite/...) is `dlopen`ed at runtime; the Arch `wine` package's dependency tree is a superset, which is why the installer pulls `wine` in as the runtime-library carrier.

## WinMetadata

- Old flow (Wine < 11.12): `https://archive.org/download/win-metadata/WinMetadata.zip` (Affinityv3.sh) or `https://github.com/ryzendew/AffinityOnLinux/releases/download/10.4-Wine-Affinity/WinMetadata.tar.xz` (Python), extracted to `drive_c/windows/system32/WinMetadata`. That tarball is 2.3 MB, 22 `Windows.*.winmd` files lifted from a Windows install. sha256 `52d9d646d37425483367af90038a8bf88eb763576b53ef9ebc126483873eabfb` (computed 2026-09-13).
- These are Microsoft-copyrighted files redistributed without a licence. With Wine 11.12 shipping generated winmd files they are not needed, so the Omarchy installer does not download them. The checksum is recorded above in case a future Wine drop regresses.

## Prefix setup (Python `_install_winetricks_deps` + `install_dxvk_dlls`)

Winetricks call shape: `winetricks --unattended --verbose --force --no-isolate --optout <verb>`, retried once. Env: `WINEPREFIX`, `WINETRICKS_GUI=0`, `WINEDLLOVERRIDES=mscoree=;mshtml=` (blocks Mono/Gecko prompts; only for the winetricks env), `WINESERVER_TIMEOUT=60`, `WINETRICKS_DOWNLOADER=aria2c|curl|wget`.

Verbs, in order:

1. `dotnet35sp1` (Affinityv3.sh: `dotnet35`; the 10.17 script omits it entirely)
2. `dotnet48`
3. `corefonts`
4. `vcrun2022`
5. `msxml3`
6. `msxml6`
7. `crypt32` (Python only)
8. `tahoma`
9. `renderer=vulkan`
10. `dxvk` (Python, separate step; falls back to extracting `doitsujin/dxvk` x64 DLLs into system32 and writing `d3d8,d3d9,d3d10,d3d10_1,d3d10core,d3d11,dxgi = native,builtin` overrides)

Then `winecfg -v win11`, then `regedit wine-dark-theme.reg` (vendored here as `default/affinity/wine-dark-theme.reg`).

Registry writes:

- `HKCU\Software\Wine\Direct3D\renderer = vulkan` (via `renderer=vulkan`)
- `HKCU\Software\Wine\DllOverrides\{d3d8,d3d9,d3d10,d3d10_1,d3d10core,d3d11,dxgi} = native,builtin` (DXVK)
- `HKCU\Software\Wine\DllOverrides\{d3d12,d3d12core} = native` (only when OpenCL/vkd3d-proton is enabled)
- `HKCU\Software\Wine\Drivers\Graphics = x11` (`force_wine_x11_driver_if_needed`: applied whenever `XDG_SESSION_TYPE=wayland`, so Wine never picks its Wayland driver)
- `HKCU\Control Panel\Desktop\LogPixels = <dpi>` (`set_dpi_scaling`, user-chosen; default 96)
- `HKLM\Software\Microsoft\Windows NT\CurrentVersion\CurrentVersion = 10.0` (`win11`)
- Dark theme: `HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\{AppsUseLightTheme,SystemUsesLightTheme}=0`, `HKCU\Control Panel\Colors\*`
- WebView2 (v3 only, optional): `HKLM\System\CurrentControlSet\Services\edgeupdate*` disabled, `HKCU\Software\Wine\AppDefaults\msedgewebview2.exe`. Upstream `Known-issues.md`: WebView2 is broken under Wine regardless; only affects in-app Help and Canva sign-in. Not installed here.

## OpenCL / vkd3d-proton

- Latest `HansKristian-Work/vkd3d-proton` `.tar.zst`; `x64/{d3d12,d3d12core,dxgi}.dll` copied to `<wine>/lib/wine/vkd3d-proton/x86_64-windows/` and then next to `Affinity.exe`; overrides `d3d12=n,b;d3d12core=n,b`.
- Only useful for Affinity's "Hardware acceleration (OpenCL)" preference; upstream itself flags AMD/Intel OpenCL as unsupported and recommends DXVK. Skipped here per the brief (Vulkan via DXVK, OpenCL off).

## Launch environment (`AffinityUbuntuLauncher.sh`, Python launch path)

```
WINEPREFIX=<prefix> WINE=<wine> WINESERVER=<wineserver> PATH=<wine>/bin:$PATH
WINEDEBUG=-all,fixme-all
WINEDLLOVERRIDES=d3d12=n,b;d3d12core=n,b[;mscms=n,b]     # vkd3d/OpenCL + optional mscms shim
DXVK_ASYNC=0
DXVK_CONFIG="d3d9.deferSurfaceCreation = True; d3d9.shaderModel = 1"   # AMD (and NVIDIA when DXVK preferred)
DXVK_LOG_LEVEL=none
VKD3D_DEBUG=none VKD3D_SHADER_DEBUG=none VKD3D_FEATURE_LEVEL=12_1 VKD3D_SHADER_MODEL=6_5
VKD3D_DISABLE_EXTENSIONS=VK_KHR_present_id,VK_KHR_present_wait   # Wayland sessions
VKD3D_CONFIG=swapchain_legacy                                     # Wayland + NVIDIA
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia __VK_LAYER_NV_optimus=NVIDIA_only  # hybrid NVIDIA
MESA_VK_DEVICE_SELECT=<pci id> MESA_VK_DEVICE_SELECT_FORCE_DEFAULT_DEVICE=1                   # GPU pick
```

Launch is `wine "<prefix>/drive_c/Program Files/Affinity/Affinity/Affinity.exe"` (not `wine start`; upstream found `start` less reliable for v3). If `AffinityHook.exe` (noahc3/AffinityPluginLoader + WineFix) is present it is launched instead.

## Affinity application

- Download: `https://downloads.affinity.studio/Affinity%20x64.exe` (single unified v3 installer, free tier; Python `_download_affinity_installer_thread`). Run as `wine "<installer>"` with fallback `wine start /wait /unix "<installer>"`; the wizard is interactive, no silent flags are passed anywhere upstream.
- Installs to `drive_c/Program Files/Affinity/Affinity/Affinity.exe`.
- Roaming data: `drive_c/users/<user>/AppData/Roaming/Affinity/Affinity/3.0/`. Upstream quarantines it when `Log.txt` contains `JPEG XL: input does not have a valid signature` (an Ubuntu-specific corruption they hit).
- Desktop entry upstream writes: `Name=Affinity Suite`, `Categories=Graphics;`, `StartupWMClass=affinity.exe`, `Path=<prefix>`, icon `~/.local/share/icons/Affinity.svg` from `Assets/Icons/Affinity-Canva.svg`. It also deletes Wine's own `wine/Programs/Affinity.desktop` and `wine-protocol-affinity.desktop`.

## Extras upstream offers that are NOT taken here

- AffinityPluginLoader + WineFix (`noahc3/AffinityPluginLoader`, MIT for the loader, separate licence for WineFix): fixes "preferences not saving" and some stability issues; launched via `AffinityHook.exe`. Candidate follow-up.
- `mscms.dll` shim built locally (colour management). Follow-up.
- `return-affinity-colors` (ShawnTheBeachy). Cosmetic.
- WebView2 runtime install. Broken under Wine anyway.
- Per-app `AffinityPatcher` (.NET, patches settings assemblies). Out of scope.

## Distro packages upstream installs (Arch branch)

`wine winetricks wget curl p7zip tar jq xz` (+ `python-pyqt6` for the GUI). OpenCL extras: `opencl-nvidia` or `opencl-amd`.
