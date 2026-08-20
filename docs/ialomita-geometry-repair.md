# Râul Ialomița geometry repair

The production chord was limited to slug `3ek8e82l` (`Râul Ialomița`, AJVPS
Dâmbovița, `Fieni - Buftea`). No association, ownership, contract, source, or
sector fields were changed.

| artifact | before | after |
|---|---|---|
| `geometry` canonical SHA-256 | `0fd8e49df786a43316dc2e323eef15b35981880c5fd6f279c05ab311e1d86b45` | `6023865f5a9de2b9c14980b292f4987803771cf3be965fb08ea24efdddc4cf08` |
| geometry type | 5,128-point `LineString` | 71-part `MultiLineString` |
| longest consecutive edge | 49.888 km | 0.606 km |
| county clip | generated from malformed core | regenerated from repaired core (`dambovita`) |

The approved after-geometry is restored byte-for-byte from
`git:6b3fe61^:public/data/waters.json`. The audit now reports a
`published_geometry_jump` independently of relation exceptions, so a reviewed
OSM relation cannot mask a malformed rendered payload.
