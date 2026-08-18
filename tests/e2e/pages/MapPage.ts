/**
 * POM — the map page (/) — composes Header + FilterBar + map + detail cards.
 * Docs/e2e-test-plan.md §4.3.
 */
import { expect, type Page } from '@playwright/test';
import { Selectors } from '../helpers/selectors';
import {
  clickWaterByPixel,
  clickWaterBySlug,
  countAllPaths,
  countPathsByColor,
  mapZoom,
  setMapZoom,
} from '../helpers/map';
import { Header } from './Header';
import { FilterBar } from './FilterBar';
import { WaterDetailCard } from './WaterDetailCard';
import { NearbyWatersSheet } from './NearbyWatersSheet';
import { AssociationChip } from './AssociationChip';
import { AssociationSearch } from './AssociationSearch';

export class MapPage {
  readonly header: Header;
  readonly filterBar: FilterBar;
  readonly waterCard: WaterDetailCard;
  readonly nearbySheet: NearbyWatersSheet;
  readonly associationChip: AssociationChip;
  readonly associationSearch: AssociationSearch;

  constructor(private readonly page: Page) {
    this.header = new Header(page);
    this.filterBar = new FilterBar(page);
    this.waterCard = new WaterDetailCard(page);
    this.nearbySheet = new NearbyWatersSheet(page);
    this.associationChip = new AssociationChip(page);
    this.associationSearch = new AssociationSearch(page);
  }

  get root() {
    return this.page.getByTestId(Selectors.mapRoot);
  }

  get leafletContainer() {
    return this.page.locator('.leaflet-container');
  }

  get locateButton() {
    return this.page.getByTestId(Selectors.locateButton);
  }

  get geolocationBubble() {
    return this.page.getByTestId(Selectors.geolocationBubble);
  }

  /** Deterministic click: open the water's detail card. */
  async clickWater(slug: string): Promise<void> {
    await clickWaterBySlug(this.page, slug);
    await expect(this.page.getByTestId(Selectors.waterCard)).toBeVisible();
  }

  /** REAL pointer click through Leaflet's hit pipeline (used sparingly). */
  async clickWaterByGesture(slug: string): Promise<void> {
    await clickWaterByPixel(this.page, slug);
    await expect(this.page.getByTestId(Selectors.waterCard)).toBeVisible();
  }

  zoom(): Promise<number> {
    return mapZoom(this.page);
  }

  /** Set the map zoom programmatically (LOD tests need zoom ≥ 8). */
  zoomTo(z: number): Promise<void> {
    return setMapZoom(this.page, z);
  }

  /** Center the map at a geographic point (uncontracted overlays are
   * viewport-culled — click targets must be panned into view first). */
  async panTo(lat: number, lon: number, zoom?: number): Promise<void> {
    await this.page.evaluate(
      ([la, lo, z]) => {
        // Leaflet is exposed only through the E2E test bridge.
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const map = (window as any).__UNDEPESCUIM_MAP__;
        if (!map) throw new Error('panTo: leaflet map bridge not available');
        map.setView([la, lo], z ?? map.getZoom());
      },
      [lat, lon, zoom ?? null],
    );
  }

  pathCount(): Promise<number> {
    return countAllPaths(this.page);
  }

  pathsByColor(colors: readonly string[]): Promise<number> {
    return countPathsByColor(this.page, colors);
  }
}
