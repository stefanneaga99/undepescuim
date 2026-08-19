# Offline national data contract

The browser keeps one all-or-nothing snapshot under the IndexedDB database
`undepescuim-offline`, object store `snapshots`, key
`undepescuim.offline-data.v1`. The `schemaVersion` field is currently `1`.

A snapshot contains the approved `associations`, contracted `waters`, and the
combined uncontracted river/lake pool, plus `syncedAt` and the source
`dataUpdatedAt`. A failed response never replaces the previous snapshot.
Missing, malformed, partial, or unknown-schema snapshots are deleted and the
map falls back to its empty first-use state. Browsers without IndexedDB use a
small localStorage fallback; large national snapshots use IndexedDB.

The map checks connectivity before loading. Offline launches read this local
snapshot and issue no data requests. Online launches fetch the national pools
and replace the snapshot only after every response is successful. Reports and
other server mutations remain network-only.

A source timestamp is stale at 30 days (inclusive), is exposed through
`dataStale`, and is shown as “Necesită reîmprospătare” while retaining cached
content. `invalidateOfflineDataset()` is the deterministic reset operation.
