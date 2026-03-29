# PROJECT_CONTEXT.md
> Complete technical context for bachelor's thesis documentation.
> Generated: 2026-03-24

---

## 1. Project Overview

### Purpose & Domain
An **aerial photo stitching web application** built as a bachelor's thesis project. The system allows users to upload drone/aerial photographs, organize them into projects, configure and trigger an image stitching pipeline, and inspect the results through an interactive tile-based viewer.

The core algorithmic work is performed by an external tool called **Exposea** (a Python-based image registration and stitching CLI). The web application acts as an orchestration layer: managing users, projects, photos, and job queues, while delegating all heavy computation to Exposea running inside a background worker process.

### What the Application Does
1. **User management** — registration, login (JWT), profile editing, account deletion
2. **Project management** — create projects, invite collaborators with role-based access
3. **Photo management** — upload drone photos to a project; previews are auto-generated and stored in S3
4. **Stitch job configuration** — users select photos, pick a preset, define output resolution, corner points, and scale, then submit a job
5. **Asynchronous processing** — jobs are queued via Redis Streams and consumed by a worker process that runs Exposea, then uploads results back to S3
6. **Result viewing** — finished jobs are sliced into a tile pyramid (Google Maps-style) and displayed in a Leaflet map viewer inside the browser; full-resolution results can be downloaded
7. **Log access** — on failure, Exposea stdout/stderr is uploaded to S3 and made available for download

### High-Level Architecture

```
Browser (Vue 3 SPA)
        │  HTTP REST (JWT)
        ▼
FastAPI backend  ──── SQLite (via SQLAlchemy async + aiosqlite)
        │                       (ORM models: User, Project, Photo, StitchJob, ProjectMember)
        │  XADD (enqueue)
        ▼
Redis Streams  ──── Consumer group "stitch-workers"
        │
        ▼ (XREADGROUP)
Worker process (app/worker.py)
        │  subprocess
        ▼
Exposea CLI (register.py)  — external Python tool; NOT part of this codebase
        │
        ▼
AWS S3 bucket  ─── photos, previews, results, tiles, logs
```

The backend and worker share the same Python codebase and database. The worker runs as a separate process (`python -m app.worker`).

---

## 2. Project Structure

```
/
├── backend/                        # FastAPI application + worker
│   ├── app/
│   │   ├── main.py                 # FastAPI app factory: CORS, router registration, startup hook
│   │   ├── config.py               # Pydantic settings (reads .env file)
│   │   ├── database.py             # Async SQLAlchemy engine (NullPool), session maker, Base
│   │   ├── worker.py               # Redis Streams consumer + Exposea runner (standalone process)
│   │   ├── models/
│   │   │   ├── user.py             # User ORM model
│   │   │   ├── project.py          # Project ORM model
│   │   │   ├── photo.py            # Photo ORM model
│   │   │   ├── stitch_job.py       # StitchJob ORM model
│   │   │   └── project_member.py   # ProjectMember ORM model (join table with role)
│   │   ├── schemas/
│   │   │   ├── user.py             # Pydantic schemas for users + auth
│   │   │   ├── project.py          # Pydantic schemas for projects
│   │   │   ├── photo.py            # Pydantic schemas for photos
│   │   │   ├── stitch_job.py       # Pydantic schemas for stitch jobs (with enums)
│   │   │   └── project_member.py   # Pydantic schemas for project members
│   │   ├── repositories/
│   │   │   ├── users_repository.py         # DB queries for users
│   │   │   ├── projects_repository.py      # DB queries for projects
│   │   │   ├── photos_repository.py        # DB queries for photos
│   │   │   ├── stitch_jobs_repository.py   # DB queries for stitch jobs
│   │   │   └── project_members_repository.py # DB queries for project members
│   │   ├── routers/
│   │   │   ├── auth.py             # /auth/* endpoints
│   │   │   ├── projects.py         # /projects/* endpoints
│   │   │   ├── photos.py           # /projects/{id}/photos/* endpoints
│   │   │   ├── stitch_jobs.py      # /projects/{id}/stitch-jobs/* endpoints
│   │   │   └── project_members.py  # /projects/{id}/members/* endpoints
│   │   ├── services/
│   │   │   ├── s3_service.py           # S3 upload/download/delete/presign (aioboto3)
│   │   │   ├── redis_service.py        # Redis Streams producer/consumer + distributed lock
│   │   │   ├── stitch_job_service.py   # Stitch job business logic (create, list, rerun)
│   │   │   └── deletion_service.py     # Cascaded deletion (user/project/photo + S3 cleanup)
│   │   ├── dependencies/
│   │   │   ├── auth.py             # get_current_user, get_current_user_flexible (tile auth)
│   │   │   └── roles.py            # require_project_role, require_project_role_flexible
│   │   └── utils/
│   │       └── auth.py             # Password hashing (SHA256+bcrypt), JWT encode/decode
│   ├── alembic/
│   │   ├── env.py                  # Alembic async environment
│   │   └── versions/               # 7 migration files (see §5)
│   ├── requirements.txt
│   └── .env                        # Environment variables (not in git)
│
└── frontend/                       # Vue 3 SPA
    ├── src/
    │   ├── main.ts                 # Vue app entry: createApp + router + mount
    │   ├── App.vue                 # Root component: router-view + ToastContainer + auth init
    │   ├── style.css               # Tailwind v4 import, @theme tokens, shadcn CSS vars
    │   ├── router/
    │   │   └── index.ts            # Vue Router config + navigation guard
    │   ├── stores/
    │   │   └── authStore.ts        # Reactive auth state (token, user, isAuthenticated)
    │   ├── api/
    │   │   ├── client.ts           # Axios instance with JWT interceptor
    │   │   ├── auth.ts             # Auth API calls
    │   │   ├── projects.ts         # Projects API calls
    │   │   ├── photos.ts           # Photos API calls
    │   │   ├── stitchJobs.ts       # Stitch jobs API calls
    │   │   └── projectMembers.ts   # Project members API calls
    │   ├── types/
    │   │   ├── auth.ts             # User, LoginData, RegisterData, TokenResponse
    │   │   ├── project.ts          # Project, ProjectCreate, ProjectRole
    │   │   ├── photo.ts            # PhotoItem
    │   │   ├── stitchJob.ts        # StitchJob, enums, constants, options arrays
    │   │   └── projectMember.ts    # ProjectMember, AddMemberRequest
    │   ├── lib/
    │   │   ├── utils.ts            # cn() helper (clsx + tailwind-merge)
    │   │   └── toast.ts            # Toast notification system
    │   ├── components/
    │   │   ├── ui/                 # shadcn-vue manually created components
    │   │   │   ├── button.vue / button.ts
    │   │   │   ├── input.vue / input.ts
    │   │   │   ├── label.vue / label.ts
    │   │   │   └── card.vue / card.ts
    │   │   ├── CreateProjectForm.vue     # New project creation form
    │   │   ├── ProjectList.vue           # Projects grid with actions
    │   │   ├── PhotoUpload.vue           # File input for photo upload
    │   │   ├── UploadedPhotosList.vue    # Photo gallery with delete + set-reference
    │   │   ├── StitchJobForm.vue         # Stitch job configuration form
    │   │   ├── StitchJobHistory.vue      # Table of past jobs with actions
    │   │   ├── StitchJobParameters.vue   # Wrapper combining job status + form
    │   │   ├── LeafletViewer.vue         # Interactive tile viewer modal
    │   │   ├── ManageUsersModal.vue      # Add/remove/update project members
    │   │   ├── ConfirmModal.vue          # Generic confirmation dialog
    │   │   └── ToastContainer.vue        # Toast notifications display
    │   ├── pages/
    │   │   ├── LoginPage/LoginPage.vue
    │   │   ├── RegisterPage/RegisterPage.vue
    │   │   ├── ProjectsPage/ProjectsPage.vue
    │   │   ├── ProjectWorkspacePage/ProjectWorkspacePage.vue
    │   │   ├── ProjectHistoryPage/ProjectHistoryPage.vue
    │   │   └── AccountSettingsPage/AccountSettingsPage.vue
    │   └── layouts/
    │       └── DefaultLayout.vue         # Basic layout wrapper
    ├── package.json
    ├── vite.config.ts
    └── tsconfig.app.json
```

---

## 3. Frontend (Vue.js)

### Routing (`src/router/index.ts`)

| Route | Component | Auth Required |
|-------|-----------|---------------|
| `/` | redirect → `/projects` | — |
| `/login` | LoginPage | No (redirects to /projects if already authed) |
| `/register` | RegisterPage | No |
| `/projects` | ProjectsPage | Yes |
| `/projects/:projectId/workspace` | ProjectWorkspacePage | Yes |
| `/projects/:projectId/history` | ProjectHistoryPage | Yes |
| `/settings` | AccountSettingsPage | Yes |

Navigation guard reads `authStore.isAuthenticated`; unauthenticated users are redirected to `/login`, authenticated users trying to reach `/login` or `/register` are redirected to `/projects`.

### Pages

**LoginPage** — email + password form; calls `auth.login()`, stores token in `authStore`, fetches current user, navigates to `/projects`. Shows per-field validation errors from both client-side and API 422 responses.

**RegisterPage** — name + email + password form; calls `auth.register()`, then auto-logs in with same credentials.

**ProjectsPage** — main dashboard:
- Lists all projects the user is a member of (with photo count, role, latest job status)
- Shows the reference photo from the latest finished job per project
- Search/filter bar for projects
- Create new project form (inline)
- Gear icon → ManageUsersModal (owner only)
- Delete project with ConfirmModal
- Navigation to workspace and history for each project

**ProjectWorkspacePage** — active work area:
- Photo upload section (PhotoUpload + UploadedPhotosList)
- Reference photo selection (clicking ⊙ on a photo card sets it as reference)
- StitchJobParameters component with the StitchJobForm
- Shows latest job status banner
- Can trigger re-run of failed/finished jobs
- Tile viewer (LeafletViewer modal) for finished jobs with `tiles_ready = true`

**ProjectHistoryPage** — read-only job log:
- Uses StitchJobHistory component
- Paginated table of all stitch jobs for the project
- Status filter pills (All / Queued / Running / Finished / Failed)
- Auto-refresh every 10 s when active jobs exist
- Download result button (green ↓) for finished jobs
- Download log button (red ↓) for failed jobs that have a log file in S3
- Error tooltip on hover (monospace, 480 px wide)
- Copy error to clipboard button
- Corner points tooltip on hover

**AccountSettingsPage** — profile management:
- Update name and email
- Change password (old + new)
- Delete account with confirmation (cascades all data)

### State Management (`src/stores/authStore.ts`)

Simple reactive object (not Pinia):
```typescript
{
  token: string | null,   // persisted in localStorage
  user: User | null,
  isAuthenticated: boolean  // computed from token != null
}
```
Methods: `setToken()`, `setUser()`, `logout()`, `getToken()`.

### Key Components

**StitchJobForm.vue** — the most complex form:
- Fields: Experiment Name, Preset, Reference Image (read-only, set externally), Final Height/Width (px), Output Format, Relative Scale, Corner Points (4 × [X, Y])
- All fields have info (ⓘ) tooltips with dark floating popover
- Real-time validation; submit disabled until valid
- On submit: calls `createStitchJob()`, emits `created` event

**StitchJobHistory.vue** — paginated table component:
- Columns: #, Exp Name, Status, Created, Finished, Preset, Reference, Resolution, Format, Scale, Points, Result, ↓
- Hover tooltips: corner points details, error message details
- Download result: fetches presigned URL on demand, opens in new tab
- Download log: fetches presigned URL, fetches blob via `fetch()`, triggers browser download with `<a download>` + blob URL (workaround for cross-origin S3 URLs ignoring the `download` attribute)
- Auto-polling via `setInterval` when jobs are active

**LeafletViewer.vue** — Leaflet map in a modal:
- Uses `L.TileLayer` with custom URL template pointing to backend tile proxy
- JWT passed via `?token=` query parameter (Leaflet cannot set headers)
- Metadata (width/height/max_zoom) used to set map bounds and zoom levels
- Download button for full-resolution result

### Styling
- **Tailwind CSS v4** via `@tailwindcss/vite` plugin — no `tailwind.config.js`
- Custom `@theme` tokens in `style.css`: `--color-primary: #3b82f6`, `--color-danger: #ef4444`, `--color-bg`, `--color-muted`, `--color-border`
- **shadcn-vue** components created manually (CLI broken in WSL due to Windows path resolution)
- All dynamic class variants use helper functions returning full static class strings (required by Tailwind v4 scanner)

---

## 4. Backend (FastAPI)

### All API Endpoints

#### Auth (`/auth`)
| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| POST | `/auth/register` | No | — | Register new user; returns UserResponse |
| POST | `/auth/login` | No | — | Login; returns JWT token |
| GET | `/auth/me` | JWT | — | Get current user profile |
| PATCH | `/auth/me` | JWT | — | Update name/email/password; re-issues token if email changes |
| DELETE | `/auth/me` | JWT | — | Delete account + all projects/photos/jobs from DB and S3 |

#### Projects (`/projects`)
| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| POST | `/projects` | JWT | — | Create project; creator auto-added as owner |
| GET | `/projects` | JWT | — | List projects where user is a member (with photo_count, role) |
| GET | `/projects/{id}` | JWT | Member | Get project detail with user's role |
| DELETE | `/projects/{id}` | JWT | Owner | Delete project + all data from DB and S3 |

#### Photos (`/projects/{project_id}/photos`)
| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| POST | `/projects/{id}/photos` | JWT | Owner/Editor | Upload photo (multipart); generates preview; stores in S3 + DB |
| GET | `/projects/{id}/photos` | JWT | Member | List photos with presigned preview URLs |
| GET | `/projects/{id}/photos/{pid}` | JWT | Member | Get presigned URL + preview_url for single photo |
| GET | `/projects/{id}/photos/{pid}/preview` | JWT | Member | Serve preview JPEG (from S3 or on-demand from original) |
| DELETE | `/projects/{id}/photos/{pid}` | JWT | Owner/Editor | Delete photo from DB + S3 |

#### Stitch Jobs (`/projects/{project_id}/stitch-jobs`)
| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| POST | `/projects/{id}/stitch-jobs` | JWT | Owner/Editor | Create and enqueue a stitch job |
| GET | `/projects/{id}/stitch-jobs` | JWT | Member | List jobs with pagination + filters |
| POST | `/projects/{id}/stitch-jobs/{jid}/run` | JWT | Owner/Editor | Re-run a failed/finished job |
| GET | `/projects/{id}/stitch-jobs/{jid}` | JWT | Member | Get job details |
| GET | `/projects/{id}/stitch-jobs/{jid}/result` | JWT | Member | Get presigned download URL for result file |
| GET | `/projects/{id}/stitch-jobs/{jid}/log` | JWT | Member | Get presigned download URL for log file |
| GET | `/projects/{id}/stitch-jobs/{jid}/tiles/metadata` | JWT | Member | Get tile pyramid metadata (width, height, max_zoom) |
| GET | `/projects/{id}/stitch-jobs/{jid}/tiles/{z}/{x}/{y}` | JWT/token | Member | Proxy tile JPEG from S3 (accepts ?token= for Leaflet) |

#### Project Members (`/projects/{project_id}/members`)
| Method | Path | Auth | Role | Description |
|--------|------|------|------|-------------|
| GET | `/projects/{id}/members` | JWT | Owner | List all members |
| POST | `/projects/{id}/members` | JWT | Owner | Add member by email with role |
| PATCH | `/projects/{id}/members/{uid}` | JWT | Owner | Update member role (editor/viewer only) |
| DELETE | `/projects/{id}/members/{uid}` | JWT | Owner | Remove member (cannot remove self as owner) |

#### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"ok": true}` |

### Authentication Flow

1. Client sends `POST /auth/login` with `{email, password}`
2. Server verifies password (SHA256 pre-hash → bcrypt.verify)
3. Returns `{access_token, token_type: "bearer"}`
4. Client stores token in `localStorage`
5. All subsequent requests include `Authorization: Bearer <token>` header
6. `get_current_user` dependency decodes JWT, queries DB by email (sub claim), raises 401 if invalid

**Special case — tile serving:** The `GET .../tiles/{z}/{x}/{y}` endpoint accepts the token via `?token=` query param because Leaflet cannot inject custom headers into tile URL requests.

### Request/Response Examples

**Create Stitch Job (POST `/projects/{id}/stitch-jobs`)**

Request body:
```json
{
  "photo_ids": ["uuid1", "uuid2", "uuid3"],
  "exp_name": "map_result_01",
  "ref_name": "reference.JPG",
  "preset_name": "default",
  "final_res": [6000, 9000],
  "save_format": "tiff",
  "corner_points": [[0,0],[9000,0],[9000,6000],[0,6000]],
  "relative_scale": 2
}
```

Response (`StitchJobOut`):
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "status": "queued",
  "exp_name": "map_result_01",
  "ref_name": "reference.JPG",
  "ref_photo_id": "uuid",
  "preset_name": "default",
  "final_res": [6000, 9000],
  "save_format": "tiff",
  "corner_points": [[0,0],[9000,0],[9000,6000],[0,6000]],
  "relative_scale": 2.0,
  "photo_ids": ["uuid1", "uuid2", "uuid3"],
  "attempt": 0,
  "created_at": "2026-03-24T12:00:00Z",
  "queued_at": "2026-03-24T12:00:00Z",
  "started_at": null,
  "finished_at": null,
  "result_s3_key": null,
  "log_s3_key": null,
  "error_message": null,
  "tiles_s3_prefix": null,
  "tiles_metadata": null,
  "tiles_ready": false
}
```

---

## 5. Database (SQLAlchemy)

### Models

#### User
```
id            String (UUID, PK)
name          String
email         String (unique, indexed)
hashed_password String
created_at    DateTime (UTC)

Relationships:
  photos      → Photo[] (cascade delete-orphan)
  projects    → Project[] (cascade delete-orphan)
  memberships → ProjectMember[] (cascade delete-orphan)
```

#### Project
```
id            String (UUID, PK)
user_id       String (FK → User.id, indexed, cascade)
name          String
description   String (nullable)
created_at    DateTime (UTC)

Relationships:
  user    → User
  photos  → Photo[] (cascade delete-orphan)
  members → ProjectMember[] (cascade delete-orphan)
```

#### Photo
```
id              String (UUID, PK)
s3_key          String           — e.g. "photos/{uuid}.jpg"
preview_s3_key  String (nullable) — e.g. "photos/previews/{uuid}.jpg"
original_name   String           — original filename
mime            String
size            Integer (bytes)
user_id         String (FK → User.id)
project_id      String (FK → Project.id, indexed, cascade)
created_at      DateTime (UTC)

Relationships:
  user    → User
  project → Project
```

#### StitchJob
```
id                String (UUID, PK)
project_id        String (FK → Project.id, indexed)
user_id           String (FK → User.id)
status            String (indexed) — queued|running|finished|failed|canceled

# Exposea parameters
exp_name          String           — output experiment name
ref_name          String           — filename of reference photo
preset_name       String           — debug|default|p_100mpx|p_200mpx|p_400mpx|p_normal
final_res_height  Integer
final_res_width   Integer
save_format       String           — jp2|j2k|tiff|tif
corner_points     String (JSON)    — [[x,y],[x,y],[x,y],[x,y]]
relative_scale    Float
photo_ids         String (JSON)    — ["uuid1", "uuid2", ...]
ref_photo_id      String (nullable) — UUID of the reference Photo row

# Timestamps
created_at        DateTime (UTC)
queued_at         DateTime (nullable)
started_at        DateTime (nullable)
finished_at       DateTime (nullable)

# Results
result_s3_key     String (nullable) — S3 key of stitched output file
log_s3_key        String (nullable) — S3 key of stdout+stderr log
error_message     String (nullable) — user-friendly failure reason

# Tiles
tiles_s3_prefix   String (nullable) — S3 prefix for tile pyramid
tiles_metadata    String (JSON, nullable) — {width, height, tile_size, min_zoom, max_zoom, ...}
tiles_ready       Boolean (default False)

# Retry tracking
attempt           Integer (default 0)
```

#### ProjectMember
```
project_id  String (FK → Project.id, PK part 1, cascade)
user_id     String (FK → User.id, PK part 2, cascade)
role        String  — owner|editor|viewer

Relationships:
  project → Project
  user    → User
```

### Database Configuration
- **Engine:** SQLite via `aiosqlite`; `NullPool` prevents stale reads between async operations
- **Session:** `async_session_maker` yields `AsyncSession` per request (dependency injection)
- **Startup:** `Base.metadata.create_all` on FastAPI startup (in addition to Alembic migrations)
- **Migrations:** Alembic with async env; batch mode required for SQLite `ALTER TABLE` limitations

### Migration History
1. Initial (empty placeholder)
2. Create `projects` table; add `project_id` FK to `photos` (batch mode)
3. Data migration: assign existing orphan photos to auto-created projects
4. Create `stitch_jobs` table with all job fields; indices on `status` and `project_id`
5. Create `project_members` table; seed existing projects with creator as owner
6. Add `ref_photo_id` (nullable FK) to `stitch_jobs`
7. Add `preview_s3_key` (nullable) to `photos`

---

## 6. Key Business Logic

### Stitch Job Lifecycle (end-to-end)

```
User fills form → POST /projects/{id}/stitch-jobs
    ↓
stitch_job_service.create_and_enqueue_job():
  1. Validate all photo_ids belong to the project
  2. Find ref_photo_id by matching ref_name → Photo.original_name
  3. Create StitchJob in DB (status=queued, queued_at=now)
  4. redis_service.enqueue_stitch_job(job_id) → XADD stitch:jobs
    ↓
Worker (app/worker.py) — main loop reads from Redis Streams:
  1. XREADGROUP → (msg_id, {job_id})
  2. Load job from DB
  3. Skip if status not in (queued, running)
  4. Check max retries if reclaim
  5. redis_service.acquire_job_lock(job_id)  ← distributed lock, TTL 600s
  6. Spawn heartbeat task (refreshes lock + PEL claim every 180s)
  7. _update_job(status=running, started_at, attempt++)
  8. Validate EXPOSEA_PATH/register.py exists
  9. Download photos from S3 → /tmp/stitch_worker/{job_id}-{attempt}-{uuid}/task/images/
 10. Write config.yaml (YAML with inline arrays, quoted save_format)
 11. subprocess: python register.py -i task/ -o output/
 12. If returncode != 0: raise RuntimeError("Exposea exited with code N")
 13. Find result file (.tiff/.tif/.j2k/.jp2) in output/
 14. Upload result → S3 stitch-results/{project_id}/{job_id}/{exp_name}{suffix}
 15. _update_job(status=finished, result_s3_key)
 16. Generate tile pyramid (Pillow or ImageMagick fallback)
 17. Upload tiles → S3 stitch-tiles/{project_id}/{job_id}/{z}/{x}/{y}.jpg
 18. Upload metadata.json
 19. _update_job_tiles(tiles_s3_prefix, tiles_metadata) → tiles_ready=True
 20. XACK msg_id
    ↓ (on any exception)
  E1. Upload stdout+stderr → S3 stitch-logs/{job_id}.txt  (if Exposea ran)
  E2. _update_job(status=failed, error_message=_parse_error_message(exc), log_s3_key)
  E3. XACK msg_id  (always ack to prevent infinite retry loop)
    ↓ (finally block, always)
  F1. Stop heartbeat task
  F2. Release distributed lock
  F3. Remove job_id from _active_jobs
  F4. Clean up /tmp work directory
```

### Tile Pyramid Generation (`_generate_tiles_pil`)

1. Opens stitched image with Pillow; if Pillow fails (e.g., SGILOG-encoded TIFF), falls back to ImageMagick `convert` with gamma correction
2. Computes `max_zoom = ceil(log2(max(width, height) / 256))`, capped at 10
3. For each zoom level `z` from 0 to max_zoom:
   - Scale factor = `2^(max_zoom - z)` → scales down at lower zoom levels
   - Resize image to scaled dimensions using LANCZOS
   - Slice into 256×256 tiles; pad with white fill if edge tile is smaller
   - Save as JPEG quality 85
4. Upload all `{z}/{x}/{y}.jpg` tiles to S3 under prefix
5. Upload `metadata.json` with width, height, tile_size, min_zoom, max_zoom, tile_format

### Distributed Job Locking

The worker uses Redis SET NX (set-if-not-exists) with TTL 600 s to ensure only one worker processes a given job at a time. The heartbeat task (every 180 s) extends the TTL, keeping it alive for jobs that take longer than 10 minutes. The lock key is `job_lock:{job_id}`. The lock is released via a Lua script that deletes the key only if the current worker owns it.

### Reclaim / Crash Recovery

Redis Streams tracks which messages have been delivered but not acknowledged in the PEL (Pending Entry List). If the worker crashes or is killed, messages stay in the PEL with an increasing idle time. The reclaim loop (every ~45 s) calls `XAUTOCLAIM` to find messages idle longer than `claim_idle_ms` (15 minutes) and reprocesses them. The 15-minute threshold is safely above the heartbeat refresh interval (3 minutes), so a healthy running job is never reclaimed.

### User-Friendly Error Messages (`_parse_error_message`)

When a job fails, the raw exception message is mapped to a user-readable string before being stored in `error_message`. The mapping:
- `"not found in DB"` → photo was deleted before job ran
- `"Exposea not found"` → misconfiguration (wrong EXPOSEA_PATH)
- `"Max retries exceeded"` → passed through as-is
- `"produced no output"` → incompatible images
- `"Exposea exited with code"` → generic algorithm failure message
- Anything else → "unexpected error" with suggestion to check the log file

If Exposea actually ran (stdout/stderr non-empty), the combined output is uploaded to S3 as a log file, and `log_s3_key` is set on the job so the UI can display a download button.

### Photo Preview Generation

On upload, the server generates a preview (800×800 px max, JPEG quality 75) using Pillow:
1. Opens the uploaded photo bytes
2. Applies `ImageOps.exif_transpose` (correct orientation from EXIF)
3. `thumbnail((800, 800))` — resizes maintaining aspect ratio
4. Saves as JPEG with quality 75 to bytes buffer
5. Uploads to S3 at `photos/previews/{uuid}.jpg`
6. Stores `preview_s3_key` in the DB alongside `s3_key`

If no preview was generated at upload time (older records), the `GET .../preview` endpoint generates it on demand from the original.

### Cascaded Deletion Strategy (`deletion_service.py`)

Delete order is critical to avoid orphaned S3 files:
1. **Collect** all S3 keys from DB (photos, previews, results, logs, tile keys from prefix listing)
2. **Delete from DB** (SQLAlchemy cascade handles related rows); commit
3. **Delete from S3** (batch, up to 1000 keys per request)

This ordering means an S3 failure leaves orphaned S3 objects (acceptable) but never leaves DB rows pointing to missing S3 objects.

### Password Security

Passwords are pre-hashed with SHA256 before bcrypt, solving bcrypt's 72-byte maximum input limit. This ensures passwords longer than 72 characters are handled correctly.

---

## 7. Dependencies

### Backend (`requirements.txt`)
```
fastapi==0.118.0            # Web framework
uvicorn[standard]==0.37.0   # ASGI server
sqlalchemy==2.0.43          # ORM (async)
aiosqlite==0.21.0           # SQLite async driver
aiofiles==25.1.0            # Async file I/O
python-multipart==0.0.20    # Multipart form parsing (file upload)
python-dotenv==1.1.1        # .env loading
pydantic-settings==2.11.0   # Settings from environment variables
aioboto3==13.2.0            # Async AWS SDK (S3)
passlib[bcrypt]==1.7.4      # Password hashing
bcrypt==4.1.3               # Bcrypt implementation
python-jose[cryptography]==3.3.0  # JWT encode/decode
email-validator>=2.0.0      # Email validation for Pydantic
alembic==1.13.1             # Database migrations
redis>=5.0.0                # Redis client (sync+async)
pyyaml>=6.0                 # YAML parsing (used internally)
Pillow>=10.0.0              # Image processing (preview gen + tile gen)
```

### Frontend (`package.json`)
```json
"dependencies": {
  "vue": "^3.5.22",                     // Vue 3 framework
  "vue-router": "^4.6.4",               // Client-side routing
  "axios": "^1.12.2",                   // HTTP client
  "leaflet": "^1.9.4",                  // Tile map viewer
  "@types/leaflet": "^1.9.21",          // TypeScript types for Leaflet
  "class-variance-authority": "^0.7.1", // CVA for component variants
  "clsx": "^2.1.1",                     // Class string builder
  "tailwind-merge": "^3.5.0",           // Tailwind class deduplication
  "lucide-vue-next": "^0.577.0"         // Icon library
},
"devDependencies": {
  "vite": "^7.1.7",                     // Build tool / dev server
  "@vitejs/plugin-vue": "^6.0.1",       // Vue SFC support for Vite
  "tailwindcss": "^4.2.1",              // Utility CSS framework
  "@tailwindcss/vite": "^4.2.1",        // Tailwind v4 Vite plugin
  "typescript": "~5.9.3",               // TypeScript compiler
  "vue-tsc": "^3.1.0",                  // Vue TypeScript type checking
  "@vue/tsconfig": "^0.8.1"             // Vue TS config preset
}
```

---

## 8. Current Development State

### Fully Implemented
- User registration, login, JWT auth, profile update, account deletion with full cascade
- Project CRUD with role-based access (owner / editor / viewer)
- Project member management (add by email, update role, remove)
- Photo upload with automatic preview generation, presigned URL serving, deletion
- Stitch job creation with full parameter validation
- Redis Streams-based job queue with consumer groups
- Distributed locking (SET NX) + heartbeat refresh for long-running jobs
- Reclaim / crash recovery loop (XAUTOCLAIM with idle threshold)
- Full Exposea integration: download photos → build YAML → run CLI → upload result
- Tile pyramid generation (Pillow primary, ImageMagick fallback) + S3 upload
- Leaflet tile viewer in the browser
- Full-resolution result download via presigned S3 URL
- Job failure log upload (stdout+stderr → S3) + log download in UI
- User-friendly error messages (no raw tracebacks shown to users)
- Job re-run (reset + re-enqueue)
- Paginated job history with filtering by status
- Auto-polling in UI when active jobs exist
- Toast notification system
- Full Tailwind CSS v4 + shadcn-vue UI components

### Known Issues / TODOs
- **`relative_scale` silently truncated to int** in `_build_exposea_config_yaml` — `int(job.relative_scale)` rounds down; should use `round()` if fractional scales are valid
- **Large result file read blocks event loop** — `result_file.read_bytes()` is synchronous; for very large files (hundreds of MB) this blocks asyncio; should use `asyncio.to_thread`
- **CORS is fully open** (`allow_origins=["*"]`) — appropriate for development but should be restricted in production
- **No tests** — no unit or integration tests exist in the codebase
- **No rate limiting** — API has no rate limiting on any endpoint
- **SQLite in production** — SQLite works for single-instance deployment but does not scale horizontally; a migration to PostgreSQL would be needed for multi-instance
- **`canceled` status** — the JobStatus enum includes `canceled` but there is no API endpoint to cancel a running job (the status exists in the DB but is never set by the application)
- **Redis disabled by default** — when `REDIS_ENABLED=false`, `enqueue_stitch_job` silently returns `None`; jobs are created in DB with status `queued` but never processed
- **Sequential tile upload** — tiles are uploaded one-by-one in a loop; for large images at high zoom levels (thousands of tiles) this is slow; concurrent uploads would improve throughput

---

## 9. Environment Variables

```env
# Required
SECRET_KEY=<random-string>                    # JWT signing key
DATABASE_URL=sqlite+aiosqlite:///./app.db     # or absolute path
AWS_ACCESS_KEY_ID=<key>
AWS_SECRET_ACCESS_KEY=<secret>
AWS_REGION=eu-north-1
S3_BUCKET_NAME=<bucket-name>

# Optional
AWS_ENDPOINT_URL=http://localhost:4566        # For LocalStack local dev
REDIS_ENABLED=true                            # Default: false
REDIS_URL=redis://localhost:6379/0
EXPOSEA_PATH=/path/to/exposea/repo            # Default: /home/makaroni/Exposea

# Worker tuning (rarely changed)
STREAM_KEY=stitch:jobs
CONSUMER_GROUP=stitch-workers
BLOCK_MS=5000
CLAIM_IDLE_MS=900000                          # 15 minutes
MAX_RETRIES=3
WORK_DIR=/tmp/stitch_worker
```

---

## 10. Running the Project

```bash
# Backend API
cd backend
pip install -r requirements.txt
alembic upgrade head          # apply DB migrations
uvicorn app.main:app --reload  # http://localhost:8000
# Swagger UI: http://localhost:8000/docs

# Background worker (separate terminal)
cd backend
REDIS_ENABLED=true python -m app.worker

# Frontend
cd frontend
npm install
npm run dev                   # http://localhost:5173
npm run build                 # production build
```

S3 can be replaced with LocalStack for local development by setting `AWS_ENDPOINT_URL=http://localhost:4566`.

Redis must be running for jobs to be processed. Without Redis, jobs are created in the DB but remain `queued` forever.
