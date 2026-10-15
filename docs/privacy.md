# Public and private material

Publish reusable code, generic configuration examples, runbooks and measured conclusions with identifying details removed.

Keep these under git-ignored `.local/` or an external private store:

- SSH destinations, private addresses, device MACs, entity inventories and account identifiers.
- Household names, location, occupancy patterns, screenshots and raw sensor history.
- Live HA configuration, integration data, diagnostic exports, backups and recovery material.
- API keys, passwords, tokens and authentication files. Prefer a password manager or secret store; local context should contain references, not secret values.

## Before publishing

1. Run local tests.
2. Stage explicit public paths and inspect `git diff --cached` in full.
3. Confirm `.local/` and sample private files are ignored with `git check-ignore`.
4. Search staged content for real addresses, device IDs and credential patterns. A search is a check, not proof that every secret is absent.
5. Confirm the repository owner and visibility before pushing. Use the account intended by the user without changing global GitHub authentication.

Git ignore rules do not protect files already tracked. If a credential is ever published, rotate it and address Git history separately. Deleting a file in a later commit is not credential recovery.
