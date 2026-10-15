# Local context

Keep this file at `.local/CONTEXT.md`. It must remain untracked.

## Access

- SSH destination: USER@PI_HOST
- HA URL: private local URL
- Container: homeassistant
- Host configuration directory: your actual directory
- Container configuration directory: /config
- Credentials: private-store references only

## Inventory

Store task-relevant entity IDs, integration entry IDs and device ownership in `.local/inventory.json`. Verify them against current HA state before changing anything.

## Recovery

- Private archive directory:
- Backup destination and retention:
- Off-host copy location:
- Recovery-key reference:

## Current work

Add dated changes and verification outcomes to `.local/changes.md`. List unresolved questions here so a new thread can pick them up.
