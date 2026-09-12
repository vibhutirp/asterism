# Galaxy overview and living glow QA

September 12, 2026. Branch: `codex/conversational-memory-ux`. Preview: http://localhost:4173/.

The approved galaxy plan and [spatial specification](../docs/design/observatory/spatial-exploration.md) supersede the earlier topic-only overview. The reference image informed the blue-violet and cyan atmosphere; procedural gradients stay anchored to category centers, without adding decorative stars or new artwork. Existing data modes, sample data, inspector and API boundary remain intact.

## Verification results

- `npm test`: **22/22 passed**. Six new tests cover deterministic aggregation, stable bounds and centers, exact filtered/category totals, distance scaling, transition reversal/settling, seeded eight-second glow and the shared particle cap.
- `npm run typecheck`: passed.
- `npm run build`: passed. The existing lazy 3D chunk is now approximately **254 KB gzip**; Vite still reports its large-chunk advisory.
- `npm run test:sites`: **4/4 passed**.
- Independent code review completed and fixes re-reviewed. No substantive findings remain from that review.

## Browser evidence

Checked in the Codex in-app browser at 1440 × 1024 and 720 × 800 CSS pixels.

| Check | Observed result |
| --- | --- |
| Overview | Two combined galaxies: Product **6 topics · 30 memories**; Personal **4 topics · 12 memories**. Separate atmospheres and prominent labels make category membership explicit. [Overview](qa/galaxies/overview.png) |
| Intermediate zoom | Two Zoom in actions produced independent detail values of approximately Product 0.48 and Personal 0.056. Points morph in place and labels crossfade; the dominant level remains interactive. [Intermediate](qa/galaxies/intermediate.png) |
| Galaxy → topic → source | Entering Product reveals topics without opening an inspector. Selecting Customer discovery opens its typed memories; the original research message retains author, channel, Received timestamp and sample identity. [Source](qa/galaxies/topic-source.png) |
| Focus handoff | Keyboard galaxy entry transfers focus to a revealed topic without selecting it. Topic entry focuses the inspector heading. Closing at overview retains and focuses the invoking topic label. Closing after switching to List falls back to search. |
| Reset and filtering | Reset retained the open Customer discovery inspector and the `customer` filter while returning both category detail values to zero. CAMPING filtering left one matching topic in Personal, with its full 4-topic/12-memory totals labeled separately; camera position and target were identical before/after filtering. [Filter](qa/galaxies/filter.png) |
| No matches | Visible no-match message and Clear search restored the overview. |
| Navigation interruption | Orbit dragging interrupted galaxy travel. The target remained at the interruption point as drag inertia settled, rather than continuing toward the requested galaxy center. |
| Breathing and pause | Actual shader brightness varied between the expected base-scaled limits (observed 0.765–0.85 for an unselected topic). Pause fixed brightness at 0.85; only eight refresh-related frames occurred over a 12-second paused sample. Resume restarted the cycle. The final timer interval is 34ms, so decorative requests cannot exceed 30fps. |
| List suspension | Only eight refresh-related frames occurred over 16.6 seconds in List; brightness and camera remained constant. |
| Crowded data | 50 topics / 82 memories rendered as two galaxies with **6,400 particles**, preserving the sample dataset. Product had 33 topics/57 memories; Personal had 17/25. Both labels remained visible. Revealed scene had nine topic labels, no overlapping interactive label rectangles and a visible List alternative. [Overview](qa/galaxies/crowded.png), [detail](qa/galaxies/crowded-detail.png) |
| Reduced motion | `?motion=reduce` produced immediate Personal galaxy entry, detail 1, breathing false and a disabled Resume control with explanation. Keyboard focus transferred to a topic. |
| Compact layout | Initial view was List. Universe remained available with both galaxy labels, wrapping controls and no horizontal overflow at 720px. Selecting Camping placed the inspector below the scene and focused its heading. [Compact](qa/galaxies/compact.png) |
| WebGL loss | The actual context-loss fixture removed the scene and showed the existing explanatory List fallback. [Fallback](qa/galaxies/webgl-fallback.png) |
| Read-only data | Existing endpoint/adaptation/stale-response tests pass. Galaxy code adds no requests, backend fields or dependencies. |

## Issues resolved

- Updated actual shader-material uniforms each frame so geometry and glow follow the computed transition.
- Gave galaxy labels alternate placements and a bounded fallback so crowded overview never loses a category solely because two labels collide.
- Preserved selected/focused labels across aggregation and camera depth changes, including available edge slots.
- Restored focus before clearing selection to prevent the overview from removing an invoking topic label mid-closure.
- Checked invoker visibility before restoration so hidden Universe labels cannot receive focus in List.
- Kept dominant labels legible during partial zoom rather than leaving both levels faint.

## Coverage limits

The visibility-change handler and timer cleanup were code-reviewed. The in-app browser continued reporting `document.hidden=false` when another tab was opened, so actual hidden-tab suspension could not be exercised on this surface. List and Pause suspension were observed directly. Physical touch pinch, native 200% browser zoom and an OS preference change were not repeated; compact reflow and the reduced-motion fixture were checked instead. Existing API failure/provenance behavior was covered by the retained tests and earlier reader QA, not a new live backend session.

Changes remain local on the current branch. No backend modification, live ingestion, new integration or deployment was performed.
