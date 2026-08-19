# Association locations

`data/processed/association_locations.json` is the curated, versioned source artifact for public association contact locations. `public/data/association_locations.json` is its byte-for-byte public projection and is loaded separately from `associations.json`.

Each record must retain:

- the canonical association id and slug;
- a source-supported function (`headquarters`, `club_contact_point`, `permit_pickup_point`, or `partner_location`);
- locality, county, public address/contact channels, source URL and checked date;
- `freshness`, confidence, review and publication gates.

The validator rejects unknown associations, invalid URLs/dates/enums, unapproved records, invalid phones, and pickup records without explicit permit wording. Legacy `adresa`, `telefon` and `siteUrl` fields remain intact and are used as a fallback when the optional artifact is unavailable. Locations are never inferred from managed-water geography or geocoding. `needs_confirmation` records remain visible with that qualification and do not imply a permit pickup function.
