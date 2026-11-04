# Changelog

## Unreleased

### Added

- Bring up external HDMI on Raptor Lake-S on macOS Tahoe without an Intel GOP: map the stolen-memory GGTT range, seed the first display path on the VBT-wired HDMI port, and add the `-wex-boot-ddi3` / `-wex-boot-ddi4` port selection.
- Drive native Raptor Lake-S HDMI up to 600 MHz TMDS with SCDC scrambling, enabling 3840x2160@60, and run 10 bpc deep colour with the matching TMDS clock and General Control Packet where the link allows it.
- Add read-only GMBus/DDC request counters and live display register and scanout descriptions for display diagnostics.
- Add read-only Raptor Lake-S render-engine runtime and outgoing-context lifetime observations for submission and completion diagnostics.

### Fixed

- Build new Raptor Lake-S render contexts through the native plain-context path on macOS Tahoe so render commands execute and complete.
- Make qualified Alder Lake-S / Raptor Lake-S framebuffers eligible for the native graphics-policy driver, and drop the donor's placeholder internal panel from external-only firmware topologies.
- Keep fixed Raptor Lake-S HDMI combo routes in combo mode on hotplug instead of the Type-C mode that drove them as DisplayPort.
- Skip the DisplayPort-only native HDCP on fixed HDMI routes, which dropped the link repeatedly.
- Program the VBT-selected HDMI voltage-swing entry on Raptor Lake-S combo PHYs.
- Skip the native GPU-hang register dump, which could hold WindowServer for minutes during resolution changes.
- Accept a Gen12 context-status element completion whose next ELSP element is the same context, instead of panicking under heavy render load.

## 0.7.0

Use the latest [WhateverXe Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases) package with this update.

### Added

- Add USB-C DisplayPort Alt Mode output on Alder Lake-class GPUs, including multi-display startup and reconnection.
- Add experimental MIPI DSI display support with graphics acceleration, brightness control, display off/on, rotation, HiDPI and external-display coexistence. Tested on GPD MicroPC 2 and CHUWI MiniBook X N100 only; do not expect it to work on other devices. System sleep/wake remains unsupported.

### Fixed

- Fix graphics initialization and acceleration on additional supported Tiger Lake and Alder/Raptor Lake GPU variants, including single-channel configurations.
- Fix graphics initialization on compatible Sequoia and Tahoe updates without requiring an exact OS build match.
- Fix display freezes during cursor resizing and improve multi-display startup and display off/on with MIPI DSI panels.
- Fix system power-off hangs with a USB-C display connected on Alder Lake-class GPUs.

## 0.6.1

Use the latest [WhateverXe Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases) package.

### Added

- Add experimental internal display (eDP) and brightness support for Alder Lake-N / Twin Lake and Alder Lake-H/P/U / Raptor Lake-H/P/U GPUs. Not yet tested on hardware.

### Fixed

- Fix DEBUG boot freezes and restart loops caused by excessive kernel stack usage.

## 0.6.0

Use the latest [WhateverXe Graphics](https://github.com/b00t0x/WhateverXe-Graphics/releases) package.

### Added

- Add Alder Lake-H/P/U and Raptor Lake-H/P/U GPU support with automatic resource detection and VBT-selected fixed HDMI routes.
- Add experimental fixed TC DisplayPort output with matching AUX wiring; Alder Lake-H has been tested through a DP-to-HDMI adapter.
- Support startup with multiple fixed TC displays, including supported firmware-scaled boot displays.

### Fixed

- Improve display clock ownership, output shutdown and reuse across the shared external-display paths.
- Stop display teardown and reuse when required shutdown steps fail.
- [WhateverXe Graphics 0.3.0](https://github.com/b00t0x/WhateverXe-Graphics/releases) fixes shader compilation failures on Sonoma–Tahoe by expanding supported AIR inputs.

Alder Lake-H hardware checks cover Big Sur–Tahoe. Other newly accepted mobile configurations remain untested. Internal panels and Type-C-managed output on the newly supported mobile GPUs still need implementation; existing DisplayPort reconnection and Sequoia App Store video hangs remain unresolved. See the [README](https://github.com/b00t0x/WhateverXe#tested-features-and-known-issues) for coverage and limits.

## 0.5.0

The newly added GPUs require [WhateverXe Graphics 0.2.0](https://github.com/b00t0x/WhateverXe-Graphics/releases). Its rendering fixes also benefit previously supported GPUs; updating both components is recommended.

### Added

- Add Alder Lake-S graphics acceleration and HDMI/DisplayPort output, including compatible USB-C wiring and up to three displays.
- Accept Tiger Lake-H45, Alder Lake-HX and Raptor Lake-S/HX using shared support. These configurations still need hardware testing.
- Use firmware information to configure more display layouts automatically.

### Fixed

- Avoid some startup panics caused by display hardware not being ready.
- Restore Safari graphics-driver access regardless of where macOS installs Safari updates.
- [WhateverXe Graphics 0.2.0](https://github.com/b00t0x/WhateverXe-Graphics/releases) fixes observed Chrome drawing failures and rendering errors on smaller integrated GPUs.

DisplayPort/USB-C reconnection can still freeze the computer. See the [README](https://github.com/b00t0x/WhateverXe#tested-features-and-known-issues) for tested configurations and other known issues.

## 0.4.0

Add experimental Tiger Lake laptop display support and automatic Display 13 tiling selection.

- Read connector routing from structurally valid firmware VBT tables even when their checksum is stale, while retaining bounds and connector checks.
- Add Tiger Lake internal eDP output with EDID-derived color depth, firmware-derived panel setup and brightness control with SSDT-PNLF.
- Add firmware-selected Tiger Lake USB-C DisplayPort Alt Mode output, including PHY, AUX and lane assignment handling.
- Keep eDP scrambler settings synchronized with the panel during link training to restore normal output after display sleep.
- Remove the `-wex-nopanel` boot argument: it is no longer needed because internal displays are detected automatically on laptops and mini PCs.
- Select Y-tiled scanout automatically on the supported Display 13 backend, removing the OpenCore `AAPL,GfxYTile` requirement.

Laptop display and brightness checks cover Big Sur through Tahoe. HDMI and both tested USB-C ports passed reconnection checks on Tahoe; Tiger Lake and Alder Lake-N mini PCs passed Big Sur/Tahoe regression checks. Automatic Display 13 Y tiling was verified on Alder Lake-N with Big Sur and Tahoe.

This update does not require updating or reinstalling the WhateverXe Graphics package. Fixed DisplayPort reconnection remains a known issue, and system sleep is not validated; see the [README](https://github.com/b00t0x/WhateverXe#tested-features-and-known-issues) for coverage and limitations.

## 0.3.0

Xe-LP graphics compatibility for the configurations described in the [README](https://github.com/b00t0x/WhateverXe#compatibility).

- One WEX binary supports Big Sur through Tahoe on the implemented Tiger Lake and Alder Lake-N / Twin Lake backends.
- Graphics installation uses the signed [WhateverXe Graphics pkg](https://github.com/b00t0x/WhateverXe-Graphics/releases), with no Xe System-volume patch or OCLP dependency.
- Includes cross-version OS/driver ABI adaptations, OpenCL compatibility and late semaphore mapping invalidation fixes.
- Supports signed Data graphics bundles with Mod AMFIPass, without `amfi=0x80` or `ipc_control_port_options=0`.
- Preserve debug information in the bundled dSYM before stripping the kext.
- Tiger Lake and Alder Lake-N have completed the six-OS functional checks described in the README. Known issues and hardware coverage limits still apply.

## 0.2.3

Fix DisplayPort startup and hotplug issues.

- Fix a kernel panic when booting with only DisplayPort connected.
- Fix DisplayPort detection when first connected after an HDMI-only boot.

The text-rendering fix is provided separately by the Xe root patch in [OpenCore Legacy Patcher 3.0.0-rc.3+m.2](https://github.com/b00t0x/OpenCore-Legacy-Patcher/releases/tag/3.0.0-rc.3%2Bm.2).

## 0.2.2

Xe-LP graphics compatibility for the configurations described in the [README](https://github.com/b00t0x/WhateverXe#compatibility).
