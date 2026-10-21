# Future experiments

## Rust device adapters

Use Rust + MQTT discovery to move device communication out of HA while retaining HA Core. Start read-only with a local air sensor, then one WiZ bulb. Verify parity before replacing all native entries for a protocol.

Awair documents a local JSON API. WiZ Rust clients exist but require maturity and hardware checks. Tuya requires verified local protocol, keys and datapoint mapping. Rust Govee bridges already exist; compare reuse before writing another. Keep Apple TV, LG webOS, ThinQ and Alexa native initially because pairing and cloud behavior increase the scope.

Preserve availability, external-app updates, stable entity references, recorder metadata and HomeKit behavior. Retained commands can replay unexpectedly; use appropriate discovery/state retention and non-retained control commands. Start with one command owner and a rollback path.

Replacing HA's frontend backend API is a different project. MQTT offload does not eliminate the Python core. A broker and adapter can initially increase total RAM.

References: [MQTT discovery](https://www.home-assistant.io/integrations/mqtt/), [rumqttc](https://github.com/bytebeamio/rumqtt), [Awair API](https://support.getawair.com/hc/en-us/articles/360049221014-Awair-Element-Local-API-Feature), [wizlight-rs](https://github.com/LucasAmion/wizlight-rs), [govee2mqtt](https://github.com/wez/govee2mqtt).

## Agent model trials

Give models the same sanitized snapshot, prompt, tools and comparable reasoning settings. Keep independent responses blind. Measure request-to-final elapsed time, including tools and queueing, separately from any token throughput claim.

Verify findings with actual code or primary documentation. Reward correct restraint when nothing needs changing. Report unsupported assumptions and false positives. A single trial is not a general ranking.

In one 2026-10-15 housekeeping review, Muse Spark 1.3 Free finished in 47.56 seconds and DeepSeek V4.1 Flash Free in 114.13 seconds. Both correctly rejected unnecessary disk cleanup; both missed a cache-schema recovery issue reproduced by the supervising agent. Muse was faster and more restrained in this trial, with factual caveats in both answers.

Provider catalogs can lag the CLI. Refresh provider status before declaring a model unavailable. Free OpenCode model IDs and OpenCode Go model IDs have different subscription requirements.

## Rust TV Home watcher trial

On 2026-10-20, a Rust client replaced the standalone Pi Go foreground watcher. It
reuses the existing service, private configuration and TV pairing, and keeps the
same Home-to-launcher and second-Home escape behavior. This does not move the TV
launcher web app or native HA LG integration into Rust.

The release binary was built on the Pi and passed Clippy with warnings treated as
errors. A local TLS fake TV exercised the compiled Go and Rust clients against the
same nine-case protocol suite, including observe-only mode, pairing/permission
rejection, escape-window expiry, heartbeat timeout and reconnection. After the TV
was turned on, Rust passed a 35-second observe-only session across heartbeat cycles,
then injected Home/double-Home checks with the custom launcher restored afterward.
Earlier attempts received "Try Again Later" before registration from both clients;
a reachable TV network port alone did not establish readiness.

The prior unit, binary and configuration were archived privately before changing
only the existing unit's executable. The Rust service is active and enabled, keeps
the previous sandbox and pairing-failure restart policy, and has no listening
sockets. A private script restores the archived Go unit. No TV power/input/wake
commands or HA restart were used. Physical remote behavior, reboot recovery and
speed/memory improvements were not tested. No security improvement is claimed by
changing language. The [Rust watcher source, pinned dependencies and fake-TV tests](../tools/lg-home-watcher/)
are public. Live configuration, pairing material, device-specific results and
deployment/rollback tooling remain private.
