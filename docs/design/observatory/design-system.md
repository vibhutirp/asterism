# Observatory design system v0.1

A compact specification for the approved dark, luminous, exploration-only web application. This defines design decisions; it does not implement application components or introduce backend capabilities.

## Authority and scope

Use this document for exact rules and tokens.json for portable design values. design-system.png is an illustrative visual companion, not a pixel ruler: generated spacing bars, measurements, colors and font rendering can be approximate. Product behavior remains governed by README.md. This system refines the approved visual concept; it does not change its information architecture.

Users browse topics, memories and original sources. Every supported action is navigation, disclosure, filtering or a read retry. No Capture, Ask, save/edit/delete, integration configuration or demo mutation controls belong in the component inventory.

## 1. Principles

1. Space gives context: position, proximity and category regions help users locate knowledge.
2. Light guides interaction: icons and actionable edges glow; paragraphs remain sharp.
3. Evidence stays attached: each memory leads directly to its original source.
4. Meaning survives styling: Idea, Decision and Question remain explicit text labels, with no implied certainty hierarchy.
5. Stability builds recognition: a source update changes content and counts without moving unrelated stars.
6. Quiet by default: reserve strong light for hovered, focused or selected elements. Do not illuminate every surface.

The information hierarchy is workspace → category → topic → memory → source. Each level has a different visual role, not a separate decorative card.

## 2. Foundations and semantic colors

| Role | Value | Use |
|---|---|---|
| canvas | #080D19 | Universe base and application background |
| panel | #101827 | Solid reading panel and header |
| raised | #182338 | Inset overview and resting controls |
| hover | #202E45 | Active pointer surface |
| source | #0C1422 | Original-message inset |
| primary | #EDF2FA | Titles, memory text, quotations |
| secondary | #B6C2D5 | Supporting text and attribution |
| muted | #95A5BE | Timestamps and placeholders; never lower-opacity body text |
| quietBorder | #2A3850 | Decorative separators only |
| controlBorder | #657C9E | Necessary resting control boundaries |
| icon | #DAE9FF | Crisp icon strokes |
| link | #8DC6FF | Read/navigation links |
| accent | #B8A7FF | Hover/selected action emphasis |
| focus | #BEDCFF | Solid keyboard-focus outline |
| onAccent | #101321 | Text if a filled accent control is needed |
| product | #83B8FF | Product category |
| personal | #7DDECA | Personal category |
| saved | #7DDECA | Saved status icon, always paired with text |
| processing | #C8B6FF | Reported processing status |
| error | #FFB4B4 | Reported failure icon/text |
| badgeSurface / badgeText | #1D2940 / #C7D4E8 | All memory-type badges |
| labelBacking | #13203A | Opaque backing behind map text |

Category color expresses membership; status color expresses process outcome. The same hue may occur in those distinct contexts, so words and icons must identify the meaning. All Idea/Decision/Question/Statement badges share a neutral treatment: a green Decision badge would visually conflate content type with successful processing.

Do not add a broad rainbow taxonomy. Add another category color only when the predefined model actually contains another category and its text contrast has been verified.

### Space background and figure/ground

Use diffuse nebula fields behind topics, with no decorative point stars. Nebulae are background grouping regions, not diagrams of relationships. Keep the inspector, header, toolbar and activity reading areas solid. Their text must not sit directly on a variable image.

Map labels use opaque labelBacking behind their complete text bounds with 4px vertical and 8px horizontal padding, no border, and a small 4px radius. This is contrast support, not a button card. Keep nebula brightness lower behind labels; do not rely on a glow or text shadow to rescue contrast.

## 3. Typography

Use Inter, weights 400/500/600. A single family is sufficient. Package the required font locally during implementation if available; system-ui, -apple-system, Segoe UI, sans-serif is the fallback. Do not block rendering or add a second display font.

| Role | Size / line height | Weight | Application |
|---|---|---|---|
| Title | 28 / 36px | 600 | Topic title; workspace wordmark may use this role |
| Section | 20 / 28px | 600 | Your knowledge, category headings, Recent updates |
| Body | 16 / 24px | 400 | Memories, overview, original messages |
| Topic | 16 / 24px | 500 | Map and list topic names |
| Control | 14 / 20px | 500 | Search, switches, links, disclosures |
| Metadata | 14 / 20px | 400 | Author, source identity, timestamp |
| Badge | 14 / 20px | 600 | Memory type and process labels |

Use sentence case. Uppercase is permitted only for short memory-type labels. Avoid large letter spacing; use normal tracking for body and controls and up to 0.02em for uppercase badges. Do not create hierarchy by making metadata faint or too small.

Reading measure target: 45–65 characters where space permits. Source and memory text wrap freely, including long URLs. Never truncate original text. Topic labels may wrap to two lines on the map and then ellipsize; the full name remains available through the accessible name and the unclamped inspector heading.

[Inter reference](https://rsms.me/inter/).

## 4. Spacing, alignment and shape

Base unit: 4px. Approved spacing scale: 4, 8, 12, 16, 24, 32, 48, 64px. Values are layout distances, not random component sizes.

| Distance | Meaning / default |
|---|---|
| 4px | Heading-to-count, small internal adjustments |
| 8px | Icon-to-label; closely related lines |
| 12px | Between toolbar controls; metadata-to-disclosure |
| 16px | Inset padding; source-block indentation |
| 24px | Panel padding and row vertical breathing room |
| 32px | Between inspector sections |
| 48px | Major separation or empty-state inset |
| 64px | Preferred separation between galaxy groups |

Align topic name, overview, memories and source disclosures to the same inspector content edge. Only original-message content is indented. Align metadata to the statement's text edge, not to a badge's optical center.

Memory anatomy: type → 8px → statement → 8px → metadata → 12px → disclosure. Expanded source starts 12px below the disclosure, with 16px padding and a 2px quote rule. Each memory row has 24px vertical padding and a 1px divider. Row content grows naturally; no fixed-height memory cards.

Control radius: 8px. Inset overview radius: 12px. Badge radius: 4px. Source block: square with a left rule; no nested card border required. Pills are reserved for circular star selection, not every label. Borders do not substitute for meaningful spacing.

## 5. Spatial layout and responsive reading

Current revision: the approved galaxy overview and 3D cloud model supersedes the previous 2D star grid, fixed inspector column, and no-pan/zoom restrictions. Full behavior is documented in [spatial-exploration.md](spatial-exploration.md).

The scene fills the workspace beneath the 64px header. Search, Universe/List, updates, and camera controls float above the background. The inspector appears on selection, inset 24px on the right/top/bottom, 512px wide at ≥1280px and 400px at 1024–1279px. Its 16px radius, near-opaque panel surface and quiet luminous edge distinguish reading content from space. Closing it preserves the camera pose.

Below 1024px, default to List. Universe remains a 720px full-width exploration region, with the inspector below it in normal document flow. Content reflows without horizontal page scrolling.

### Cloud density and stable positions

At overview, each cloud represents a galaxy with category totals. At detail, each cloud represents one topic. Its seeded particles are visual texture, not individual memory records. Cloud world radius is min(10, 4 + 0.6 × log2(memoryCount)) for counts ≥1; zero-memory topics remain available in List without a cloud. Exact persisted counts remain the authority because perspective changes apparent size. No brightness or size implies confidence, truth or importance.

Topic centers occupy stable append-only 3D slots grouped by category; filtering, source order, and count changes cannot move them. Each cloud starts with 128 deterministic particles; total particles are capped at 64,000 by reducing per-cloud density. No force layout or ambient particle drift. Zoom-level changes morph the same points between a combined galaxy and stable topic positions.

Visible HTML labels are capped at 16 and placed around projected topic centers with collision avoidance. Selected, focused and hovered topics take priority. Each label is a native button with a name, category and count in its accessible name; List exposes all topics when labels are hidden by density or the viewport.

Left-drag orbits, Shift/right-drag pans, scroll/pinch zooms. Camera controls provide Zoom in/out and Reset view, with bounded movement. Selection frames a topic beside the inspector in 450ms, interrupted by user navigation. Reduced motion makes focus immediate and disables inertia. Updates and filters never reset the camera.

## 6. Gestalt principles applied

| Principle | Application in Observatory | Failure to avoid |
|---|---|---|
| Proximity | 8px related spacing keeps a memory with its metadata; 32px separates sections. Star labels sit next to their stars. | Equal spacing everywhere makes unrelated content look attached. |
| Similarity | Every topic uses the same star grammar; all memory types use the same neutral badge structure. | Giving a Decision a stronger glow implies greater truth or importance. |
| Common region | Each subtle nebula groups related topics. The solid inspector groups one selected topic's details. | Nested boxes and hard galaxy borders imply extra hierarchy or exact boundaries. |
| Figure–ground | Stars are luminous; reading areas and label backings are solid; text remains sharp. | Bright clouds behind attribution make atmosphere compete with evidence. |
| Continuity | Source expansion follows directly below its memory; reading keeps one left alignment. | Opening a source in a distant panel makes its relationship hard to track. |
| Closure | A clear selection ring identifies one topic; diffuse category fields suggest grouping without enclosing everything. | Decorative constellation lines suggest unsupported relationships. |
| Consistency and simplicity | One topic target, one source disclosure pattern, one focus treatment, and a small spacing scale. | Different control shapes for equivalent actions increase interpretation work. |
| Spatial stability | Updated memories change in place; the selected name in the inspector matches the selected star/list row. | Force-layout reflow makes users relearn their knowledge map. |

Galaxy grouping combines proximity, blue-violet or cyan-teal atmosphere, and prominent category labels. The eight-second 10% breathing cycle is decorative and never conveys confidence, status or group membership; all reading surfaces stay stationary.

## 7. Light, icons and motion

Use one 20px line-icon family with 1.75px rounded strokes; 16px icons are allowed only next to a visible label. All icon-only controls have a 44px hit target and an accessible name. Source/service identities use genuine available assets or plain text, never invented integration logos.

Required icons: Search, Universe, List, Document/source, disclosure chevrons, Close, external link, Info, processing status, Saved check and failure. Do not resurrect Capture or Ask icons from superseded boards.

| State | Surface / light |
|---|---|
| Rest | Raised or panel surface; controlBorder where needed; crisp icon with a subtle halo |
| Hover | hover surface; accent edge; localized halo; no movement or layout change |
| Pressed | Return toward raised surface; smaller halo; no scale transform |
| Selected | Persist ring/label emphasis independently of hover |
| Keyboard focus | 2px solid focus outline, 3px offset; outline coexists with selected state |
| Disabled | Matte, no glow; no hover or action response |
| Loading | Text plus static activity icon; no shimmer needed |
| Failure | Error icon plus explanation; only read failures can offer a read retry |

Glyph halo: 4px blur at 22% and 10px at 12%, using icon color. Hover halo: 8px at 22% and 20px at 14%, using accent. Topic halo: 6px at 45% and 18px at 22%, using category color. These halos surround the crisp foreground shape; they never replace its solid stroke.

Keep stronger glow on the active target, not its whole panel. Transition halo opacity/surface color for 150ms ease-out; do not animate blur radius, layouts or star positions. New data may receive a single 600ms highlight fade, accompanied by persistent Updated text. Reduced motion sets transitions to immediate and retains the badge. No sound, flashing, shimmer or animated nebula assets. The approved exception is an eight-second seeded glow cycle dimming stars by at most 10%, with Pause/Resume controls. Camera focus and galaxy aggregation use 450ms transitions. Reduced motion removes all three effects and camera inertia.

## 8. MVP component anatomy

| Component | Required anatomy / behavior |
|---|---|
| Topic search | Visible label, search icon, placeholder, 44px field, standard text-input behavior; clearing filters never writes knowledge |
| Universe/List switch | Two 44px view buttons; selected state plus text; preserve selection/query; use native button semantics |
| Topic cloud | Volumetric dots, adjacent name/count, optional New/Updated text; one topic target with a native label button |
| Topic list row | Minimum 72px; 16px vertical padding; title, category/count metadata, optional update label; grows for wrapped content |
| Topic inspector | Title, category/count, source identity/latest update, overview, ordered memories, inline provenance; close control |
| AI overview | 16px padding, raised surface, explicit AI overview label; no decorative sparkle suggesting truth |
| Memory row | Neutral type label, statement, attribution, View original disclosure; divider-based grouping |
| Original source | source surface, 2px left rule, full text, author/channel/timestamp, genuine link only when available |
| Recent update | Read-only source/status, persisted outcome, affected topic link; no ingestion retry or creation action |
| Status / empty / error | Icon and concise words; honest origin/status; no fake source integration or confidence score |

Type badges are not controls. Sample data and connection labels are informational and do not glow on hover. Links may glow subtly on hover but also underline. Do not show an artificial primary CTA in a reading view.

## 9. Accessibility and quality gates

Target WCAG 2.2 AA. Require ≥4.5:1 for normal text and ≥3:1 for necessary component/state boundaries; focus must remain visible and unobscured. These targets come from [text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html), and [focus visibility under overlays](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html).

Our 44px target is a product default with extra room, not a claim that WCAG AA requires 44px. See the [WCAG 2.2 target-size criterion](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

The declared palette has 49 checked pairings. Lowest checked normal-text ratio is 5.463:1; the lowest necessary control-border pairing is 3.205:1. These calculations apply to specified solid backgrounds only. See contrast-report.md. Rendered backgrounds, real font rendering, native focus behavior and zoom still require verification.

Keyboard: logical order header → search → view switch → topics → updates → inspector. Opening topic detail moves focus to its heading; closing restores the invoker. Source disclosure keeps focus on its button and exposes expanded/collapsed state. Use native controls; decorative icons and star effects are hidden from assistive technology. Every topic accessible name includes its name, category and memory count.

Polite status announcements report actual saved updates once; do not announce every poll. If content loading fails, preserve available content with a stale-data message. Color never carries type, category or status alone.

Verify at 1440×1024 and 1280×800, 200% browser zoom, keyboard-only operation, reduced motion, long topic names, long original sources, no-match, crowded map, stale data and disconnection. Ensure focus rings are not clipped. Do not call the application accessible based solely on these tokens or images.

## 10. Implementation scope and order

First establish tokens, text, spacing and solid surfaces. Then build search/list/inspector and source disclosure. Then apply stars, stable slots, category nebulae and halos. Finally verify keyboard behavior, contrast and content edge cases.

Reuse the same primitives across the reader: Button, IconButton, SearchField, ViewSwitch, TopicTarget, MemoryRow, SourceDisclosure, and StatusLabel. No general-purpose enterprise component library, theme editor, animation engine, graph physics, or extra backend endpoints are needed.

Keep tokens.json as portable design data; it is intentionally not a framework-specific stylesheet. Exact implementation adapters can follow the selected frontend stack. No app code is part of this design-system deliverable.
