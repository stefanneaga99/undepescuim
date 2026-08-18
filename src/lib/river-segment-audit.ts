export type Coord = readonly [number, number];
export type Way = { osm_id?: number; id?: number; coordinates?: Coord[]; geometry?: Coord[] };

const EARTH_M = 6_371_000;
export const haversineM = (a: Coord, b: Coord): number => {
  const r = Math.PI / 180;
  const [lon1, lat1, lon2, lat2] = [a[0], a[1], b[0], b[1]].map((v) => v * r);
  const dlon = lon2 - lon1, dlat = lat2 - lat1;
  const q = Math.sin(dlat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dlon / 2) ** 2;
  return 2 * EARTH_M * Math.asin(Math.min(1, Math.sqrt(q)));
};
export const lineLengthM = (line: readonly Coord[]) => line.slice(1).reduce((n, p, i) => n + haversineM(line[i], p), 0);

const coords = (w: Way) => w.coordinates ?? w.geometry ?? [];
const endpoint = (p: Coord, eps: number, keys: { p: Coord }[]) => {
  for (let i = 0; i < keys.length; i++) if ((eps > 0 && haversineM(p, keys[i].p) <= eps) || (eps === 0 && p[0] === keys[i].p[0] && p[1] === keys[i].p[1])) return i;
  keys.push({ p }); return keys.length - 1;
};
const graph = (ways: readonly Way[], snapEpsM = 0) => {
  const keys: { p: Coord }[] = [], edges = new Map<string, { id: number; length: number; coords: Coord[] }>(), adj = new Map<number, Set<number>>();
  for (const w of [...ways].sort((a, b) => (a.osm_id ?? a.id ?? 0) - (b.osm_id ?? b.id ?? 0))) {
    const c = coords(w); if (c.length < 2) continue;
    const a = endpoint(c[0], snapEpsM, keys), b = endpoint(c[c.length - 1], snapEpsM, keys);
    if (!adj.has(a)) adj.set(a, new Set()); if (!adj.has(b)) adj.set(b, new Set()); adj.get(a)!.add(b); adj.get(b)!.add(a);
    const key = `${Math.min(a, b)}:${Math.max(a, b)}`;
    edges.set(key, { id: w.osm_id ?? w.id!, length: lineLengthM(c), coords: c.map((p) => [...p] as Coord) });
  }
  return { adj, edges };
};
export const connectedComponents = (ways: readonly Way[], snapEpsM = 0): number[][] => {
  const { adj, edges } = graph(ways, snapEpsM), seen = new Set<number>(), out: number[][] = [];
  for (const start of [...adj.keys()].sort((a, b) => a - b)) { if (seen.has(start)) continue; const stack = [start], ids = new Set<number>(); seen.add(start);
    while (stack.length) { const n = stack.pop()!; for (const next of [...adj.get(n)!].sort((a, b) => a - b)) { const e = edges.get(`${Math.min(n, next)}:${Math.max(n, next)}`); if (e) ids.add(e.id); if (!seen.has(next)) { seen.add(next); stack.push(next); } } }
    out.push([...ids].sort((a, b) => a - b));
  }
  return out.sort((a, b) => (a[0] ?? -1) - (b[0] ?? -1));
};
export const topology = (ways: readonly Way[], snapEpsM = 0) => { const { adj, edges } = graph(ways, snapEpsM); const degree = Object.fromEntries([...adj.entries()].sort((a, b) => a[0] - b[0]).map(([k, v]) => [String(k), v.size])); return { components: connectedComponents(ways, snapEpsM).length, node_degree: degree, branch_nodes: Object.entries(degree).filter(([, v]) => v > 2).map(([k]) => k), ways: [...edges.values()].map((e) => e.id).sort((a, b) => a - b) }; };

const nearest = (p: Coord, line: readonly Coord[]) => { if (!line.length) return Infinity; const scale = Math.cos(p[1] * Math.PI / 180); let best = Infinity;
  for (let i = 0; i + 1 < line.length; i++) { const a = line[i], b = line[i + 1], ax = (a[0] - p[0]) * scale, ay = a[1] - p[1], bx = (b[0] - p[0]) * scale, by = b[1] - p[1], dx = bx - ax, dy = by - ay, den = dx * dx + dy * dy, t = den ? Math.max(0, Math.min(1, -(ax * dx + ay * dy) / den)) : 0; best = Math.min(best, haversineM(p, [p[0] + (ax + t * dx) / scale, p[1] + ay + t * dy])); }
  return line.length > 1 ? best : haversineM(p, line[0]);
};
const samples = (line: readonly Coord[]) => { if (line.length < 2) return []; const total = lineLengthM(line), count = Math.max(2, Math.ceil(total / Math.max(100, total / 100)) + 1), out: { fraction: number; cumulative_m: number; coordinate: Coord }[] = [];
  for (let i = 0; i < count; i++) { const fraction = i / (count - 1), target = total * fraction; let walked = 0; for (let j = 0; j + 1 < line.length; j++) { const seg = haversineM(line[j], line[j + 1]); if (walked + seg >= target || j + 2 === line.length) { const t = seg ? (target - walked) / seg : 0; out.push({ fraction, cumulative_m: target, coordinate: [line[j][0] + (line[j + 1][0] - line[j][0]) * t, line[j][1] + (line[j + 1][1] - line[j][1]) * t] }); break; } walked += seg; } }
  return out;
};
export const coverage = (published: readonly Coord[], osm: readonly Coord[], toleranceM = 125) => { const pub = samples(published).map((s) => ({ ...s, distance_m: nearest(s.coordinate, osm) })); const raw = samples(osm).map((s) => ({ ...s, distance_m: nearest(s.coordinate, published) })); return { published_to_osm: pub.length ? pub.filter((s) => s.distance_m <= toleranceM).length / pub.length : 0, osm_to_published: raw.length ? raw.filter((s) => s.distance_m <= toleranceM).length / raw.length : 0, published_samples: pub, osm_samples: raw }; };
