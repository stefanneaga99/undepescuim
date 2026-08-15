/**
 * UndePescuim.ro — national recreational-fishing permit (F1a).
 *
 * In Romania, fishing any contracted water legally requires TWO permits:
 *   1. the national "permis de pescuit recreativ" issued by ANADSPA
 *      (https://permise.anpa.ro/portal-public/permis), and
 *   2. the association's own permit/abonament for that water.
 *
 * The national-permit link is a CONSTANT shown on every contracted water,
 * alongside the association-specific permit row (permitUrl on the water /
 * association record, populated from arebaltapeste `link_permis`).
 *
 * Centralized here so the URL is trivial to update.
 */
export const NATIONAL_PERMIT_URL = 'https://permise.anpa.ro/portal-public/permis';
export const NATIONAL_PERMIT_LABEL = 'Permis național de pescuit (ANADSPA)';
