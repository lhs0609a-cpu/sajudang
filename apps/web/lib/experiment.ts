"use client";
import { analyticsId, track } from './track';

export function entryVariant(): number | null {
  const sid = analyticsId();
  if (!sid) return null;
  let h = 2166136261;
  for (const c of 'entry-value-v1:' + sid) h = Math.imul(h ^ c.charCodeAt(0), 16777619) >>> 0;
  return h % 2;
}

export function exposeEntry(): number | null {
  const arm = entryVariant();
  if (arm !== null) track('experiment_exposed', 'a1', { n: 1, stage: arm });
  return arm;
}
