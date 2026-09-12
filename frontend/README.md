# Observatory reader

A read-only React + TypeScript workspace for browsing topics, memories, and their sources. The existing Python application remains separate. There are no web capture, question, or knowledge-writing controls.

## Run locally

Requires Node 22.18+ (verified with Node 25.8.2).

```sh
cd frontend
npm ci
npm run dev -- --port 4173
```

Open http://localhost:4173. Default mode is **fixture**, visibly labeled **Sample data**. The demo contains **10 topics, 42 memories, and 30 original Slack messages from six fictional teammates**, across Product and Personal. All sources are labeled samples and have no invented external URLs. See [demo-data.md](demo-data.md) for the story and a short walkthrough.

## Select the data mode

Copy `.env.example` to `.env.local`, choose one mode, and restart Vite:

```dotenv
VITE_DATA_MODE=fixture
VITE_WORKSPACE_ID=demo
API_TARGET=http://127.0.0.1:8000
```

For the backend, set `VITE_DATA_MODE=api`. The Vite development proxy forwards relative `/api` requests to `API_TARGET`. The reader calls only:

- `GET /api/topics?workspaceId=demo`
- `GET /api/topics/{id}?workspaceId=demo`

API mode refreshes topics and the selected detail every ten seconds while visible, and when returning to the page. Superseded requests are aborted and guarded by a generation check. Failed reads remain visible; previously loaded data remains available with a stale-data notice. API errors never activate fixtures. Production hosting must supply its own same-origin `/api` routing; the Vite proxy is development-only. Deployment is not included in this slice.

`models.ts` separates wire types from display models; `repository.ts` is the read boundary. The backend's `overview` is labeled **Topic description**. `fact` is displayed as **Statement**, while other memory types retain their meaning. Confidence and token counts are omitted. **Received** means ingestion time. Original text, author, and channel are optional and currently absent from the backend response; the UI explicitly says **Original text unavailable**. A memory extraction is never substituted for an original quote.

API update notices use only changes observed during the current session. No historical activity or Slack connection/ingestion state is inferred. Same-count content edits cannot be detected in the list response unless the description/name also changes; selected details still refresh.

## Verification

```sh
npm test
npm run typecheck
npm run build
npm run test:sites
```

Focused tests cover name filtering, adaptation and missing provenance, source URLs, stable ID slots, observed updates, superseded responses, and read-only API calls. See `design-qa.md` and `qa/` for browser evidence.

Development-only fixture URLs support repeatable QA without adding demo controls to the normal interface:

| URL parameter | State |
| --- | --- |
| `?fixture=empty` | Empty saved universe |
| `?fixture=loading` | Delayed initial read |
| `?fixture=error` | Failed topic read |
| `?fixture=stale` | Initial success, subsequent read failures |
| `?fixture=detail-error` | Topic loads; detail fails |
| `?fixture=missing-source` | Original text/author/channel unavailable |
| `?fixture=long` | Long topic name and complete long source |
| `?fixture=crowded` | 50 topics and map overflow |

These parameters are ignored in API mode and production builds. They do not write data. Refreshing returns fixture state to its initial value.

## Design

Authoritative values: `../docs/design/observatory/design-system.md` and `tokens.json`. `src/tokens.css` translates the shared values. The layout uses stable 3D topic clouds and a floating inspector. See `../docs/design/observatory/spatial-exploration.md` for camera and particle semantics. List is the initial compact view below 1024px. Readable labels, solid focus outlines, native buttons, and reduced-motion overrides remain independent of glow.

`public/assets/nebula.png` was generated as reusable artwork without point stars and is now a faint background. Topic clouds are separate WebGL geometry with accessible HTML labels. Generation prompt: “Reusable astronomical knowledge-map background; midnight #080D19, diffuse blue-violet nebula upper half, soft sage-teal wisps lower-left; restrained luminance, deep navy negative space; atmospheric clouds only. No stars, dots, speckles, planets, flares, crosses, constellations, text, panels, UI, logos, or watermark.”

Template hosting support files are preserved. No deployment or real Slack ingestion was performed as part of this frontend implementation.

## 3D exploration revision

Drag to orbit; Shift/right-drag to pan; scroll/pinch to zoom. Selecting a cloud frames it beside the floating inspector. Closing preserves the camera. Reset view frames all topics without clearing filters or selection. Points are visual texture, not individual memory records.

Three.js and React Three Fiber 9 render on demand with a 64,000-point budget. The WebGL scene is lazy-loaded; the build reports a large 3D chunk (about 251 KB gzip). If WebGL fails, the app shows an explanation and switches to List.

Development-only fixture checks: `?motion=reduce` forces immediate camera transitions; `?scene=context-loss` loses the WebGL context after initialization to verify List recovery. These are disabled in production and API mode. Updated evidence is in `qa/3d/`; the current report is `design-qa-3d.md`.

## Galaxy overview and animation

The widest view combines Product and Personal into galaxy clouds with exact category totals and world-anchored colored atmospheres. Select a galaxy to approach its topics, then select a topic to inspect memories. Search keeps the camera fixed and labels category totals separately from matching topics. Reset returns to the overview while retaining search and selection.

Glow dims by at most 10% on an eight-second cycle, scheduled up to 30fps only while Universe is visible. Pause animation stops this decorative cycle; List, hidden tabs and reduced motion also suspend it. Geometry and labels remain stationary except during navigation and aggregation transitions. No new API calls or dependencies are introduced.

Current visual evidence and coverage: [Galaxy QA](design-qa-galaxies.md).

## Compact exploration controls

The Universe/List switch is centered above the scene; search is centered below and expands on focus. Both shift into the space beside the open inspector. Camera controls are compact bottom-left icons with tooltips. Help contains gestures and keyboard shortcuts; Recent updates opens from the header. Escape in search clears, then collapses without closing the inspector. Compact List places search above the rows.

Current layout evidence and verification: [Compact controls QA](design-qa-controls.md).
