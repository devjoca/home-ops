# Current design

Last reviewed: 2026-10-15. This is a design record, not proof of current health. Confirm live versions and measurements when starting work.

## Host and HA

Raspberry Pi 4 with 4 GB RAM, Home Assistant Container and local-network device integrations. Docker's memory accounting returned zero on this installation, so monitoring reads Linux process data instead. The installed HA startup script selected Python's mimalloc allocator. Neither observation should be assumed to apply to another release or host.

HA uses an explicit list of essentials instead of `default_config`. Duplicate Google Cast and unused go2rtc are disabled. Native LG webOS and Apple TV remain. Some voice components load as dependencies even when omitted from the explicit list.

## Behavior to preserve

- Work and Relax are manual, mutually exclusive downstairs presets. Neither changes bedroom lights.
- Bedroom night is a separate manual red-light preset.
- Good night turns off downstairs lights, the combined diffuser and TV backlight, sleeps Apple TV and turns off the LG TV. Bedroom lights remain untouched.
- Govee power follows the TV without changing the camera's video colour-matching mode.
- The diffuser's mist and small LED have one combined on/off control.
- Laundry completion increments persistent monthly counters and announces in Spanish on the household Echo, temporarily setting volume and then restoring it.
- Apple TV's dashboard surface is status and TV/soundbar volume adjustment.

## HomeKit

The HA bridge uses an explicit entity allowlist. Broad domain exposure previously imported unrelated Amazon devices, diagnostic switches, duplicate controls and appliance power into Apple Home. Keep automatic exposure limited. Preserve bridged scene/script entities referenced by native Home scenes.

The Alexa Devices integration lets HA control the Echo and make announcements. Vendor devices linked directly to Alexa for spoken control use a separate path. Devices from elsewhere on the same Amazon account are not necessarily household devices.

## History and recovery

Detailed recorder history is seven days. The System view has Pi and HA CPU/memory charts, a weekly memory trend, automation activity and editable sustained-load indicators. Automatic protected HA backups run daily with 14-day/14-copy retention, plus a Mac copy job. An archive or a verified file copy is not a tested restore.

HA remains responsible for dashboard, automation, history, HomeKit and authentication. A future Rust adapter is an experiment, not a current dependency.
