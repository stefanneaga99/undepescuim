import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";
import { proxy } from "./proxy";

describe("host canonicalization proxy", () => {
  it("permanently redirects www while preserving path and query", () => {
    const request = new NextRequest(
      "https://www.unde-pescuim.ro/ape/raul-olt?county=BV&view=map",
      { headers: { host: "www.unde-pescuim.ro" } },
    );

    const response = proxy(request);

    expect(response.status).toBe(308);
    expect(response.headers.get("location")).toBe(
      "https://unde-pescuim.ro/ape/raul-olt?county=BV&view=map",
    );
  });

  it("does not redirect the apex domain", () => {
    const request = new NextRequest("https://unde-pescuim.ro/data/waters.json", {
      headers: { host: "unde-pescuim.ro" },
    });

    const response = proxy(request);

    expect(response.status).toBe(200);
    expect(response.headers.get("location")).toBeNull();
  });

  it("does not redirect the Vercel rollback domain", () => {
    const request = new NextRequest("https://undepescuim.vercel.app/", {
      headers: { host: "undepescuim.vercel.app" },
    });

    const response = proxy(request);

    expect(response.status).toBe(200);
    expect(response.headers.get("location")).toBeNull();
  });
});
