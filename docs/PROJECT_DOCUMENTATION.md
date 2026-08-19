# CAD-AID — Project Documentation

**Repository:** `kartAI/CAD-AID`
**Reviewed:** 2026-08-16 (main @ `439d557`, plus all 18 remote branches)

This document is a full walkthrough of the CAD-AID repository: what the project does, how the code on `main` is architected, the ML/data pipeline behind it, and what every side branch in the repo was exploring. It was produced by reading the actual source on `main` and diffing/inspecting all branches — not from the READMEs alone (the top-level `README.md` is a two-line Docker run snippet and does not describe the project).

---

## 1. What is CAD-AID?

CAD-AID is an AI system that classifies and interprets **CAD drawings ("byggetegninger")** submitted as part of Norwegian **building-permit applications ("byggesak")**. It is a Norkart / kartAI project. Its lineage traces back to a UiA (University of Agder) internship project (branch `objectdetection-text`, see §6.3) that used real drawings from Kristiansand kommune's public building-case archive.

Given a scanned/exported PDF or image of a submitted drawing page, the system:

1. **Classifies the drawing type** using a YOLOv8 object-detection model into one of four Norwegian categories:
   - `fasade` — facade/elevation drawing
   - `plantegning` — floor plan
   - `situasjonskart` — site/situation map
   - `snitt` — section/cross-section drawing
2. **Extracts type-specific required metadata** via OCR (EasyOCR or Tesseract, Norwegian language model) + regex + geometry, branching on the detected type:
   - `fasade` → cardinal direction ("himmelretning") and scale
   - `snitt` / `situasjonskart` → scale, nearest to the detected drawing region
   - `plantegning` → room names ("rom"), cross-checked against a second YOLOv8 **segmentation** model that outlines individual room polygons, plus a room count
3. Surfaces the results in a **Vue.js web app** where a caseworker can review the drawing, see what was detected (with bounding-box highlighting), and give Yes/No **feedback** on whether each extracted field is correct — closing the loop for future model improvement.

The underlying idea (explicit in the original prototype's README): a caseworker should be able to quickly verify that a submitted drawing set contains all legally-required information (room labels, scale, compass orientation, etc.) without manually reading every page.

---

## 2. Repository layout (`main`)

```
CAD-AID/
├── cadaid_api/              # The deployed application (backend microservices + Vue frontend)
│   ├── detect/               # Detection microservice (FastAPI, port 8000)
│   ├── feedback/              # Feedback microservice (FastAPI, port 8001)
│   ├── performance/            # Offline evaluation harness (FastAPI, port 8002, dev-only)
│   ├── shared/                # Common library: config, auth, ML wrappers, OCR/regex, models
│   ├── nginx/                  # Reverse proxy in front of detect + feedback
│   ├── frontend/               # Vue 3 + Vite single-page app
│   ├── deploy/                  # Azure Container Instances (ACI) deployment templates
│   ├── training/                # Lightweight local retraining scripts (API-context)
│   ├── upload_files/             # Runtime volume: uploaded drawings awaiting processing
│   ├── metadata_files_store/      # Runtime volume: detection + feedback JSON output
│   ├── docker-compose.yml         # Production compose (detect + feedback + nginx)
│   ├── docker-compose.dev.yml      # Dev compose (detect + feedback + performance, no nginx)
│   └── Dockerfile.dev               # Shared dev image for all three services
├── training/                 # Production Azure ML training pipeline (offline, MLOps)
│   └── dataPrep/               # PDF→JPG conversion, dataset train/test/val splitting
├── azure/                    # Azure ML model registration / AKS compute / endpoint deployment
├── data/                     # Object-detection dataset (4 drawing-type classes)
├── data_seg/                 # Segmentation dataset (1 class: "rom"/room)
├── models/                   # Root-level trained YOLO checkpoints (runs/detect, runs/segment)
├── models_to_register/       # Staging dir for Azure ML model registration
├── utils/                    # Root-level inference helpers (mirrors cadaid_api/shared/utils)
├── .env.dev                  # Root dev/example environment file (model paths, Azure config)
└── README.md                 # Minimal: Docker run instructions only
```

`cadaid_api/` and the root-level `training/`/`azure/`/`data*/` directories represent two halves of one system: the **runtime application** (microservices + frontend, deployed to Azure Container Instances) and the **offline MLOps pipeline** (Azure ML training/registration/deployment for the YOLO models that the runtime application loads).

---

## 3. Backend architecture (`cadaid_api/`)

`cadaid_api/` is a microservice-based **FastAPI** backend, containerized with Docker and fronted by **nginx** as a reverse proxy. Three Python services (`detect`, `feedback`, `performance`) share a common `shared/` package for config, auth scaffolding, ML model wrappers, and OCR/text-processing utilities.

```
                         ┌──────────────────────────────┐
   Vue frontend  ───────▶│   nginx  (port 80)            │
   (localhost)           │   / → redirect /detect/docs/  │
                          │   /detect/   → detect:8000    │
                          │   /feedback/ → feedback:8001  │
                          └───────────┬───────────┬───────┘
                                      │           │
                         ┌────────────▼──┐   ┌────▼──────────┐
                         │ detect (8000) │◀──│ feedback(8001) │
                         │ YOLO detect + │   │ GET detect's   │
                         │ YOLO segment +│   │ /detection-    │
                         │ OCR + regex   │   │ results, store │
                         └───────┬───────┘   │ feedback JSON  │
                                 │            └────────────────┘
                     shared Docker volumes:
                     /app/upload_files, /app/metadata_files_store
```

`performance` (port 8002) is a separate offline evaluation service, not part of this request path (see §3.4).

### 3.1 `shared/` — common library

Imported by all three services (`PYTHONPATH=/app:/app/shared`).

- **`shared/config.py`** — loads `.env.dev` (python-dotenv) into a `Config` object: model paths/names/versions/confidence for both YOLO models, plus `OCR_MODEL`.
- **`shared/auth.py`** — JWT (`python-jose`) + static API-key scaffolding: `get_api_key()` (FastAPI `Security` dependency checking an `X-API-KEY` header) and `verify_api_key()` (JWT decode). **Not currently enforced** — see §3.7.
- **`shared/utils/models_manager.py`** — `ModelsManager` base class wrapping an `ultralytics.YOLO` model; subclassed as `ObjectDetection` and `Segmentation`, configured from `Config`.
- **`shared/utils/object_detection.py`** — `ObjectDetectionHandler.run_detection()` runs the detection model and extracts `(drawing_types, bboxes, confidences)`.
- **`shared/utils/segmentation_handler.py`** — `SegmentationHandler.run_segmentation()` runs the room-segmentation model.
- **`shared/utils/text_detection.py`** — `TextDetection` wraps EasyOCR (`easyocr.Reader(['no'])`) and pytesseract (`lang='nor'`); `TextProximityFilter` provides geometry helpers built on Shapely: point-in-polygon matching of OCR text to segmentation masks (room-name matching), text-within-bbox filtering, and nearest-text-to-object distance (scale/cardinal-direction matching).
- **`shared/utils/regex_patterns.py`** — Norwegian-language regexes: scale (`\d+\s*:\s*\d+`), cardinal direction (nord/sør/øst/vest combinations), room names (soverom, bad, kjøkken, stue, gang, bod, …), gnr/bnr cadastral parcel numbers, area (m²).
- **`shared/utils/data_structures.py`** — dataclasses `TextInfo`, `DrawingInstance` (drawing_type, bbox, confidence, cardinal_direction, scale, room_names, num_of_rooms, gnr_bnr), `Metadata` (filename + detections), `DrawingType` enum, `FeedbackData`.
- **`shared/utils/logger.py`** — shared file+console logger (`/app/logs/app.log`).
- **`shared/models/`** — the actual deployed weights: `detection_model/best.pt` (~22.5MB, 4 classes) and `segmentation_model/best.pt` (~24MB, 1 class `rom`), loaded directly by `ultralytics.YOLO()` at container startup — no live Azure ML inference call in the request path.

### 3.2 `detect/` — detection service (port 8000)

The primary inference service, mounted at `root_path="/detect"`. CORS is wide open (`allow_origins=["*"]`).

| Method | Path (external, via nginx) | Purpose |
|---|---|---|
| `POST` | `/detect/` | Upload 1+ files (PDF/JPG/PNG); runs the full detection pipeline |
| `GET` | `/detect/detection-results` | Returns in-process accumulated metadata dict (`{filename: detection}`) — called cross-container by `feedback` |
| `GET` | `/detect/health` | Liveness/readiness probe |
| `GET` | `/detect/logs/` | Dumps `app.log` as JSON |

**Pipeline** (`DetectionService.run_detection_pipeline`, per uploaded file):
1. PDF → rasterized per page via `pdf2image`; JPG/PNG → read directly via OpenCV.
2. `ObjectDetectionHandler.run_detection()` → YOLO drawing-type classification.
3. Per detected box, OCR (`TextDetection`) runs over the whole image; branch by type:
   - `fasade` → all cardinal-direction and scale regex matches in the image (no proximity filtering).
   - `snitt` / `situasjonskart` → scale text nearest the detected bbox.
   - `plantegning` → OCR text filtered by room-name regex, `SegmentationHandler` run for room polygons, text kept only if it falls inside a room polygon *and* inside the plantegning's own bbox; room count = number of segmentation masks.
4. Results written to `/app/metadata_files_store/detection_results.json` (global file, **overwritten each request** — not per-session) and kept in an in-process `metadata` dict.

### 3.3 `feedback/` — feedback service (port 8001)

Mounted at `root_path="/feedback"`. `POST /feedback/` accepts `filename` + `user_response: bool` (form fields):
1. Calls `GET http://detect:8000/detection-results` (hardcoded Docker service name, not env-configurable) to fetch that file's detection metadata.
2. Writes `{filename}_feedback_metadata.json` into a per-file folder under `metadata_files_store/`.
3. Moves the original uploaded image from `upload_files/` into the feedback folder (this is where upload cleanup actually happens).

`GET /feedback/health` has a copy-paste bug — its JSON body reports `"service": "detect"`.

### 3.4 `performance/` — offline evaluation harness (port 8002, dev-only)

Not part of production `docker-compose.yml`, the ACI deploy YAML, or nginx routing — only present in `docker-compose.dev.yml`. Directly imports `DetectionService` from the `detect` module (not an HTTP call) and runs it over a fixed set of sample images under `performance/performance_data/images/`, scoring against `ground_truth.json`:

- `objdet_accuracy` — exact drawing-type match
- Plantegning: room-count accuracy, fuzzy-string room-name accuracy (`difflib.SequenceMatcher.ratio() > 0.8`)
- Fasade: cardinal-direction accuracy, scale accuracy
- **Incomplete**: `SnittMetrics`/`SituasjonskartMetrics` Pydantic models exist but `evaluate_image()` never populates them; `valid_cardinal_directions.json` is empty.

### 3.5 `nginx/` — reverse proxy

Single server on port 80: `/detect/` → `detect:8000`, `/feedback/` → `feedback:8001`, `/` → 301 redirect to `/detect/docs/` (Swagger UI as the landing page). Security headers set (`X-Frame-Options`, `X-Content-Type-Options`, HSTS). 300s timeouts to accommodate slow OCR/YOLO inference. No `/performance/` route (consistent with it being dev-only).

### 3.6 Deployment

- **`docker-compose.yml`** (production): `detect` + `feedback` + `nginx`, ports 8000/8001/80, bridge network, healthchecks present but commented out.
- **`docker-compose.dev.yml`**: `detect` + `feedback` + `performance` (no nginx — each service exposed directly for local debugging), all built from the shared `Dockerfile.dev`.
- **`deploy/aci_deploy.yaml`**: Azure Container Instances multi-container group template (region `westeurope`), 3 containers pulling from `cadaidregistry.azurecr.io`, liveness/readiness probes hitting `/health`, `STATIC_API_KEY` templated as `secureValue`, single public IP with DNS label `cadaid-api`.
- **`deploy/deploy.ps1`**: PowerShell wrapper that substitutes the API key into the template and calls `az container create`.
- Root **`azure/`**: a *separate*, offline model-lifecycle pipeline — `register_model.py` registers `models_to_register/*` into the Azure ML model registry; `create_aks_compute.py` attaches an AKS compute target; `deploy_model.py` stands up an Azure ML **Managed Online Endpoint** on AKS; `test_endpoint.py` smoke-tests it. This AML-endpoint path (`.../analyze`) appears to be an **alternate/experimental inference deployment**, separate from and not called by the actual running `detect` FastAPI service.

### 3.7 Cross-cutting issues worth knowing about

- **Auth is effectively disabled.** `get_api_key`/JWT verification exists in `shared/auth.py` and is wired into the ACI deploy template (`STATIC_API_KEY`), but every route's `Depends(get_api_key)` is commented out in the actual service code. Combined with `allow_origins=["*"]`, all endpoints are currently open.
- **A real secret is committed to the repo.** `cadaid_api/deploy/aci_deploy_processed.yaml` (lines 18 and 30) contains a plaintext `STATIC_API_KEY` value, not a placeholder. This looks like a generated artifact of `deploy.ps1` that should have been gitignored. **Recommend rotating this key and removing the file from git tracking (and history).**
- **Service coupling is hardcoded.** `feedback` calls `http://detect:8000/...` directly (Docker service-name DNS), not configurable via env var.
- **State is filesystem/in-process, not a database.** `detect`'s `metadata` dict is per-process and lost on restart; `detection_results.json` is a single global file overwritten on every request (race risk under concurrent uploads).
- **Two parallel inference paths exist**: the containerized `detect` FastAPI service (the one actually serving traffic) and an independent Azure ML managed endpoint (`azure/deploy_model.py` → `/analyze`) that doesn't appear to be integrated with the running system.

---

## 4. Frontend (`cadaid_api/frontend/`)

**Stack:** Vue 3.5 (`<script setup>` style) + Vite 5.4, `vue-router` 4 (HTML5 history), no state-management library (component-local state + `sessionStorage` as a page-to-page data bridge), no UI framework (hand-styled, Google Fonts + Font Awesome CDN), plain `fetch` for HTTP (no axios).

### Routes

| Path | View | Purpose |
|---|---|---|
| `/` | `HomeView.vue` | Norwegian marketing landing page, CTA → `/upload` |
| `/upload` | `UploadView.vue` | Drag-and-drop / file-picker upload, live per-file progress |
| `/results` | `ResultsView.vue` | Largest view (~1750 lines) — drawing viewer + detected fields + Yes/No feedback |
| `/feedback` | `FeedbackView.vue` | **Dead route** — a star-rating feedback form never linked to from the app, with a payload shape that doesn't even match the backend's `/feedback/` contract |
| `/success` | `SuccessView.vue` | Confirmation screen after the last file's feedback is submitted |

### User flow

1. **Home** → "Prøv CAD-AID her" → **Upload**.
2. **Upload**: each dropped/selected file is immediately `POST`ed to `/detect/` (field `uploaded_files`) while a simulated progress bar plays; on completion the result is stored per-file. "Fortsett til resultater" stashes everything into `sessionStorage.uploadedFiles` and navigates to **Results**.
3. **Results**: for each file — a zoomable/pannable/fullscreen image viewer (`FileViewer.vue`) plus panels showing detected drawing type(s), room names, and other extracted fields (cardinal direction, scale, gnr/bnr). Hovering a detected item highlights its bounding box on the drawing. The user answers Yes/No for each item; when a file's feedback is complete, `POST /feedback/` is called with `{filename, user_response}` — where `user_response` is a **single aggregate boolean** (`true` if *any* per-item answer was "yes"), so the granular per-field feedback the UI collects is not actually sent to the backend individually.
4. After the last file, routes to **Success** → "Tilbake til start" → **Home**.

### Notable dead code / rough edges

- `FeedbackView.vue` and its `/feedback` route are unreachable.
- `components/common/ProgressBar.vue` and `components/upload/FileUploader.vue` are defined but unused — each view reimplements the same UI inline instead.
- `src/utils/fileHelpers.js` is an empty stub.
- `ResultsView.vue` has significant duplicated CSS blocks.
- The API base URL is hardcoded as `const API_URL = 'http://localhost'` in `src/services/api.js` — no environment-based override for staging/production.

---

## 5. Machine-learning & data pipeline

### 5.1 The two models

1. **Object detection** (drawing-type classification) — YOLOv8, 4 classes: `fasade`, `plantegning`, `situasjonskart`, `snitt` (`data/data.yaml`).
2. **Segmentation** (room outlining within floor plans) — YOLOv8-seg, 1 class: `rom` (`data_seg/data_seg.yaml`).

Both are fine-tuned iteratively — each new training run in `training/train_yolo.py` warm-starts from the currently-registered Azure ML model version rather than training from scratch. Currently deployed checkpoints: `models/runs/detect/nora/train6/weights/best.pt` and `models/runs/segment/train8/weights/best.pt` (mirrored into `cadaid_api/shared/models/`).

### 5.2 Dataset

Images in both datasets are real Norwegian building-permit drawing pages (filenames are street addresses / gnr-bnr cadastral IDs / PDF page names), produced by rasterizing submitted PDFs via `training/dataPrep/convertFromPDF.py`. Counts below were computed directly from the label files (not just image counts).

#### `data/` — object detection (drawing-type classification), 513 MB on disk

Per-class instance counts (one label line = one bounding box):

| Class | train | test | val | **Total instances** | **Share** |
|---|--:|--:|--:|--:|--:|
| `fasade` (facade/elevation) | 546 | 57 | 77 | **680** | 42.3% |
| `plantegning` (floor plan) | 332 | 45 | 57 | **434** | 27.0% |
| `snitt` (section) | 248 | 19 | 32 | **299** | 18.6% |
| `situasjonskart` (site map) | 154 | 19 | 22 | **195** | 12.1% |
| **All classes** | **1,280** | **140** | **188** | **1,608** | 100% |

Split-level file stats:

| Split | Images | Label files | Instances | Images w/ empty label (background) | Images w/ no label file |
|---|--:|--:|--:|--:|--:|
| train | 911 | 906 | 1,280 | 120 | 5 |
| test | 107 | 106 | 140 | 21 | 1 |
| val | 116 | 116 | 188 | 13 | 0 |
| **Total** | **1,134** | **1,128** | **1,608** | **154** | **6** |

- Class balance is uneven — `fasade` outnumbers `situasjonskart` by ~3.5×, making situasjonskart the weakest-represented class.
- ~14% of label files (154) are present but empty, presumably negative/background examples rather than missing annotations.
- **Labeling bug found**: `data/train/labels/gnr-bnr53-354_fasade_sør_page_1.txt` has a class token of `w0` instead of a numeric class id — unparseable by strict `int()` loaders and likely silently dropped by Ultralytics' loader. Needs a manual fix.

#### `data_seg/` — segmentation (room outlines within floor plans), 237 MB on disk

1 class (`rom`), polygon-format labels (one line per room instance), presumably a re-annotated subset of the `plantegning` images from `data/`.

| Split | Images | Label files | Room instances | Avg rooms / labeled image | Images w/ no label file |
|---|--:|--:|--:|--:|--:|
| train | 355 | 354 | 1,651 | 4.7 | 0 |
| test | 110 | 1 | 5 | 5.0 | **109** |
| val | 48 | 48 | 233 | 4.9 | 0 |
| **Total** | **513** | **403** | **1,889** | **4.7** | **109** |

- The segmentation **test split is essentially unlabeled** — 109 of its 110 images have no label file at all, confirming it functions as a qualitative/visual holdout rather than a scored eval set.
- Average room count per labeled floor plan is consistent across train/val (~4.7–4.9 rooms/image), a reasonable signal of consistent labeling.

### 5.3 Data preparation (`training/dataPrep/`)

- **`convertFromPDF.py`** — rasterizes submitted PDFs to `<name>_page_<n>.jpg` via `pdf2image`/poppler, then deletes the source PDF.
- **`new_folder_split.py`** — randomly splits newly labeled images (80/10/10) into `data/train|test|val`, moving both image and label.

### 5.4 Training & MLOps pipeline (root `training/` + `azure/`)

End-to-end Azure ML flow:

```
Raw PDFs → convertFromPDF.py → JPGs → labelImg annotation → data/ + data_seg/
   → new_folder_split.py (80/10/10 split)
   → upload_data.py → Azure ML datastore ("detection_data", "segmentation_data")
   → register_env.py + Dockerfile → Azure ML Environment (ACR image yolov8-training:latest)
   → submit_training_job.py + yolo_training_job.yml → Azure ML job on compute "cadaidcompute"
        runs train_yolo.py: fine-tunes both YOLOv8 models from the previously-registered checkpoint
   → new best.pt → models_to_register/{detection_model,segmentation_model}/ (staging)
   → azure/register_model.py → Azure ML Model Registry (versioned)
   → azure/create_aks_compute.py + azure/deploy_model.py → AKS Managed Online Endpoint
   → azure/test_endpoint.py → HTTP smoke test (POST .../analyze)
```

`cadaid_api/training/train_object_detection.py` / `train_segmentation.py` are a **separate, simpler pair of scripts** — local retraining against local paths, no Azure ML orchestration, one model per script — apparently a lighter-weight "retrain within the API app" utility distinct from the production Azure ML pipeline above.

### 5.5 Root `utils/` (inference-time logic, mirrors `cadaid_api/shared/utils/`)

Same responsibilities as the backend's `shared/utils/` package described in §3.1 (regex patterns, OCR wrapping, detection/segmentation handlers, plotting helpers for visualizing detections and OCR bounding boxes) — this root copy is the pre-microservice-split / dataset-adjacent version used by the training and evaluation scripts at the repo root.

---

## 6. Branches — side projects & experiments

The project explicitly uses branches for side experiments. All 18 non-`main` branches were inspected (diffed and read against `origin/main`, without altering the working tree). Five are pure ancestors of `main` with no unique content (their work is already folded in): **`dev/backend_api`**, **`easy_oc`**, **`performance`**, **`refractoring`**, **`yolo_text_detection`**.

### 6.1 Architecture lineage

The clearest throughline across branches is the evolution of the backend's architecture:

```
objectdetection-text (orphan — original UiA internship prototype)
        │
drawing_types ("clean up" — minimal single detect microservice, diverged early from main)
        │
dev/backend_api_julia / dev/feedback_api (pre-split monolithic cadaid_api/src/)
        │
dev/feedback_api_julia_testerting (proper detect/ + feedback/ split, services layer, SQLAlchemy)
        │
main  →  current cadaid_api/{detect,feedback,performance} + shared/ + Vue frontend
```

### 6.2 Branches by theme

**Feedback-API / persistence experiments**
- **`dev/feedback_api`** — earliest feedback endpoint, bolted onto the pre-split monolith; introduced the Norwegian user-facing validation messages (`messages.py`) still conceptually present today (e.g. *"Er du sikker på at dette er en byggesakstegning?"*).
- **`dev/feedback_api_julia_testerting`** — the most architecturally mature branch in the set: a SQLAlchemy `Metadata` ORM model (SQLite), a pluggable `MetadataStorage` interface (`InMemoryMetadataStorage` / `DatabaseMetadataStorage`), and a `detect/src/services/` refactor. Represents real, unmerged progress toward persistent (non-filesystem) storage that `main` still lacks.
- **`backend_api_are_continue`** — a content-hash-based `CacheManager` (24h TTL) to skip reprocessing identical uploads, plus a throwaway static HTML/JS/CSS "frontend-demo-test" separate from the real Vue app.

**Floorplan / room-name segmentation research**
- **`floorplan_segmentation`** → **`floorplan_check_roomnames`** (direct lineage, same base commit) — trains YOLO segmentation models and builds logic to flag rooms in a floor plan whose polygon has no OCR-detected label inside it (`check_text_inside_room()`, with a red "Mangler rombenevnelse" / "Missing room name" annotation). Also checks `fasade` drawings for required scale/cardinal-direction text against dictionary word lists (`text_in_drawings_dictionary/`). These are local, `cv2.imshow`-based research scripts, not integrated into any API.

**"Matrikkel" (cadastral registry) exploration**
- **`cadaid_matrikkel`** — despite the name and commit message ("API to extract matrikkel info"), a full-text search across the branch found **no actual Matrikkelen/cadastral-registry integration code**. It's really a clean, from-scratch restructuring of the floorplan-analysis logic into a standalone FastAPI app with `/classification` and `/floorplan` routers plus a Gradio demo UI — likely scaffolding for a matrikkel feature that was never built, or an aspirational branch name.

**Text-extraction / regex refinement**
- **`areReview`** — Azure Blob Storage abstraction (`StorageHandler`, local-vs-cloud), substantial regex overhauls for gnr/bnr and room-name patterns, done under time pressure before a demo (commit messages like "struggling with finding metadata from blob storage").
- **`backend_api_julia_new`** — fixed a dedup bug in `filter_text_within_polygons()` that was wrongly dropping valid room-name text near multiple room polygons.
- **`arebarelagerting`** — small robustness fix: segmentation handler falls back to a stored prediction image if none is passed.

**Performance / streaming architecture**
- **`charlie-tester`** — on the old `fast_api/`-layout codebase (predates the `cadaid_api/` rename): `ThreadPoolExecutor`-based parallel file processing plus a Server-Sent-Events endpoint (`GET /stream`, `sse_starlette`) for live per-file progress — an unrealized alternative to today's synchronous batch `/detect/` response.

**Frontend prototypes**
- **`areReview`**'s Vue `ResultsView`/`UploadView` polish (pre-demo) vs. **`backend_api_are_continue`**'s throwaway static-HTML demo — two non-converging frontend efforts, neither of which is what ended up on `main`.

**The origin**
- **`objectdetection-text`** — an orphan branch (no shared git history with `main`) containing the original 6-commit UiA internship project: *"Objektdeteksjon i byggesakstegninger"* ("Object detection in building-application drawings"), using real drawings from Kristiansand kommune. Trained the first YOLOv8 drawing-type classifier (450+ labeled drawings, 30 epochs) with a Flask demo and an early FastAPI endpoint. Its README's "further work" section — detecting required *components* within each drawing type (room names for plantegning, roof angle/heights for snitt, cardinal direction/scale for fasade) — is exactly the roadmap that the later branches and `main` pursued.
- **`drawing_types`** — a drastic "clean up" commit that strips the repo down from ~3,600 files to a minimal standalone `detection/` FastAPI service (one `POST /detect` endpoint). Reads as a deliberate clean-slate exploration of what a minimal detect microservice could look like, and conceptually a forerunner of `cadaid_api/detect/`.

### 6.3 All branches at a glance

| Branch | Status vs `main` | Theme |
|---|---|---|
| `objectdetection-text` | Orphan (no shared history) | Original prototype — origin of the project |
| `drawing_types` | Diverged, unmerged | Minimal clean-slate detect service |
| `dev/backend_api_julia` | Diverged, unmerged, stale | Pre-split monolithic architecture |
| `dev/feedback_api` | Diverged, unmerged, stale | Early feedback endpoint |
| `dev/feedback_api_julia_testerting` | Diverged, unmerged | SQLite-backed feedback persistence |
| `floorplan_segmentation` | Diverged, unmerged | Room segmentation training (base) |
| `floorplan_check_roomnames` | Diverged, unmerged | Room segmentation + missing-label check |
| `cadaid_matrikkel` | Diverged, unmerged | Floorplan analysis rewrite (no matrikkel code found) |
| `areReview` | Diverged, unmerged | Frontend + Azure Blob Storage, regex overhaul |
| `backend_api_julia_new` | Diverged, unmerged | Bugfix: duplicate text in segmentation |
| `arebarelagerting` | Diverged, unmerged | Segmentation endpoint config fix |
| `backend_api_are_continue` | Diverged, unmerged | Caching + throwaway demo frontend |
| `charlie-tester` | Diverged, unmerged | SSE streaming + threaded processing |
| `dev/backend_api` | Ancestor of `main` | *(fully merged, nothing unique)* |
| `easy_oc` | Ancestor of `main` | *(fully merged, nothing unique)* |
| `performance` | Ancestor of `main` | *(fully merged, nothing unique)* |
| `refractoring` | Ancestor of `main` | *(fully merged, nothing unique)* |
| `yolo_text_detection` | Ancestor of `main` | *(fully merged, nothing unique)* |

---

## 7. Configuration reference (env vars)

From `.env.dev` / `cadaid_api/shared/.env.dev`:

| Variable | Purpose |
|---|---|
| `OBJECT_DETECTION_MODEL_NAME/VERSION/PATH/CONFIDENCE` | Detection model identity + local weights path + threshold |
| `SEGMENTATION_MODEL_NAME/VERSION/PATH/CONFIDENCE` | Segmentation model identity + local weights path + threshold |
| `OCR_MODEL` | `easy_ocr` or `pytesseract_ocr` |
| `PREDICTION_IMAGE_PATH` | Sample image used by local scripts / AML endpoint env var |
| `AZURE_SUBSCRIPTION_ID`, `AZURE_RESOURCE_GROUP`, `AZUREML_WORKSPACE_NAME`, `AZURE_LOCATION` | Azure ML workspace targeting |
| `ACR_NAME` | Azure Container Registry for training/serving images |
| `AKS_CLUSTER_NAME`, `AKS_COMPUTE_NAME`, `AKS_LOCATION` | AKS compute target for the AML managed endpoint |
| `DEPLOYMENT_NAME`, `ENDPOINT_NAME`, `API_KEY`, `MODEL_NAME`, `MODEL_VERSION` | AML managed-endpoint deployment identity |
| `JWT_SECRET_KEY`, `STATIC_API_KEY` (not in `.env.dev`, only at deploy time) | API auth (currently unenforced, see §3.7) |

Note: `.env.dev`'s `OBJECT_DETECTION_YAML=data_obj/data.yaml` references a `data_obj/` path that doesn't exist in the repo (the real file is `data/data.yaml`) — likely a stale reference from a rename.

---

## 8. Consolidated known issues

1. **Committed secret** — a real `STATIC_API_KEY` value is checked into `cadaid_api/deploy/aci_deploy_processed.yaml`. Rotate the key; remove the file from tracking.
2. **Auth is scaffolded but not enforced** on any of the three services, combined with wide-open CORS.
3. **No database** — detection/feedback state lives in a single overwritten JSON file and an in-process dict; not multi-replica-safe, not durable across restarts.
4. **Frontend aggregates feedback** into a single boolean before sending to the backend, discarding the granular per-field Yes/No data the UI actually collects.
5. **Dead code**: `FeedbackView.vue`/`/feedback` route, `ProgressBar.vue`, `FileUploader.vue`, `fileHelpers.js` stub (frontend); `json_response_converter` defined but unused in `detect`; `performance` service's snitt/situasjonskart metrics unimplemented.
6. **Two unreconciled inference deployment paths** — the running Docker/ACI `detect` service vs. an experimental Azure ML managed online endpoint.
7. **Config path mismatches** in `.env.dev` (`data_obj/` vs `data/`, `data_seg/data.yaml` vs `data_seg/data_seg.yaml`).
8. **Dataset labeling bug** — `data/train/labels/gnr-bnr53-354_fasade_sør_page_1.txt` has a non-numeric class token (`w0`), unparseable by strict YOLO label loaders. Also, the segmentation dataset's test split (`data_seg/test/`) has label files for only 1 of its 110 images, so it can't be used for quantitative segmentation eval (see §5.2).

---

## 9. Glossary (Norwegian terms used throughout the codebase)

| Term | Meaning |
|---|---|
| byggesak | building-permit case/application |
| byggetegning | building/construction drawing |
| fasade | facade / elevation drawing |
| plantegning | floor plan |
| situasjonskart | site/situation map |
| snitt | section / cross-section drawing |
| rom | room |
| himmelretning(er) | cardinal direction(s) |
| målestokk | scale |
| gnr/bnr | gårdsnummer/bruksnummer — Norwegian cadastral parcel identifiers |
| matrikkel(en) | the Norwegian cadastral/land registry system |
| areal / BRA / BYA | area / usable floor area / building footprint area |
