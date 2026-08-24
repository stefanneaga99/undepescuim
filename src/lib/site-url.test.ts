import { describe, expect, it } from "vitest";
import { siteMetadata } from "@/lib/site-metadata";
import { CANONICAL_SITE_URL, SITE_URL, siteUrl } from "@/lib/site-url";
import robots from "@/app/robots";
import sitemap from "@/app/sitemap";

describe("canonical site URLs", () => {
  it("uses the custom apex in production metadata", () => {
    expect(CANONICAL_SITE_URL).toBe("https://unde-pescuim.ro");
    expect(siteMetadata.metadataBase?.toString()).toBe(`${SITE_URL}/`);
    expect(siteMetadata.alternates?.canonical).toBe("/");
    expect(siteMetadata.openGraph?.url).toBe(`${SITE_URL}/`);
  });

  it("generates first-party absolute URLs from one site origin", () => {
    expect(siteUrl("/sitemap.xml")).toBe(`${SITE_URL}/sitemap.xml`);
    expect(siteUrl("robots.txt")).toBe(`${SITE_URL}/robots.txt`);
  });

  it("publishes canonical sitemap and robots targets", () => {
    expect(sitemap().map((entry) => entry.url)).toEqual([
      `${SITE_URL}/`,
      `${SITE_URL}/specii`,
      `${SITE_URL}/permis`,
      `${SITE_URL}/sesizeaza`,
    ]);
    expect(robots()).toMatchObject({
      sitemap: `${SITE_URL}/sitemap.xml`,
      host: `${SITE_URL}/`,
    });
  });
});
