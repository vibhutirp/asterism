# Observatory design QA

The current control layout is documented in [Compact controls QA](design-qa-controls.md). [Galaxy overview QA](design-qa-galaxies.md) preserves the prior spatial refinement. The earlier [3D exploration QA](design-qa-3d.md) and sections below preserve historical implementation evidence.

## Demo dataset verification — September 12, 2026

Expanded fixture mode to 10 topics, 42 memories, 30 distinct original messages, and six fictional teammates. This section supersedes the fixture counts in the original implementation evidence below; those screenshots document the earlier three-topic dataset.

- `npm test`: all 10 tests passed, including integrity checks for counts, unique memory IDs, complete and consistent shared provenance, sample identity, fixed valid timestamps, isolated detail copies, and crowded-scenario records.
- `npm run typecheck` and `npm run build`: passed, including template packaging.
- `npm run test:sites`: all four hosting tests passed.
- Browser checked at http://127.0.0.1:4173 in the Codex in-app browser. Header displayed **10 topics · 42 memories**, with six Product and four Personal topics. Universe showed four topics with an explicit **Showing 4 of 10 topics** overflow affordance at the current 1280 × 720 viewport.
- Opened Atlas onboarding and verified all eight typed memories, overview, authors, and Received timestamps. Expanded its first original and verified the complete message contains both onboarding and camping context, with the Sample source label. Visually inspected the rendered map and inspector.
- List exposed all ten topic rows with matching counts. Searching `launch` left only Preview launch; clearing restored the topics. Returned to Universe with onboarding selected and the first original expanded for the demo.

Limits: this data-only update did not repeat the full earlier responsive/accessibility/API browser matrix. No real Slack data was imported and no deployment was performed. The existing bounded map intentionally requires List to browse all ten topics. Fixed fixture dates do not advance with the clock. See [demo-data.md](demo-data.md) for the three-minute walkthrough.

## Original implementation verification

Result: **passed** for the implemented reader and the verification coverage below.

Date: September 12, 2026. Branch: `codex/conversational-memory-ux`.
Browser: Codex in-app browser. Main reference viewport: 1440 × 1024 CSS pixels.

## Visual comparison

Compared the approved `../docs/design/observatory/exploration-only.png` and the rendered application together in [reference-comparison.png](qa/reference-comparison.png), with Atlas onboarding selected and its decision source expanded. The generated reference was normalized from 1487 × 1058 to the documented 1440 × 1024 viewport.

The implementation follows the written design system where the image differs: 64px header, 512px inspector, 24px panel padding, 28/36 topic title, 16/24 memory text, 14/20 metadata, 44px controls, opaque label backings, neutral memory-type badges, and 2px solid focus outlines with 3px offset. Those dimensions were also inspected in the browser. Source timestamps are explicitly Received; unsupported Slack connectivity and historical update claims from the reference are omitted.

The star-free nebula retains blue-violet Product and teal Personal regions, with interactive topic stars rendered separately. It is intentionally restrained beneath the labels. There are no relationship lines or continuous motion. Exact nebula texture and topic slots differ from the generated reference. The inspector scrolls naturally when source content exceeds the viewport.

Issues resolved during QA:

- Reduced background brightness so topic light remains legible.
- Corrected the view-switch hit targets to 44px and metadata to the documented minimum size.
- Reserved the map overflow row and recent-updates height so filtering/activity does not shift existing stars.
- Allowed 112px rows (above the 96px minimum) for two-line labels with an update badge.
- Fixed repeat selection clearing a loaded inspector without re-fetching it.
- Kept the search accessible name stable when its clear button appears.
- Removed misleading loading copy after a failed initial read.
- Kept compact inspector title and close control accessible when opening a topic.

No outstanding substantive visual or usability mismatch was found in the exercised states.

## Functional browser checks

| Check | Evidence / result |
| --- | --- |
| Universe → topic → memory → source | Full multi-topic original retained, including the camping question in the onboarding source. Idea and Decision remain distinct. [Main screen](qa/observatory-1440.png) |
| List/search equivalence | Trimmed, case-insensitive `PRICING` returned the same one topic in both views; selection and disclosure survived the switch. |
| No match | Clear search available; no invented results. Closing a topic whose opener was filtered out focused the search. [No match](qa/no-match.png) |
| Stable positions | Camping star bounds stayed exactly x=85.59375, y=581.0390625 before/after filtering a crowded map down to Camping. |
| Crowded map | 43 topics; 4 safely mapped at the test viewport; View all topics exposed all 43 list rows, including topic 40 by search. [Crowded map](qa/crowded-map.png) |
| Empty universe | Zero persisted counts, no fictional saved activity, guidance toward connected services. [Empty](qa/empty.png) |
| Loading | Reading state, no saved counts before successful read. [Loading](qa/loading.png) |
| Failed initial read | Visible error and read retry; unavailable state instead of sample fallback. [API failure](qa/api-initial-failure.png) |
| Failed refresh | Previously loaded topics and detail remained with explicit stale notices. [API stale data](qa/api-failed-refresh.png), [fixture stale data](qa/stale-data.png) |
| Detail failure | Visible error with read retry; no substituted memories. |
| Missing provenance | Original text unavailable; no disclosure button or fabricated quote/author/channel. [Missing source](qa/missing-source.png) |
| Long names and sources | Full topic title in inspector; 4,605-character original retained and wrapped without horizontal overflow. [Long source](qa/long-source.png) |
| Keyboard | Enter selects; heading receives focus; disclosure preserves button focus; Escape closes and restores opener. Tab advances to the next star with a computed 2px solid #BEDCFF outline and 3px offset. [Focus](qa/keyboard-focus.png) |
| Compact layout | 1100px viewport uses 400px inspector; 720px viewport stacks List and inspector. No horizontal overflow, including long text. [Compact](qa/compact-200-percent-reflow.png) |
| API contract | Browser used a temporary local HTTP test server through the configured Vite proxy. Correct Topic description, Statement, Received, missing original, and no historical updates. [API detail](qa/api-contract.png) |
| Late responses | Selected a 1,200ms first topic then an 80ms second topic. Second title and memories remained after the delayed response. |
| Polling | Request log confirms list and selected detail refresh at ten-second intervals. Visibility/focus event handling is implemented and code-reviewed. |
| Read-only boundary | Server observed only the two allowed GET routes through selections, filtering and view changes. [Request evidence](qa/api-requests.txt). No web creation or AI-query controls exist. |

## Coverage limits

- 200% **equivalent reflow** was verified at 720 × 512 CSS pixels for the 1440 × 1024 target; the available browser tool does not expose native browser zoom. Actual native 200% zoom remains a manual check.
- The page has no running CSS animations. The browser-exposed reduced-motion media rule disables all transitions/animations and smooth scrolling. An OS preference toggle was not emulated; that native preference check remains manual.
- API-mode tests used a disposable local contract server, not real Slack ingestion or the pending backend deployment. Full original-source inspection in real API mode depends on the backend exposing that text. Background/foreground polling wiring was inspected; automated hidden-tab timing was not measured.
- This is focused hackathon QA, not a screen-reader certification or a cross-browser accessibility audit.

## Automated checks

- `npm test`: 9 focused tests pass (filtering, response adaptation, missing provenance, URL validation, stable positions, observed updates, stale-response gating, read-only API contract, shared fixture sources).
- `npm run typecheck`: passes.
- `npm run build`: passes, including the preserved template packaging step.
- `npm run test:sites`: 4 preserved template tests pass, including rejection of write/API requests from the static fallback.

Preview remains at http://localhost:4173 in fixture mode. The temporary API contract server and secondary API preview were stopped after QA. No deployment was performed.
