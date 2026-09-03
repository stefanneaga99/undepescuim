const CANONICAL_SITE_URL = "https://unde-pescuim.ro";
const LOCAL_SITE_URL = "http://localhost:3000";

/**
 * The public origin used for canonical metadata and absolute first-party URLs.
 * Production intentionally defaults to the custom domain, including Vercel
 * previews, so preview deployments never publish a vercel.app canonical.
 */
export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL?.trim() ||
  (process.env.NODE_ENV === "test" || process.env.NODE_ENV === "development"
    ? LOCAL_SITE_URL
    : CANONICAL_SITE_URL);

export const siteUrl = (path = "") =>
  new URL(path.replace(/^\//, ""), `${SITE_URL}/`).toString();

export { CANONICAL_SITE_URL };
