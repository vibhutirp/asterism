# Observatory frontend constraints

- This is an exploration-only reader. Creation and conversational queries belong to Slack/connected services. Do not add web write or AI-query interactions.
- Preserve the separate Python app and the approved design documents in `../docs/design/observatory`.
- `design-system.md` and `tokens.json` are authoritative over generated image pixels. Keep Inter, dark solid reading surfaces, opaque map-label backings, luminous line icons, and a faint star-free background. The approved spatial-exploration.md supersedes old 2D, star-grid and reserved-column rules.
- API mode calls only the two topic GET endpoints. Never fall back to sample data after an API failure, infer connection state, or fabricate historical updates.
- Keep wire and display types separate. Missing original source text remains missing. Label source timestamps Received and the backend overview Topic description. Hide confidence/token fields.
- Keep 3D topic centers stable by ID and particles deterministic and counts derived from successful read responses. Disclosure preserves focus; inspector closure restores its invoker.
- At overview, aggregate category galaxies; zoom reveals topic clouds without changing canonical centers. The spatial specification permits seeded 8-second/10% breathing with Pause/Resume and reduced-motion/visibility suspension; it supersedes older no-looping rules.
- Before delivery run the focused tests, TypeScript check, production build, and inspect the browser. Record evidence and limitations in `design-qa.md`.
- Preserve template hosting support: `.openai/hosting.json`, `worker/index.js`, `scripts/prepare-sites-build.mjs`, `tests/sites-worker.test.mjs`.
