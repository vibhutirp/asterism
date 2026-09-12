# Observatory 3D exploration QA

September 12, 2026. Branch: `codex/conversational-memory-ux`. Local preview: http://localhost:4173/. No deployment or backend changes.

The approved [spatial exploration specification](../docs/design/observatory/spatial-exploration.md) supersedes the historical flat-map reference. The implementation retains its typography, category colors, dark reading surface, luminous controls and solid focus outlines, while replacing the map and reserved column with volumetric topic clouds and a floating inspector.

## Verification

- `npm test`: 16/16 tests passed, including deterministic volume generation, bounded count scaling, the global particle cap, append-only centers, interrupted transitions, filtering, provenance, stale responses and the two permitted GET endpoints.
- `npm run typecheck`: passed.
- `npm run build`: passed. Vite reports a large lazy-loaded 3D chunk, approximately 251 KB gzip; the main application is approximately 75 KB gzip.
- `npm run test:sites`: 4/4 template hosting tests passed.
- Independent code review completed. Closing an inspector during a focus transition was corrected to cancel the transition and preserve the current pose.

## Browser checks

Checked in the Codex in-app browser at 1440 × 1024, 1100 × 800 and 720 × 512 CSS pixels.

| Interaction or state | Observed result |
| --- | --- |
| Workspace overview | Existing sample dataset preserved: 10 topics, 42 memories; 10 actual clouds and 1,280 particles. Categories group the clouds. [Overview](qa/3d/overview.png) |
| Selection and source disclosure | Cloud geometry and HTML labels both select. The camera frames the selected topic beside the inspector; its heading receives focus. Typed memories and complete original text retain author, channel, Received timestamp and sample identity. [Selected source](qa/3d/selected-source.png) |
| Orbit and selection discrimination | Drag changed camera orientation without selecting another topic. Navigation interrupts a focus transition. |
| Zoom and pan | Wheel and keyboard zoom changed the camera. Shift-arrow panning changed its target. Reset restored workspace framing. |
| Inspector independence | Scrolling the floating reader left camera position and target unchanged. Closing during a transition preserved the exact observed pose after closure and restored the invoking label focus. |
| Search and List | Case-insensitive Camping filtering returned the same topic in both views. Switching views preserved search, selection and camera. No-match state included Clear search. [No match](qa/3d/no-match.png) |
| Crowded scene | 50 topics, 6,400 particles; visible labels had no overlapping DOM rectangles. Label count stayed below 16, with an explicit List alternative for hidden labels. [Crowded](qa/3d/crowded.png) |
| Refresh and idle rendering | Camera position and target remained identical over 155 seconds of polling. Only 74 frames rendered in that interval, associated with data refreshes rather than an idle animation loop. |
| Keyboard | Labels select with keyboard input; details focus the heading; disclosure retains button focus; closure restores the opener. Canvas arrows, Shift-arrows, plus/minus and Home provide camera control. |
| Reduced motion | Development fixture override confirmed immediate camera focus and no inertia. Closing retained the pose. |
| Compact and long content | Intermediate inspector was 400px wide. Compact List-first layout stacked the inspector; long names and a 4,808-character source wrapped without horizontal overflow. [Compact source](qa/3d/compact-long-source.png) |
| Recent updates | Compact popover opened; Escape closed it and restored its trigger. Fixture/session semantics remain unchanged. |
| WebGL recovery | The development fixture invoked the actual WEBGL_lose_context extension. The app displayed an explanation and switched to List; topic and original-source reading continued. [Fallback](qa/3d/webgl-fallback.png) |
| Read-only boundary | Existing repository tests confirm only the two relative GET endpoints. Scene and camera code add no data requests. Existing adaptation and stale-response tests still pass. |

Issues corrected during visual QA included an effectful Canvas fallback incorrectly activating List, overly dim particle colors, labels disappearing at the scene edge, label collisions, unstable initial camera configuration and camera motion continuing after inspector closure.

## Coverage limits

Physical touch pinch, hardware right-button dragging, OS-level reduced-motion changes and native browser 200% zoom were not exercised. Keyboard equivalents, the reduced-motion fixture and compact viewport reflow were checked. Actual context loss was tested; cold hardware WebGL initialization failure was covered by the fallback implementation rather than a separate hardware environment.

This pass did not repeat the earlier live API failure/refresh browser matrix; those data paths were retained and their focused tests rerun. See the historical [reader QA](design-qa.md) for loading, empty, failed-read, stale-data and missing-source evidence. The original three-topic arrangement is represented in stable-center unit tests; the current ten-topic sample was preserved for browser checks.
