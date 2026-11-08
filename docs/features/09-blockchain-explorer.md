# 9. Blockchain Explorer (Tamper-Evident Audit Chain)

## Overview
Every audit-log row is sealed into a **hash chain**: each "block" stores a sequence number, the previous block's hash, and its own SHA-256 hash over its content plus that previous hash. Editing, deleting or reordering any earlier row breaks verification from that point onward. The **Blockchain Explorer** (`/blockchain-explorer`) lets admins browse blocks, inspect one, and verify the entire chain.

## Who can use it
Admin.

## Tech stack
| Concern | Technology |
|---|---|
| Hashing | Python `hashlib` SHA-256 over canonical JSON (sorted keys, normalised UTC timestamps) |
| Automatic sealing | SQLAlchemy `after_insert` mapper event on `AuditLog` |
| Concurrency | Serialised sealing (advisory lock on Postgres; single writer on SQLite) |
| Frontend module | `frontend/src/modules/explorer/` (`ExplorerPage`, `BlockTable`, `BlockDetail`, `IntegrityPanel`, own CSS) |

## How it works
```
INSERT audit_logs row
  → after_insert hook: seq = head.seq + 1
                       prev_hash = head.hash  (genesis = 64 × "0")
                       hash = SHA-256(canonical(row content) + seq + prev_hash)
  → chain_seq, chain_prev_hash, chain_hash written on the same row

seal_pending()  — at startup and before explorer requests: chains rows that
                  predate the feature or were inserted with raw SQL

verify_chain()  — walks blocks in order, recomputes each hash and checks the
                  links; flags hash mismatches, broken links and sequence gaps
                  with expected vs. actual values
```
Because sealing hooks into the ORM, it covers every code path that writes an audit row (chat, auth, admin actions, Ghost Mode) without changing those code paths.

## Key files
`backend/app/services/ledger.py`, `backend/app/routes/explorer.py`, `frontend/src/modules/explorer/*`.

## API
| Method | Path | Notes |
|---|---|---|
| GET | `/api/explorer/stats` | Height, head block, genesis, unsealed count, breakdown by status and risk |
| GET | `/api/explorer/blocks` | Paginated list |
| GET | `/api/explorer/blocks/<seq>` | One block + its own verification |
| GET | `/api/explorer/verify` | Full-chain verification (can be slow on large chains) |

## Limitations
Tamper-*evident*, not tamper-*proof*: someone with direct database write access could recompute every hash. Anchoring the head hash externally (signed exports or periodic notarisation) closes that gap.
