# Observatory spatial exploration

This approved revision supersedes the previous 2D-only layout and fixed inspector column. The web application remains a read-only reader; API contracts and provenance semantics are unchanged.

## Representation

At topic detail, a cloud is a topic. At overview, a cloud aggregates one category as a galaxy. Its points are deterministic visual texture, not individual memories. Product and Personal retain their blue and teal identities. The cloud radius follows `min(10, 4 + 0.6 * log2(memoryCount))`, with no cloud for zero memories. Counts remain visible and authoritative; perspective also changes apparent size. Category proximity is organization, not a claim of a relationship between topics.

The frontend owns append-only world positions, seeded ellipsoid particles, camera state, and projected labels. API/display models do not acquire coordinates. Each nonempty cloud uses 128 particles unless its share of the global 64,000-particle budget is smaller. New topics append to category slots; memory refreshes and name filtering never rearrange existing centers. No ambient rotation, particle drift, postprocessing bloom, or relationship lines.

## Controls

- Left-drag orbits; Shift-drag or right-drag pans; wheel or two-finger pinch zooms. Motion and distance are bounded.
- A pointer move greater than 5px is a drag, not a topic selection. Clicking a cloud or its HTML label selects the topic.
- Selection glides toward a framing beside the inspector in 450ms. Dragging or another camera command cancels that motion. Closing cancels focus motion and preserves the current pose, including projection offset.
- Zoom in/out and Reset view are native buttons. Reset frames all workspace galaxies at the aggregated overview level, even while a filter is active, without clearing search or selection.
- On the focused canvas, arrows orbit, Shift-arrows pan, plus/minus zoom, and Home resets. Topic labels and List rows are native buttons.
- Reduced motion uses immediate focus and no inertia. Source disclosure, filtering, refreshes, and switching views do not reset the camera. Selecting a different topic in List is an explicit focus request applied when Universe returns.

## Floating surfaces

The full workspace under the 64px header renders the 3D scene. The compact controls revision below defines current overlay placement. The header holds persisted totals and a Recent updates icon; its popover retains sample/session-observed labels.

The inspector is visible only on selection. It sits 24px from the top, right and bottom; width is 512px at desktop ≥1280px and 400px at 1024–1279px. It uses 24px padding, a 16px radius, near-opaque dark fill, and a subtle luminous edge. Its scroll never reaches the camera controls behind it.

Topic labels remain crisp HTML surfaces with exact counts, selected borders, and solid keyboard focus. Up to 16 topic labels are shown, prioritizing selected/focused/hovered topics and avoiding collisions with other labels and UI. Alternate placements around a cloud keep edge labels visible. A visibility count and List provide the fallback for density. Lists retain complete names even when map labels are clamped.

Below 1024px, the same workspace defaults to List and stacks the inspector in document flow. Universe remains available as a 720px-high full-width scene. No separate mobile product is added.

## Failure and performance

A WebGL initialization failure or context loss shows a clear notice and moves to List; memory inspection continues. Read failures never switch API data to fixtures. The renderer remains demand-driven. While Universe is visible and breathing is enabled, a timer requests at most 30 glow frames per second; user-driven transitions can render at display cadence. List, hidden tabs, Pause animation and reduced motion stop the breathing timer. Idle data refreshes can still schedule frames. Geometry is disposed on unmount, pixel ratio is capped at 1.5, and the 3D bundle is lazy-loaded.

Development-only fixture QA supports `?motion=reduce` to exercise immediate camera behavior and `?scene=context-loss` to trigger an actual WebGL context loss. Both overrides are ignored in production and API mode; neither changes saved knowledge.

## Galaxy overview and living glow — current refinement

This section supersedes always-visible topic clouds, the earlier no-looping-animation rule, and topic-only initial/reset framing.

Product appears as a blue-violet galaxy and Personal as a cyan-teal galaxy. Each has a procedural, layered gradient billboard anchored at its world-space center. Camera movement changes its screen position; there are no decorative stars, background motion or postprocessing bloom. Reading panels retain dark solid surfaces.

A galaxy center is the midpoint of its initial category topic-center bounds. It never moves during a session. Its radius is at least 18 world units and includes each initial center plus the fixed maximum topic radius of 10. Only newly observed topic IDs may expand it; filters and memory counts cannot shrink or resize it. Current totals and matching-topic counts are computed separately from this geometry.

At camera distance ≥5 galaxy radii, the category is one aggregate cloud; at ≤3 radii, its individual topic clouds are fully revealed. The intermediate blend uses smoothstep and an interruptible 450ms transition. The same points interpolate on the GPU between deterministic aggregate positions and canonical topic positions, retaining the global 64,000-point cap. Aggregate radius is 0.58 times the category bounds radius. A count change can resize a topic but never its center.

Galaxy labels expose exact category topic and persisted-memory totals. A filtered galaxy also shows the number of matching topics; zero-match galaxies are omitted. Galaxy selection approaches to 2.8 radii and does not select a topic or open an inspector. Reset fits the full category overview without clearing search or selection. Filters never move the camera.

Galaxy and topic labels crossfade with detail. At the midpoint, the interactive level changes; selected/focused topic labels are retained, with bounded fallback placement when necessary. Once a keyboard-focused galaxy reveals topics, focus transfers to a visible topic label without selecting it. Hidden labels cannot receive keyboard or pointer interaction. Closing an inspector restores its visible invoker or falls back to search.

Point luminance follows an eight-second sine cycle between 90% and 100% of its normal level. Topic-ID phase offsets avoid synchronized flashing. No particle positions, sizes, background gradients or labels breathe. Pause animation stops the cycle; Resume animation restores it. Reduced motion disables breathing, camera easing, aggregation easing and inertia. The Resume control is disabled with an explanatory title while the system preference is active.

## Compact controls — current layout

This section supersedes the large top-left toolbar, visible Your knowledge heading, permanent instruction card and bottom legend. The heading remains available to screen readers. Galaxy artwork, camera behavior, particle motion and inspector dimensions remain unchanged.

The scene's shared overlay frame ends 560px before the desktop right edge when the inspector opens (448px at 1024–1279px). The Universe/List switch and search center within this remaining width. Frame repositioning takes 200ms ease-out and never moves the camera.

- The 44px-high Universe/List segmented switch sits 24px beneath the header, with short labels and line icons.
- Search sits 24px above the scene bottom. Its single input is a 200 × 44px pill, expanding to 420px over 200ms ease-out on focus and clamping to the available space. It stays expanded while focused or nonempty. Empty blur collapses it. Clear retains input focus. Escape first clears a query; a second Escape collapses and focuses the selected view button. Search consumes Escape before inspector/popover dismissal.
- Navigation sits bottom-left, 24px inset. Zoom in/out share a rounded vertical capsule; Reset, Pause/Resume and Help follow with 8px gaps. All navigation buttons have 44px targets, 18–20px luminous line icons, accessible names, solid focus outlines and hover/focus tooltips.
- Help is a scrollable dark popover above the lower controls. It explains gestures, canvas keyboard shortcuts, decorative particle semantics, exact counts and List browsing. Closing restores the Help button. It stays below the switch on short screens and above other scene surfaces.
- The header replaces the previous tagline with actual topic/memory totals and places Recent updates beside workspace status. Its popover opens below the header. Closing restores the updates button. Only one of Help and updates is open at a time.
- Loading, empty, no-match, failed-read and stale-read messages remain visible in compact surfaces below the switch. They are never hidden in Help.

Label placement measures actual controls, expanded search, open popovers, notices, inspector and rendered label dimensions. It excludes their rectangles plus an 8px gap, instead of reserving large top/bottom bands. Selected/focused labels get priority and nearest available fallback positions. Hover/focus changes reuse existing positions when camera/data/obstacle geometry has not changed, preventing labels from jumping during a click. Where no rectangle can fit, List remains the complete reader.

Desktop List scrolls between the centered switch and search; camera controls are hidden. Below 1024px List remains the initial view, the inspector stacks below, and search appears above the rows. Universe retains a 720px scene and compact overlays. Edge insets become 16px below 620px; all widths clamp to fit. Reduced motion removes search and frame transitions as well as existing scene motion. Floating reading surfaces isolate pointer and scrolling input from the canvas.

These are frontend layout states and DOM measurements only: no new requests, dependencies, backend fields or data mutation controls.
