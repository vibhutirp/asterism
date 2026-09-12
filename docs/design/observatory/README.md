# Observatory — exploration-only web application

## Confirmed scope

The web frontend only browses topics, memories, and original sources. Memories enter exclusively through Slack and connected services. There is no web Capture, fallback input, Ask interface, or ability to create, edit, delete, reclassify, merge, retry ingestion, seed, or reset stored knowledge.

This supersedes the previous Capture and grounded-answer designs. External conversational ingestion/retrieval and the shared HTTP API remain separate backend concerns; this change does not remove or redesign those services.

Status: approved Observatory visual direction; updated exploration-only concept prepared. These are static design artifacts. Application code is unchanged.

Current references:
- design-system.md: design-system specification, spacing, Gestalt, layout, and component rules.
- tokens.json: portable design values; no application implementation.
- contrast-report.md: calculations for declared solid color pairings.
- design-system.png: illustrative system board; exact values come from the specification.
- exploration-only.png: authoritative main-screen concept.
- generation-prompts.md: exact built-in image-generation prompt.
- superseded/: historical designs and prior handoff. Their Capture/Ask/save/demo controls are obsolete and must not be implemented.

## Workspace and controls

One desktop workspace with a full-width 3D scene, floating Universe/List controls, and a contextual inspector floating 24px from the right edge. See [the current spatial specification](spatial-exploration.md).

Universe means all workspace knowledge; galaxies are predefined categories with ordinary labels such as Product and Personal. Each particle cloud is one stable topic; particles are visual texture, not individual memories. Topics include project identity in their names and contain typed memories with provenance.

The review journey is: notice an update or filter topic names → select a topic → read overview and memories → inspect an original message → optionally open a real source link.

| Control | Read-only behavior |
|---|---|
| Find topics by name | Case-insensitive filtering of existing topic names in both views; no semantic/full-text or AI-query claim. |
| Universe / List | Changes representation of the same topic set, retaining query and selection. |
| Topic star, list row, View topic | Opens that topic's inspector by stable topic ID. |
| Close inspector / Escape | Clears selection, closes content, restores focus to the invoking element. |
| View original / Hide original | Expands/collapses original source inline without losing the memory. |
| Open in Slack or another source | Appears only with a genuine source URL; no fabricated sample links. |
| Sample data / connection status | Informational labels, not buttons. |

List rows show name, category, count, and update state. No-match says "No topics match this name"; clearing the query restores the set. With no selection, the inspector area says "Select a topic to explore its memories."

## Galaxy and luminous style

Fully dark navy space; diffuse blue-violet Product and sage Personal nebulae; luminous topic stars; crisp pale line icons; violet interaction edges; sharp readable text on a dark inspector.

Each cloud represents an actual topic. Orbit, pan and zoom explore its volume; selection focuses the camera and opens the floating inspector. No connectors, invented relationships, or graph editing. Topic centers remain stable when an existing topic gains a memory. The older exploration-only.png is retained as historical 2D artwork; the approved 3D interaction model now takes precedence.

Star core size represents persisted, deduplicated memory count only. Bound the size range and show exact counts. Selection adds a ring and label emphasis without changing core size. Brightness never indicates truth, confidence, importance, or retrieval rank.

Use a consistent icon family with soft localized halos on Search, Universe/List, source disclosures, View topic, and Close. Rest is subtle; hover brightens an edge; pressed tightens the light. Keyboard focus uses a crisp 2px offset outline. Disabled controls have no glow. Target approximately 150ms transitions; reduced motion keeps static equivalents. No pulsing stars or moving nebulae.

Keep body/source text unglowing: target 16px body and 14px controls with readable metadata. Verify contrast, focus, and hit targets in implementation; generated images do not establish accessibility compliance.

## Inspector and trust

Show topic name, category, count, actual contributing source identities, latest update, AI overview, typed memories, and original messages. At topic level, "From Slack" applies only when all contributions come from Slack. List actual services for mixed-source topics.

Label the generated summary "AI overview." If absent, show "Overview unavailable" and keep memories readable; no Generate action.

Preserve Idea, Decision, Question, and Statement meanings. A question is not a fact and a proposal is not approval. Keep conflicting statements with their sources rather than overwriting them or introducing manual conflict resolution.

Original source includes complete text, author/source identity, channel when available, timestamp, and optional genuine URL. One multi-topic message may support several memories; expansion still shows the complete original. Extracted memory and source quotation remain distinct.

## Essential read-only states

Recent updates reports source-service ingestion and links affected topics. It does not accept text or retry ingestion. New/Updated labels are read-only indicators; do not require server-side read-receipt writes.

| State | Behavior |
|---|---|
| Empty universe | "No memories yet. Memories appear here after conversations are saved through Slack or a connected service." No web fallback. |
| Sample data | Persistent Sample data badge and sample source labels. Seed/replay/reset stay in external developer/demo tooling. |
| Received / organizing | Show source identity and status only if the service supplies them. Keep stored counts/content unchanged until persistence succeeds. |
| Saved / updated | Read persisted results, preserve positions, identify New/Updated, and link the topic. |
| Extraction failed | Report failure if available. No fake saved counts or web Retry action; recovery is external. |
| Slack disconnected | Retain stored knowledge and show truthful connection state. No "web capture available" or setup button. |
| Knowledge loading | Show loading rather than briefly presenting an empty universe. |
| Read request failed | Explain the load failure. A Try again action may repeat the read only, never re-ingest. Preserve available content with a stale-data notice. |
| Topic selected / source expanded | Preserve overview/memory/source hierarchy and keyboard focus. |

Sample / Live / Replay describe origin independently of processing status. Unknown status stays unknown rather than claiming live connectivity.

There are no web answering, context-budget, answer-citation, or insufficient-retrieval-evidence states. Source provenance for stored memories remains essential.

## Canonical Slack demo

Timestamps below are fictional sample data on September 12, 2026, in the displayed workspace timezone.

1. Alex, Slack #product, 2:10 PM:
   "Idea for Atlas onboarding: try a three-step setup checklist. Separately, for the camping trip, could we borrow Maya’s tent?"
   Persist one onboarding Idea and one Camping trip Question: two topics, two memories. Both source disclosures show the same complete original.

2. Alex, Slack #product, 2:12 PM:
   "For Atlas pricing, an idea is to test a $12 monthly plan."
   Persist one pricing Idea: three topics, three memories.

3. Alex, Slack #product, 2:14 PM:
   "For Atlas onboarding, we decided to pilot the three-step checklist with five new users."
   Enrich existing onboarding with one Decision: three topics, four memories total. Onboarding has two; pricing and camping have one each. Do not reposition existing stars.

4. In the web app, follow Atlas onboarding updated / 1 new memory saved. Read the overview and Idea/Decision, expand the decision's original source, and verify author, channel, timestamp, and quotation. Open in Slack only if a live run supplies a real link.

The screen intentionally shows sample data with Slack disconnected. It demonstrates previously stored knowledge, not current ingestion through a disconnected service.

## Frontend/backend boundary

Read existing categories/topics/memories, persisted counts, typed text, overview if available, provenance, real timestamps/links, and available source/ingestion status. Keep filtering and selection local.

No new web write path, extraction path, or answer endpoint is required. Do not expose existing write endpoints through web controls. No backend redesign, event bus, extra provider integration, or automatic conflict detection is implied. Use available read/status refresh mechanisms rather than fabricating live updates.

The overall backend's HTTP API and external conversational retrieval remain outside this web slice. Manual correction, merge/split, graph editing, permissions, account setup, and integration management remain out of scope.

## Acceptance checks

- Users identify a cloud as a topic, read its exact count, and understand that its dots are visual texture.
- Web controls only navigate/filter/read; users cannot add memories or submit AI questions.
- Source ingestion can produce memories across topics, and later enrich an existing topic without moving others.
- Pending/failed ingestion never falsely increments saved counts.
- Name search and List navigate real topics; no-match, empty, loading, and failure remain distinct.
- Users can inspect full original text, identity, timestamp, and a source link only when real.
- Idea, Question, Decision, AI overview, and original quotation are distinguishable.
- Disconnection leaves stored knowledge readable and provides no web-capture fallback.
- Sample/Live/Replay and status labels are honest; no demo mutation controls exist.
- Focus survives view changes and inspector closure; reduced motion preserves information.
- Browser actions perform reads/local navigation only; ingestion/retry stays external.
