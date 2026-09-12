# Demo workspace

The default fixture mode loads a fictional Atlas team snapshot dated September 12, 2026. No backend connection or import is needed. Start with `npm run dev -- --port 4173` and open http://localhost:4173. If a local environment already selects API mode, use `VITE_DATA_MODE=fixture npm run dev -- --port 4173`.

The dataset is in `src/fixtures.ts`: 10 topics, 42 extracted memories, 30 distinct Slack messages, and six fictional teammates. Topic counts come from the memory arrays. Dates and IDs are fixed so refreshing gives a repeatable demo. All names, messages, research results, prices, and plans are fictional examples. The overview copy is authored fixture content, not a live model response.

| Topic | Category | Memories | Story |
| --- | --- | ---: | --- |
| Atlas onboarding | Product | 8 | Checklist idea → pilot → evidence → limited rollout |
| Atlas pricing | Product | 6 | Per-user proposal → interview feedback → comparison experiment |
| Camping trip | Personal | 4 | Tent question → confirmed loan; campsite and rain plan unresolved |
| Customer discovery | Product | 5 | Recruiting → six interviews → qualitative findings |
| Preview launch | Product | 4 | Conditional date, scoped preview, readiness, walkthrough |
| Topic search | Product | 4 | Usability confusion → explicit name filter; aliases unresolved |
| Source traceability | Product | 3 | Missing originals, trustworthy links, open access question |
| Team dinner | Personal | 3 | Preferences and budget; reservation unconfirmed |
| Running club | Personal | 3 | Inclusive proposal → scheduled run; finish time unresolved |
| Book club | Personal | 2 | Reading proposal → confirmed lunchtime discussion |

## Three-minute walkthrough

1. Start in Universe. Point out the Product and Personal groups, differing memory counts, and Sample data label. The map deliberately limits visible topics to fit the viewport; use **View all topics** or **List** for all ten.
2. Open **Atlas onboarding**. Expand the first **View original**: Alex’s complete message includes both the checklist idea and the camping question. Scroll through the pilot result and the later decision to retain a limited rollout. Small-sample findings stay qualified in the original.
3. Open **Atlas pricing**. Compare the initial $12-per-user idea with the later decision to interview users about a $99 workspace alternative. Explain that a proposal is distinguishable from an approved change; billing has not changed.
4. Open **Camping trip**. Expand its first original to show the same message, author, channel, and received time as the onboarding idea. The next memory confirms Maya’s tent loan while other logistics remain unresolved.
5. Switch to **List**, search `launch`, and open **Preview launch** to show owners, dates, and outstanding readiness work. Clear the search to restore all ten topics.

Use the existing development-only `?fixture=missing-source`, `?fixture=long`, `?fixture=empty`, or `?fixture=error` URLs for alternate states. The crowded scenario adds 40 QA topics for a total of 50. API mode never uses these fixtures as an error fallback.

Recent updates are explicitly labeled sample events and reset on reload; they are not live ingestion. Source times mean Received. Original messages remain complete, and no fictional Slack links are generated.
