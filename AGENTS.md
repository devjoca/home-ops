# Working in home-ops

This public repo documents a live Home Assistant installation. Start with read-only inspection and complete the user's scoped task.

1. For live work, read `.local/CONTEXT.md` and only the relevant entries in `.local/inventory.json`. They contain private access details and device mappings. In a worktree, use `git worktree list --porcelain` to locate the primary checkout's `.local/`; it is not copied into new worktrees. If absent there too, use `examples/local-context.example.md` to identify missing information; continue work that needs no live access.
2. Read `docs/current-state.md` for behavioral constraints. For maintenance or deployment, follow `docs/maintenance.md`. For CPU, memory or benchmark claims, read `docs/monitoring.md`. For publishing, read `docs/privacy.md`. For Rust offload or model trials, read `docs/experiments.md`.
3. Inspect the current source before editing, archive affected live configuration privately, make a narrow reversible change, and verify the resulting behavior. Record changed decisions in public docs and device-specific changes in `.local/`.
4. Before committing, inspect the complete staged diff for household details and credentials. Stage explicit paths. Never commit `.local/`, `.storage/`, live backups, tokens, raw HA configuration or this conversation's transcript.

Preserve entity IDs, HomeKit pairing, existing manual scene behavior and backup recovery material. A valid configuration check is necessary for YAML changes; inspect its output as well as its exit code. Device power changes, announcements and restarts are operational effects, not harmless verification steps.

Use the user's authorized scope for routine reversible work. Identify a concrete missing input or irreversible effect before asking for permission. Report what changed, what was verified, and any unresolved limitation.
