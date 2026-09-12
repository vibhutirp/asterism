import { useLayoutEffect, useState } from 'react';
import type { RefObject } from 'react';
import type { Rect } from './overlay-layout.ts';

/** Measure UI in scene coordinates, including animated widths and popovers outside the canvas parent. */
export type LabelSizes = Record<string, { w: number; h: number }>;

export function useSceneObstacles(scene: RefObject<HTMLDivElement | null>) {
  const [rects, setRects] = useState<Rect[]>([]);
  const [labelSizes, setLabelSizes] = useState<LabelSizes>({});
  useLayoutEffect(() => {
    const element = scene.current, app = element?.closest('.app-shell');
    if (!element || !app) return;
    let frame = 0;
    const observed = new Set<Element>();
    const measure = () => {
      frame = 0;
      const origin = element.getBoundingClientRect();
      const next = [...app.querySelectorAll<HTMLElement>('[data-scene-obstacle]')].filter(node => {
        const bounds = node.getBoundingClientRect();
        return node.getClientRects().length > 0 && getComputedStyle(node).visibility !== 'hidden'
          && bounds.bottom > origin.top && bounds.top < origin.bottom && bounds.right > origin.left && bounds.left < origin.right;
      }).map(node => {
        const bounds = node.getBoundingClientRect();
        return { x: Math.round(bounds.left-origin.left), y: Math.round(bounds.top-origin.top), w: Math.ceil(bounds.width), h: Math.ceil(bounds.height) };
      });
      setRects(previous => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
      const measured: LabelSizes = {};
      for (const label of app.querySelectorAll<HTMLElement>('[data-label-key]')) {
        const bounds = label.getBoundingClientRect();
        if (bounds.width && bounds.height) measured[label.dataset.labelKey!] = { w: Math.ceil(bounds.width), h: Math.ceil(bounds.height) };
      }
      // Retain measurements through aggregation/filtering; hidden labels need no offscreen copies.
      setLabelSizes(previous => {
        const updated = { ...previous, ...measured };
        return JSON.stringify(previous) === JSON.stringify(updated) ? previous : updated;
      });
    };
    const schedule = () => { if (!frame) frame = requestAnimationFrame(measure); };
    const resize = new ResizeObserver(schedule);
    const reconcile = () => {
      const current = new Set<Element>([element, ...app.querySelectorAll('[data-scene-obstacle],[data-label-key],.overlay-frame,.app-header')]);
      for (const node of observed) if (!current.has(node)) { resize.unobserve(node); observed.delete(node); }
      for (const node of current) if (!observed.has(node)) { observed.add(node); resize.observe(node); }
      schedule();
    };
    const mutation = new MutationObserver(reconcile);
    mutation.observe(app, { childList: true, subtree: true });
    window.addEventListener('scroll', schedule, true); window.addEventListener('resize', schedule);
    reconcile();
    return () => { cancelAnimationFrame(frame); resize.disconnect(); mutation.disconnect(); window.removeEventListener('scroll', schedule, true); window.removeEventListener('resize', schedule); };
  }, [scene]);
  return { obstacles: rects, labelSizes };
}
