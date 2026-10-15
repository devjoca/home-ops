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
