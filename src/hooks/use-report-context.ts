'use client';

import { useCallback } from 'react';
import { parseReportContext } from '@/lib/report-context';
import type { ReportContextInput, ReportContextV1 } from '@/types/report-context';

export type MapContextReader = () => ReportContextInput['map'];
let mapReader: MapContextReader | null = null;
export function registerReportMapReader(reader: MapContextReader | null) { mapReader = reader; }
export function readReportMapContext() { return mapReader?.() ?? null; }

/** Creates the one snapshot used by a report submit; it never stores context. */
export function useReportContext(builder?: () => ReportContextInput | null) {
  return useCallback((): ReportContextV1 | null => {
    try { return parseReportContext(builder?.() ?? null); } catch { return null; }
  }, [builder]);
}
