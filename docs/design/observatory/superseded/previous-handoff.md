# Observatory UX and visual handoff

Status: approved visual direction; Capture and Ask mockups prepared for review. These are static image concepts, not implemented capabilities. Application code has not changed.

## References

- topic-inspection.png — approved dark galaxy workspace and source inspection; illustrative earlier sample snapshot.
- interaction-style.png — approved luminous icons, buttons, focus, and selected-star treatment.
- capture.png — completed multi-topic web capture; ready for the next message.
- grounded-answer.png — workspace-wide question with citations and one original source expanded.
- generation-prompts.md — exact prompts for the two new screens, using the built-in Image Generation tool.

The topic-inspection reference establishes appearance. The Capture and Ask pair use the consistent sample story below; do not combine their source identities with the earlier illustrative Slack snapshot.

## Stable workspace

One main screen: persistent universe/list on the left, one contextual panel on the right. Topic inspection, Capture, and Ask replace panel content. Keep separate drafts and preserve the latest answer when switching. The recent-capture strip is another view of the same receipt, not a duplicate stored event.

Universe > predefined category (galaxy) > stable topic > typed memory. Label concepts in ordinary language: category names, topics, memories, AI overview, Original message. Include project identity in topic names.

Every map star is a topic. Category nebulae are diffuse fields with no decorative star points or relationship lines. Stable topic slots prevent re-layout when a memory arrives. Count only persisted, deduplicated memories. Exact totals are available as text; bound star core sizes so small count differences remain modest.

The map can retain its last selected topic while Capture or Ask is open. A selection ring identifies that topic only; it never implies question scope. Scope is explicit in the Ask panel. The Capture close control shown in the image returns to the last inspected topic; omit it when there is no previous topic. Ask remains reachable at all times.

Find topics by name is case-insensitive filtering of topic names in both Universe and List. List rows show category, count, and update state and open the same topic inspector.

## Light and interaction system

Deep navy canvas; midnight reading surface; offwhite text; violet actions; icy-blue icon strokes; sage Personal category. Use a consistent line-icon family with rounded strokes and a small halo. Paragraphs and original sources have no bloom.

- Rest: crisp icon strokes and quiet localized light.
- Hover: brighter edge and modest halo, without layout movement.
- Pressed: darker fill and tighter light.
- Keyboard focus: crisp 2px outline with offset, supported by glow.
- Disabled: matte, no glow.
- Selected topic: ring and label emphasis; selection does not change memory count or star core size.
- Transition target: approximately 150ms. Reduced motion uses immediate/static states. No pulsing stars or continuous nebula motion.
- Status always has text and an icon. Brightness never represents truth, confidence, importance, or retrieval rank.
- Verify contrast and visible focus in actual implementation; generated images are not accessibility validation.

## Capture behavior and states

Capture explicitly saves new context. Ask retrieves existing context. Never infer which action the user intended from text alone. Deliberately captured questions remain Questions.

The empty composer has a disabled Save context action. Use the final helper copy "Source: Web capture" in implementation rather than the mockup's "Saved as a web message", which could suggest the new empty draft was already saved.

Received and Organizing states show text plus an indicator. No optimistic memory counts, new stars, or success badges before persistence is confirmed. Saved receipts name affected topics and distinguish New from Updated. Clicking a receipt topic opens its inspector. Clear the successful submission from the composer; keep its original text in the receipt.

Extraction failure preserves the draft/source and explains that organization failed. Show an actual server outcome, not a fabricated rollback or saved-memory count. Offer retry only with duplicate-safe backend support; no automatic replay after an uncertain result.

Empty universe: "No saved context yet" and usable Capture. Loading sample data is a separate Demo control. Slack disconnected leaves web capture available and clearly says so.

Sample, Live, and Replay identify origin independently of Received/Organizing/Saved/Failed. Use only real source links. No functional-looking Connect, MCP, or provider controls.

## Ask behavior and states

Opening Ask normally defaults to All topics. Ask about this topic explicitly adds a removable topic scope chip for one submission. Preserve that scope label with the submitted question/answer. The next question resets to All topics. A highlighted star never silently restricts retrieval.

Submitted questions and generated answers are not automatically saved. Keep Ask and Capture drafts separate. Disable duplicate submission while answering.

Answering shows "Finding relevant context…" with an activity indicator. A grounded response includes claim-level citation controls and actual used-memory/topic totals returned by the service. Citations expand supporting original messages inline without losing the answer.

No relevant evidence: "No relevant stored context was found for this question." Offer rephrasing and clearing a topic scope where applicable. Distinguish service failure from lack of evidence and preserve the question on failure.

Show a context-limit omission notice only if the service reports that relevant candidates were omitted. Never imply exhaustive search or infer omissions from a small used-memory count.

## Canonical sample story for Capture and Ask

All timestamps are sample data on September 12, 2026, in the displayed workspace timezone.

Before capture: two Product topics, two memories total.
1. Alex, Web capture, 2:10 PM: "Idea for Atlas onboarding: try a three-step setup checklist." Extract one Idea into Atlas onboarding.
2. Alex, Web capture, 2:12 PM: "For Atlas pricing, an idea is to test a $12 monthly plan." Extract one Idea into Atlas pricing.

At 2:14 PM:
"For Atlas onboarding, we decided to pilot the three-step checklist with five new users. Separately, for the camping trip, could we borrow Maya’s tent?"

Persist one Decision into existing Atlas onboarding and one Question into new Personal topic Camping trip. Final counts: three topics, four memories; onboarding two, pricing one, camping one. Receipt: Saved · 2 memories. Mark these origins as Sample; no external source link.

Ask across All topics:
"What has been decided for Atlas, and what is still only proposed?"

Illustrative retrieval selects onboarding Decision and pricing Idea: two memories from two topics. The answer cites the onboarding pilot decision as [1] and the pricing proposal as [2], explicitly stating that retrieved context does not establish pricing approval. Expanding [1] reveals the full original multi-topic web message, including its unrelated camping sentence. That unrelated sentence is provenance, not a second retrieved memory. The universe remains at three topics and four memories after asking.

## Backend boundary

No backend redesign is specified. Minimum response information needed: persisted capture outcome and affected topics; stable topic/memory IDs and counts; memory types; original source identity/text/timestamp and optional genuine URL; grounded answer and citation references; actual used-memory/topic totals. An optional omission indicator supports limit messaging. Generated topic overviews depend on the backend; show "Overview unavailable" when absent.

Server-side reset, duplicate-safe retry, Slack ingestion/status, and live retrieval are pending capabilities, not made real by these mockups. Clearly label fixtures until connected. Demo reset requires deliberate confirmation and clears only the shared demo workspace's data while preserving category definitions.

Manual correction, topic merge/split, automatic conflict resolution, semantic search, graph editing, integration settings and MCP are outside this frontend slice. Preserve contradictory statements and sources; do not silently overwrite.

## Acceptance checks for implementation

- A new user can identify what a star and its size represent.
- Capture yields one receipt linking two affected topics with preserved memory types.
- Pending/failed operations do not falsely increment saved counts.
- A later message enriches an existing topic without moving unrelated stars.
- Source inspection distinguishes generated overview, extracted memory, and original text.
- Answer claims trace to sources; proposals and questions are not presented as decisions.
- Topic-scoped Ask followed by a new question defaults to All topics.
- Asking does not add memories.
- Empty, disconnected, failed, answering, insufficient-evidence and sample-data states are legible.
- Search and list are keyboard-operable; all controls have labels and visible focus.
- Reduced motion preserves all information.
