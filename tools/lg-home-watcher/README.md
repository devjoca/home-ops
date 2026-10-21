# LG Home watcher

An outbound WebSocket client that opens a configured launcher when LG Home becomes
foreground. A second LG Home event within three seconds leaves stock Home open.
`--observe` watches events without sending launcher commands.

This is a standalone Linux process, not a server or Home Assistant integration.
It has no listening port and sends no wake, power, volume or input-switch commands.
The launcher must already be installed. The client reuses an existing TV pairing;
it does not obtain a pairing key or request a new pairing.

## Build and test

Use a Rust toolchain supporting edition 2024, Cargo, a C compiler and the usual
OpenSSL build prerequisites. TLS uses vendored OpenSSL. Resolved Rust dependencies
are pinned in `Cargo.lock`.

From this directory:

```sh
cargo build --release --locked
cargo clippy --release --locked -- -D warnings
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python tests/test_protocol.py target/release/lg-home-redirect-rust
```

Tests require Python, `openssl` on PATH and an available loopback TCP port 3001.
They create a temporary self-signed TLS WebSocket peer and dummy configuration.
They exercise the compiled binary without TV access: registration/key reuse,
foreground filtering, configured launcher, the escape window and its expiry,
observe mode, permission failures, heartbeats, invalid configuration, signal
shutdown and reconnection. They also check that the dummy key stays out of logs.

The public copy was built and checked on aarch64 Linux using an existing isolated
Rust toolchain. No resource or performance improvement is claimed.

## Private configuration

Copy `examples/config.example.json` to a private location outside this repository.
The example is a schema template, not a usable registration manifest.

- `host`: the TV host or IPv4 address, without a scheme or port. The client uses
  TLS WebSocket port 3001.
- `client_key`: the existing approved TV pairing key.
- `launcher_id`: the installed launcher's app ID. Set it explicitly. If omitted or
  empty, the client retains its original `com.gathin.tvhome` default.
- `registration`: the complete registration message used by the already-paired
  client, including its approved manifest and any required signatures. Replace
  the placeholder payload with that message. The client overwrites
  `payload.client-key` with `client_key` before sending it.

Keep the configuration readable only by the service account, for example mode
`0600`. Keep the key, registration material and captured TV messages out of Git.

First run in observe mode:

```sh
./target/release/lg-home-redirect-rust --observe /path/to/private/tv.json
```

Only after confirming registration, foreground subscription and stable heartbeats,
run without `--observe` to enable launcher redirects:

```sh
./target/release/lg-home-redirect-rust /path/to/private/tv.json
```

The client accepts the TV's self-signed certificate without verifying its identity.
TLS therefore does not establish that the peer is your TV. Use it only on a trusted
network; changing the implementation language does not change that trust policy.
Peer messages and configuration are omitted from routine error logs. The configured
launcher ID is logged when a redirect occurs.

## Optional service and rollback

`examples/lg-home-watcher.service` is a user-service template. Review its paths
before using it. It expects the binary at `~/.local/bin/lg-home-redirect-rust` and
private configuration at `~/.config/lg-home-watcher/tv.json`. The example does not
install or enable itself. Boot startup depends on the host's user-manager setup.

Before replacing an existing watcher, privately archive its exact unit, binary
and configuration. Stop that watcher before starting this one so both cannot
redirect the same event. Do not replace the TV launcher or change HA pairing.

After a deliberate switch, check the running executable, registration/heartbeat
logs and actual Home/second-Home behavior. A service reporting active alone does
not prove it is connected. To roll back, stop this watcher and restore the archived
binary and service definition, leaving the existing TV pairing intact. With no
watcher connected, Home opens stock LG Home.

Exit codes: `2` invalid arguments, `77` pairing/permission rejection, `78` invalid
configuration, `0` normal SIGINT/SIGTERM shutdown. Session/transport errors retry
with backoff from five to thirty seconds. The service example prevents automatic
restart on `77` and `78`, so rejected pairing does not trigger a re-pairing loop.

Hardware compatibility, physical-remote behavior and reboot recovery must be
checked on the intended installation. The fake-TV suite does not establish them.

Licensed under the repository's [MIT license](../../LICENSE).
