# home-ops

How I maintain Home Assistant Container on a Raspberry Pi, with small scripts, repeatable checks and context that survives a new agent conversation.

This is an operations notebook and toolkit for a working home. It is not a replacement for Home Assistant, a configuration backup, or a collection of credentials.

## Start a new thread

Open this repository as the project. Give the agent one concrete task, for example:

> Read AGENTS.md and the local context. Check Pi memory growth over the last day and compare it with automation activity. Start read-only.

> Investigate why a bulb becomes unavailable. Preserve the existing entity IDs and HomeKit pairing.

> Review backup retention and verify the latest copy. Keep existing recovery keys private.

[AGENTS.md](AGENTS.md) routes the agent to the relevant runbook. Household inventory lives in git-ignored `.local/`, so new threads on this checkout can find it without publishing it.

## What is here

- [Current design](docs/current-state.md): what stays in HA and the decisions behind it.
- [Maintenance](docs/maintenance.md): inspect, change, verify and roll back.
- [Monitoring](docs/monitoring.md): CPU/memory definitions and comparison rules.
- [Privacy](docs/privacy.md): public versus local material.
- [Future experiments](docs/experiments.md): incremental Rust device adapters and fair model comparisons.
- `scripts/pi_snapshot.py`: a read-only SSH health snapshot, using Python's standard library.
- `scripts/resource_sample.py`: the collector used inside the HA container.
- [LG Home watcher](tools/lg-home-watcher/): standalone Rust foreground watcher, example configuration and fake-TV protocol tests.

## Run locally

Requires Python 3.10 or later and an existing SSH login for live checks. Tests use fixtures and need no Pi.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/pi_snapshot.py --host USER@PI_HOST --output .local/snapshots/pi.json
```

For a separate installation, copy [the local context template](examples/local-context.example.md) to `.local/CONTEXT.md` and fill in only the access details needed for maintenance. Keep recovery keys and API tokens in your password manager or private secret store.

Scripts do not install themselves, deploy configuration, prune Docker or restart HA. Review the runbooks before using them against a live home.

## Skills

No custom skill is required. Repository instructions and task-specific runbooks are enough for now. Add a skill only when a workflow has repeated enough times to justify a reusable entry point; keep the actual rules in one authoritative document.

## License

MIT. This repository describes one installation; verify assumptions against your own hardware and HA release.
