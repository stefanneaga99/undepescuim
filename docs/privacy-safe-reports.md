# Privacy-safe map reports

Status: implemented baseline; operator policy must be reviewed before production use.

## Public payload contract

`POST /api/report` accepts the required structured fields `reason`, `waterSlug`, and
`waterName`, plus the existing bot honeypot. GitHub issue creation uses only:

- one enumerated reason (`data_correct`, `water_invalid`, `association_changed`,
  `wrong_coordinates`, or `other`);
- the sanitized canonical water name and slug; and
- a fixed operator-generated disclosure line.

The endpoint deliberately ignores optional legacy fields such as `details`,
`contactEmail`, `reportContext`, location, screenshots, headers, and arbitrary
metadata. Ignoring them preserves the core report instead of forcing a user to
submit personal data. They must never be copied to an issue, digest, analytics
record, or application log. The UI discloses this immediately before submission:
do not enter contact data, location, secrets, or allegations about third parties.

The water identity is checked for presence and bounded length server-side and is
allowlist-sanitized again before it reaches GitHub. The reason is checked against
the fixed server-side enumeration. GitHub failures log only the HTTP status; no
request body, token, IP address, or upstream response body is logged.

## Abuse controls and retention

The report endpoint retains no application-side report database. The in-memory
sliding limiter is five accepted attempts per client key in ten minutes and the
in-memory duplicate coalescer expires after sixty seconds. Both are best-effort
per warm server instance, not an identity system or a global guarantee. Client
IP-derived keys are transient abuse-control state only and are not put in issue
payloads or logs; configure the hosting provider's access-log retention
separately and disable/request-minimize those logs where possible.

GitHub is the public processor/storage surface for accepted issues. The operator
must configure an administrative retention job or manually remove issues when
the documented retention period expires; this repository does not claim that
GitHub automatically deletes reports. The chosen retention period and hosting
provider settings must be recorded by the operator before production use.

## DSAR and takedown

For a deletion request, correction request, or takedown of a public issue, use
the operator's verified private contact channel: **[OFFICIAL EMAIL]**. Do not
invent an identity or put private details in a GitHub issue. Include the public
issue URL only when necessary to locate the record. Until the operator fills in
that channel, the form intentionally provides no private free-text/contact
channel.

Deleting or editing a GitHub issue does not guarantee immediate deletion from
notifications, email, caches, search indexes, forks, screenshots, or third-party
backups. The operator must request propagation/deletion from relevant recipients
where feasible and document the residual limits in the response to the requester.

This document is an implementation record, not legal advice. **[LEGAL ENTITY]**,
**[ADDRESS]**, the lawful basis, exact retention periods, controller/processor
roles, international-transfer safeguards, and Romanian counsel approval remain
release conditions.
