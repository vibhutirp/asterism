# Compact exploration controls QA

September 12, 2026 · `codex/conversational-memory-ux` · local preview http://localhost:4173/.

The [current spatial specification](../docs/design/observatory/spatial-exploration.md) defines this refinement. The Apple Maps reference informed compact grouping and control placement; galaxy artwork, particles, data and inspector dimensions are retained.

## Automated verification

- `npm test`: **29/29 passed**, including seven focused obstacle-placement tests plus existing filtering, API adaptation, provenance, stable centers, aggregation and stale-response coverage.
- `npm run typecheck`: passed.
- `npm run build`: passed, including Sites packaging. The lazy Three.js chunk remains large (approximately 256 KB gzip); Vite reports its existing chunk-size advisory.
- `npm run test:sites`: **4/4 passed**. Static/SPA serving works and missing API/write requests do not become application HTML.
- Independent code review completed; substantive findings were fixed and re-reviewed.

## Browser checks

Checked in the Codex in-app browser at 1440×1024, 1024×640, 720×800, 720×512 and 390×844 CSS pixels.

| Check | Observed result |
| --- | --- |
| Overview | Header shows 10 topics / 42 memories. Compact switch is top-center, 200×44 search bottom-center, navigation icons bottom-left. Both galaxies remain central. [Overview](qa/controls/overview.png) |
| Search | Focus expands the same input to 420px. Nonempty blur retains expansion; empty blur collapses to 200px. Clear restores input focus. Camera position remained `93.712,91.694,232.263` before/after focus and filtering. |
| Escape with inspector | First Escape cleared `atlas`; second collapsed search and focused Universe. The Atlas inspector and expanded original remained open. |
| Inspector positioning | At 1440px, both centered controls moved to x=440 in the 880px remaining scene. The inspector retained its 512px width. Atlas source shows the complete multi-topic message, author, channel, Received timestamp and sample label. [Source](qa/controls/topic-source.png) |
| Pointer and keyboard | Galaxy entry reveals topics; settled Atlas pointer selection opens its inspector on the first click. Enter selection focuses its heading. Zoom in/out, Reset, Pause/Resume work through icon controls. Pause sets breathing false; Resume restores true. Keyboard focus exposes named tooltips. |
| Help and updates | Both popovers show readable dark surfaces. Close buttons and Escape restore the corresponding invoker. Help stays below the switch at 1024×640 with the 400px inspector open, and scrolls internally. [Short desktop Help](qa/controls/help-short-desktop.png) |
| List | Desktop rows scroll between switch and search, camera controls disappear, source disclosure remains open and camera state is preserved. [List](qa/controls/list.png) |
| Crowded collision avoidance | With 50 topics, open Help and expanded 420px search, eight visible topic labels had **zero overlaps** with each other or measured control/popover rectangles. [Crowded Help + search](qa/controls/crowded-help-search.png) |
| Compact reflow | List is initial below 1024px; search sits above rows and inspector stacks below. At 390px Universe remains 720px high, has 16px control insets, a 200px resting search pill, and no horizontal overflow. [Compact List](qa/controls/compact-list.png), [narrow Universe](qa/controls/narrow-universe.png) |
| Reduced motion | Fixture override yields search transition `0s`, immediate 420px width, breathing false and an aria-disabled Resume control. |
| Read states | Loading remains visible below the switch; empty, no-match and failed-read surfaces are distinct. Stale fixture retains the galaxies and persisted totals with an explicit failed-refresh notice. [Empty](qa/controls/empty.png), [no match](qa/controls/no-match.png), [failure](qa/controls/failed-read.png), [stale](qa/controls/stale-data.png) |
| WebGL fallback | Context-loss fixture switches to a working List reader with a visible explanation and disabled Universe control. [Fallback](qa/controls/webgl-fallback.png) |
| 200% reflow equivalent | 720×512 CSS-pixel viewport exercises the available layout at half of 1440×1024, retaining search, switch, readable notices and scrollable content. [Evidence](qa/controls/200-percent-equivalent-reflow.png) |

## Fixes made during verification

- Removed the Help stacking restriction and bounded its height so it cannot sit behind the view switch on short desktops.
- Measured actual rendered label sizes, including wrapping, instead of relying on undersized fixed height estimates.
- Reused existing label placements for focus/hover-only changes. This prevents a label moving between pointerdown and pointerup and swallowing selection.
- Removed inherited empty-state margins and large vertical gaps, keeping read-state feedback compact beneath the switch.

## Coverage limits

The in-app browser did not change page zoom in response to the native zoom shortcut and exposes only viewport dimensions. Native 200% browser zoom is therefore **not verified**; equivalent CSS reflow is recorded separately. Reduced motion was exercised through the existing development fixture rather than changing the operating-system setting. Hidden-tab suspension, touch pinch and live API sessions were not repeated for this layout-only pass; their implementations remain unchanged and existing API tests pass. Browser logs retain the dependency's Three.Clock deprecation warning; the context-loss fixture also produces a WebGL cleanup warning.

No backend changes, new endpoints, dependencies, data-writing controls or deployment. All changes remain local and the preview stays running.
