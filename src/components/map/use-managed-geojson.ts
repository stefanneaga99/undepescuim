'use client';

import { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useMap } from 'react-leaflet';

type FeatureLike = GeoJSON.Feature;

type WorkItem<T extends FeatureLike> = {
  id: string;
  kind: 'update' | 'add' | 'replace' | 'remove';
  feature?: T;
};

export type ManagedGeoJSONOptions<T extends FeatureLike> = {
  data: GeoJSON.FeatureCollection;
  getId?: (feature: T) => string;
  style?: L.StyleFunction;
  pointToLayer?: (feature: T, latlng: L.LatLng) => L.Layer;
  onEachFeature?: (feature: T, layer: L.Path) => void;
  pane?: string;
};

type ManagedLayer = {
  feature: FeatureLike;
  layer: L.GeoJSON;
  geometrySignature: string;
};

type QueueItem<T extends FeatureLike> = WorkItem<T>;

function geometrySignature(feature: FeatureLike): string {
  return JSON.stringify(feature.geometry);
}

export function createFeatureWorkQueue<T extends FeatureLike>(
  existing: Map<string, T>,
  next: T[],
  getId: (feature: T) => string,
) {
  const nextById = new Map(next.map((feature) => [getId(feature), feature]));
  const work: QueueItem<T>[] = [];

  for (const [id, previous] of existing) {
    const current = nextById.get(id);
    if (!current) {
      work.push({ id, kind: 'remove' });
    } else if (geometrySignature(previous) !== geometrySignature(current)) {
      work.push({ id, kind: 'replace', feature: current });
    } else {
      work.push({ id, kind: 'update', feature: current });
    }
  }
  for (const feature of next) {
    const id = getId(feature);
    if (!existing.has(id)) work.push({ id, kind: 'add', feature });
  }

  let cursor = 0;
  return {
    map: <R>(mapper: (item: QueueItem<T>) => R): R[] => work.map(mapper),
    flush: (deadline: number, isCurrent: () => boolean, apply: (item: QueueItem<T>) => void) => {
      while (cursor < work.length && isCurrent() && performance.now() < deadline) {
        apply(work[cursor]);
        cursor += 1;
      }
      return cursor < work.length;
    },
  };
}

/**
 * Maintains one Leaflet layer per feature id while the viewport changes.
 * Structural work is scheduled in short animation-frame slices so a moveend
 * cannot synchronously remount an entire GeoJSON collection.
 */
export function useManagedGeoJSON<T extends FeatureLike>({
  data,
  getId = (feature) => String(feature.properties?.slug ?? ''),
  style,
  pointToLayer,
  onEachFeature,
  pane,
}: ManagedGeoJSONOptions<T>) {
  const map = useMap();
  const optionsRef = useRef({ getId, style, pointToLayer, onEachFeature, pane });
  const layersRef = useRef(new Map<string, ManagedLayer>());
  const generationRef = useRef(0);

  useEffect(() => {
    optionsRef.current = { getId, style, pointToLayer, onEachFeature, pane };
    const generation = ++generationRef.current;
    const current = layersRef.current;
    const existingFeatures = new Map<string, T>();
    for (const [id, entry] of current) existingFeatures.set(id, entry.feature as T);
    const features = data.features as T[];
    const queue = createFeatureWorkQueue(existingFeatures, features, optionsRef.current.getId);
    let frame = 0;

    const configure = (entry: ManagedLayer, feature: T) => {
      entry.feature = feature;
      entry.geometrySignature = geometrySignature(feature);
      entry.layer.eachLayer((child) => {
        if (optionsRef.current.style && 'setStyle' in child) {
          (child as L.Path).setStyle(optionsRef.current.style(feature));
        }
        child.off('click');
        optionsRef.current.onEachFeature?.(feature, child as L.Path);
      });
    };

    const create = (feature: T) => {
      const opts: L.GeoJSONOptions = {
        style: optionsRef.current.style,
        pane: optionsRef.current.pane,
        pointToLayer: optionsRef.current.pointToLayer as L.GeoJSONOptions['pointToLayer'],
      };
      const layer = L.geoJSON(feature, opts);
      layer.addTo(map);
      const entry = { feature, layer, geometrySignature: geometrySignature(feature) };
      layersRef.current.set(optionsRef.current.getId(feature), entry);
      if (optionsRef.current.onEachFeature) {
        layer.eachLayer((child) => optionsRef.current.onEachFeature?.(feature, child as L.Path));
      }
    };

    const apply = (item: QueueItem<T>) => {
      const existingEntry = layersRef.current.get(item.id);
      if (item.kind === 'remove') {
        existingEntry?.layer.removeFrom(map);
        layersRef.current.delete(item.id);
      } else if (item.kind === 'replace') {
        existingEntry?.layer.removeFrom(map);
        layersRef.current.delete(item.id);
        if (item.feature) create(item.feature);
      } else if (item.kind === 'add' && item.feature) {
        create(item.feature);
      } else if (item.kind === 'update' && existingEntry && item.feature) {
        configure(existingEntry, item.feature);
      }
    };

    const flush = () => {
      if (generationRef.current !== generation) return;
      const more = queue.flush(performance.now() + 4, () => generationRef.current === generation, apply);
      if (more) frame = requestAnimationFrame(flush);
    };
    frame = requestAnimationFrame(flush);

    return () => {
      generationRef.current += 1;
      cancelAnimationFrame(frame);
    };
  }, [data, map, getId, style, pointToLayer, onEachFeature, pane]);

  useEffect(
    () => () => {
      for (const entry of layersRef.current.values()) entry.layer.removeFrom(map);
      layersRef.current.clear();
    },
    [map],
  );
}

export function ManagedGeoJSONLayer<T extends FeatureLike>(props: ManagedGeoJSONOptions<T>) {
  useManagedGeoJSON(props);
  return null;
}
