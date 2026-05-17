# Image Lab

A lightweight Replit-friendly image generation wrapper for experimenting with image APIs without turning the project into a full chat app.

This repo is intentionally separate from VeniceChat. The goal is a small, inspectable Flask app with a plain HTML/CSS/JavaScript frontend, provider adapters, local image saving, and a checklist-driven roadmap.

## Check Here First

### Current status

- [x] Created the starter repository structure.
- [x] Added a Flask backend skeleton.
- [x] Added a simple one-page browser UI.
- [x] Added provider adapters for Venice.ai and Fal.ai.
- [x] Added local image saving for base64 images and remote image URLs.
- [x] Added SQLite history for runs and generated images.
- [x] Added a basic async job system with polling.
- [x] Added `.env.example` for API keys.
- [x] Added Phase 2 gallery workflow basics: favorites, delete image/run, rerun, vary, load old run, download links, and metadata panels.
- [x] Added static model/pricing catalog with model notes and cost estimates.
- [x] Added live provider metadata/pricing refresh into `data/model_cache.json`.
- [ ] Test live model/pricing refresh in Replit with real API keys.
- [ ] Test Phase 2 actions in Replit with real generated images.
- [ ] Adjust model defaults after seeing which models you like best.

### Decisions already made

- Use Flask, not React.
- Use plain HTML/CSS/JavaScript.
- Keep the first version small and patchable.
- Store generated images locally so gallery history does not depend on temporary provider URLs.
- Use one normalized request shape internally, then translate it into provider-specific requests.
- Start with prompt-to-image only. Editing, upscaling, and background removal can come later.
- Do not optimize primarily for huge batches or ultra-fast iteration yet. The app should support batches, but the main priority is a clean wrapper and a good foundation.
- Keep local human-written model notes in `services/model_catalog.py`, and save live provider metadata/pricing in ignored runtime file `data/model_cache.json`.

### Decisions Josie may need to make later

- Whether this app should stay private or be deployed publicly.
- Which provider should be the default: Venice.ai or Fal.ai.
- Which models should appear at the top of the dropdown.
- Whether to track actual cost per completed generation in history.
- Whether to add prompt enhancement using a text model.
- Whether to support image editing/inpainting next, or model browser/cost analytics next.
- Whether to add a phone-friendly patch/fetch helper later, similar to VeniceChat, or keep this project simpler.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add API keys

Copy `.env.example` to `.env` for local development, or add these as Replit Secrets:

```text
VENICE_API_KEY=your_venice_key_here
FAL_KEY=your_fal_key_here
```

The app will start without keys, but provider calls and live model/pricing refresh will fail until the relevant key is present.

### 3. Run the app

```bash
python main.py
```

Then open the Replit web preview.

### 4. Refresh model/pricing data

In the app, click:

```text
Refresh model/pricing data
```

This calls:

```text
POST /api/models/refresh
```

The app saves live provider metadata/pricing to:

```text
data/model_cache.json
```

That file is ignored by Git because it is runtime/account-specific cache data.

## First test prompts

Try simple prompts first while testing the plumbing:

```text
A cozy little robot painting flowers in a sunlit greenhouse, warm soft light, charming, detailed
```

```text
A cinematic photo of a tiny dragon asleep on a stack of library books, shallow depth of field
```

For debugging, use one image at a time first. After a provider works, try 2 or 4 images.

## Roadmap

### Phase 1 — Working generator

- [x] Flask backend
- [x] Plain frontend
- [x] Provider selector
- [x] Model selector
- [x] Prompt and negative prompt fields
- [x] Image count field
- [x] Aspect ratio field
- [x] Seed field
- [x] SQLite run history
- [x] Local image saving
- [x] Confirmed by Josie: initial app is working in Replit
- [ ] Add clearer provider-specific error messages if either API returns validation errors

### Phase 2 — Better gallery workflow

- [x] Favorite images
- [x] Delete images/runs
- [x] Rerun a previous prompt
- [x] Vary a previous run by clearing the seed
- [x] Show image metadata in a collapsible panel
- [x] Show run settings in a collapsible panel
- [x] Load/copy a previous run back into the form
- [x] Download individual images
- [ ] Test all Phase 2 actions in Replit
- [ ] Batch-download a run as a ZIP

### Phase 3 — Model management

- [x] Static model catalog with provider-specific notes
- [x] Live Fal pricing refresh route
- [x] Live Venice image model metadata refresh route
- [x] Persistent runtime cache at `data/model_cache.json`
- [x] UI button for refreshing model/pricing data
- [x] Merge live cache into `/api/models`
- [ ] Fetch Venice image styles from the styles endpoint
- [ ] Add a proper model browser/table view
- [ ] Mark models with simple labels like fast, quality, edit, cheap, experimental
- [ ] Tune/hide models after real-world testing

### Phase 4 — Cost awareness

- [x] Show pre-generation cost estimate when pricing metadata is available
- [ ] Store estimated cost on each run
- [ ] Store actual cost when provider response exposes enough billing data
- [ ] Track total runs/spend by provider/model
- [ ] Add a simple monthly usage page

### Phase 5 — Editing and post-processing

- [ ] Add image upload
- [ ] Add image-to-image generation where supported
- [ ] Add inpainting/editing
- [ ] Add Venice upscale/enhance
- [ ] Add Venice background removal
- [ ] Add before/after comparison view

### Phase 6 — Prompt helper features

- [ ] Saved prompt snippets
- [ ] Style preset chips
- [ ] Prompt templates
- [ ] Optional prompt enhancer
- [ ] Prompt history search

### Phase 7 — Replit/mobile polish

- [ ] Improve iPhone layout
- [ ] Add loading/progress details
- [ ] Add keyboard shortcut for desktop generation
- [ ] Add better empty states
- [ ] Add app-level settings page
- [ ] Add backup/export for SQLite metadata

## Notes to self for future development

- Keep provider quirks in `providers/`, not spread through the UI.
- Keep generated files out of GitHub. `static/generated/` is ignored except for `.gitkeep`.
- Keep API keys server-side only.
- Prefer small exact patches over broad rewrites.
- Do not add chat/memory/summarization features unless there is a clear need.
- When provider validation fails, save the raw error text in the run record so it can be debugged later.
- Deleting images/runs removes the saved local generated file if it is under `static/generated/`.
- Do not commit `data/model_cache.json`; it is runtime/account-specific cache data.

## Known limitations of this starter version

- Fal model schemas vary. The current Fal adapter supports `image_size` and `aspect_ratio` payload styles, but some models may need special mapping.
- Venice model sizing rules vary. The current Venice adapter supports aspect ratio, width/height, seed, negative prompt, variants, format, and resolution tiers for cataloged resolution-tier models.
- Live pricing refresh depends on provider API keys and provider endpoint behavior. Some models may still return unknown/range pricing.
- Jobs are tracked in memory while running. Completed history is stored in SQLite, but if the server restarts mid-generation, the in-progress job status may be lost.
- There is no authentication. Keep the app private unless/until auth is added.
