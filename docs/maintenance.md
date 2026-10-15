# Maintain the live installation

## Inspect

1. Read the local access details, relevant inventory and the user's task. Recheck live state rather than treating old measurements as current.
2. Start with `scripts/pi_snapshot.py`. Use the authenticated HA UI/API for entity state, history and integration configuration. Keep credentials outside transcripts and public files; avoid extracting or publishing HA auth storage.
3. Identify a concrete problem. Low load, available memory, unused swap and no reclaimable Docker space are reasons to leave things alone. Do not manufacture a cleanup target.

## Change

1. Archive the affected configuration and dashboard JSON to a private directory outside the public Git tree. Record the restoration path in `.local/changes.md`.
2. Preserve entity IDs and the constraints in `current-state.md`. Prefer HA configuration flows or supported APIs for stored integration options. Avoid editing `.storage` while HA is running.
3. For YAML, run inside the container:

   ```sh
   python3 -m homeassistant --script check_config --config /config
   ```

   Inspect the full validation result. This command has returned success exit status alongside configuration errors in prior work.
4. Reload only the affected domain when supported. A new integration domain may require a restart. A template reload may leave trigger-based forecast sensors waiting for their next trigger; check and refresh them deliberately.

## Verify

- Read back the saved configuration and relevant live states. Confirm all changed entities are available and their units and targets are correct.
- For monitoring, confirm numeric samples reach recorder, not just that the script prints JSON.
- For HomeKit changes, inspect Apple Home after bridge reload and verify the expected accessories remain. An HA allowlist save alone does not prove the app updated.
- For scenes and scripts, inspect targets before testing. A physical test can change lighting, sound or appliance state; coordinate it within the user's requested scope.
- For a backup, verify creation, retention, protected recovery material and the off-host copy. Claim restoration only after an actual restore test.
- If verification fails, restore the archived change and confirm recovery. Document the unresolved cause.

## Close the thread

Update the relevant design decision, add a short dated entry to `.local/changes.md`, and state the outcome and verification. New threads should not need to recover this conversation.
