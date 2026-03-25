# YouTube Shorts OS — System Architecture

## Overview

A modular Python pipeline that automates the full lifecycle of a faceless psychology YouTube Shorts channel: research → ideation → scripting → production → publish → analytics → improvement loop.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTELLIGENCE LAYER                           │
│   content_patterns  ←── pattern_extractor  ←── competitor_videos   │
│         ↓                                                           │
│   performance_snapshots → analyzer → idea_generator (feedback loop) │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                         PRODUCTION PIPELINE                          │
│                                                                      │
│  ideas → scripts → hook_variants → TTS audio → render → publish    │
│   DB       DB           DB           files      MP4      YouTube    │
└─────────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────────┐
│                         CONTROL LAYER                                │
│  Streamlit dashboard  |  CLI runner  |  APScheduler daemon          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.11+ | Best AI/data ecosystem, fastest iteration |
| Database | SQLite (WAL mode) | Zero-config, file-based, zero ops overhead for v1 |
| AI / LLM | Anthropic Claude API | Best instruction-following for structured JSON output |
| TTS | ElevenLabs | Highest quality AI voiceover, natural prosody |
| Video assembly | MoviePy + FFmpeg | Pythonic API, battle-tested, template-friendly |
| Stock footage | Pexels API + Pixabay API | Free commercial license, no attribution required |
| YouTube upload | Google YouTube Data API v3 | Official API, resumable uploads |
| Analytics | YouTube Analytics API v2 | Official, daily data granularity |
| Scheduling | APScheduler | Pure Python, no Redis/Celery overhead for v1 |
| Dashboard | Streamlit | Fastest Python dashboard, no frontend code |
| HTTP | httpx | Async support, connection pooling |
| Logging | loguru | Structured, colored, file rotation built in |
| Retry | tenacity | Declarative retry logic for all API calls |

**Future v2 upgrades**:
- SQLite → Postgres (when multi-process or remote DB needed)
- APScheduler → Celery + Redis (when parallel workers needed)
- Local render → Cloud render (when scaling to 5+ videos/day)

---

## Module Map

### 1. Research Engine
`modules/research/`

| File | Responsibility |
|------|---------------|
| `channel_analyzer.py` | Add competitor channels, scrape Shorts via YouTube API |
| `pattern_extractor.py` | Batch-analyze video titles/descriptions with Claude, extract patterns |

**Data flow**: competitor_channels → YouTube API → competitor_videos → Claude → content_patterns

**Runs**: Weekly (Monday 6am). Can be triggered manually anytime.

---

### 2. Idea Engine
`modules/ideas/`

| File | Responsibility |
|------|---------------|
| `idea_generator.py` | Call Claude with performance context, generate ranked idea batch |
| `idea_ranker.py` | (v2) ML-based re-ranking using historical performance signals |

**Data flow**: content_patterns + performance_snapshots → Claude → ideas (backlog)

**Trigger**: Runs automatically when backlog drops below `IDEA_BACKLOG_MIN` (default: 14)

**Claude model**: `claude-haiku-4-5` (fast, cheap for bulk generation)

---

### 3. Script Engine
`modules/scripts/`

| File | Responsibility |
|------|---------------|
| `script_generator.py` | Generate main script + 3 hook variants per idea |

**Data flow**: idea → Claude (sonnet) → scripts + hook_variants

**Claude model**: `claude-sonnet-4-6` (quality matters for scripts)

**Human checkpoint**: If `HUMAN_REVIEW_SCRIPTS=true`, scripts sit in `draft` status until approved in dashboard.

---

### 4. Production Engine
`modules/production/`

| File | Responsibility |
|------|---------------|
| `tts_generator.py` | Convert full_script to MP3 via ElevenLabs |
| `asset_preparer.py` | (v2) Fetch B-roll from Pexels/Pixabay based on visual_notes |

**Data flow**: script.full_script → ElevenLabs → audio file → production.audio_path

---

### 5. Render Pipeline
`modules/render/`

| File | Responsibility |
|------|---------------|
| `renderer.py` | Assemble final 1080x1920 MP4 using MoviePy + FFmpeg |
| `subtitle_generator.py` | (v2) Word-level subtitle timing from audio alignment |

**Render composition** (bottom to top):
1. Background layer: B-roll footage or dark gradient (1080x1920)
2. Text clips: on-screen segments from script, word-by-word, centered
3. Audio: ElevenLabs voiceover + background music at 8% volume

**Output**: `output/prod_{id}.mp4`

---

### 6. Publish Engine
`modules/publish/`

| File | Responsibility |
|------|---------------|
| `metadata_generator.py` | Claude generates title variants, description, hashtags |
| `uploader.py` | OAuth2 + resumable upload to YouTube |
| `scheduler.py` | (v2) Manage scheduled publish times, content calendar |

**Human checkpoint**: If `HUMAN_REVIEW_VIDEOS=true`, videos sit in `queued` status until approved in dashboard.

**Upload schedule**: 2 videos/day — 9am and 5pm (configurable via `PUBLISH_CRON`)

---

### 7. Analytics Engine
`modules/analytics/`

| File | Responsibility |
|------|---------------|
| `ingester.py` | Fetch daily YouTube Analytics snapshots for all live videos |
| `analyzer.py` | Score videos, update pattern success rates, generate AI insights |

**Performance score formula** (0.0–1.0):
- 40% — view count (normalized vs channel median × 3)
- 35% — average view percentage (retention)
- 25% — engagement rate (likes + comments / views, benchmarked at 5% = perfect)

**Feedback loop**: analyzer.py updates `content_patterns.success_rate`, which is read by `idea_generator.py` on next run.

---

### 8. Control Panel
`modules/dashboard/app.py`

5 pages:
- **Overview**: KPIs, recent jobs, top topic clusters
- **Idea Backlog**: Browse, approve, reject ideas
- **Script Review**: Read scripts, approve/reject with hooks visible
- **Publish Queue**: See queued videos, approve for upload
- **Analytics**: Views chart, retention distribution, top performers
- **Experiments**: A/B test tracker

---

## Job Orchestration

### Job Types (jobs/ directory)

| Job | Trigger | Duration |
|-----|---------|----------|
| `daily_research.py` | Weekly, Monday 6am | ~5 min |
| `daily_production.py` | Daily, 7am | ~10–20 min (TTS + render) |
| `daily_analytics.py` | Daily, 8am | ~2 min |
| Manual upload | Triggered from dashboard or CLI | ~2 min/video |

### Job Queue (SQLite `jobs` table)

Used for async work tracking and retry. Workers claim jobs atomically using `claim_next_job()`. All jobs support retry (max 3 attempts by default).

**V1 approach**: Jobs are run synchronously within the scheduled functions (APScheduler). No separate worker process.

**V2 approach**: Extract worker to Celery + Redis when parallel processing is needed.

---

## Data Flow (end-to-end)

```
competitor_channels (seeded manually or via research job)
    ↓
channel_analyzer → competitor_videos
    ↓
pattern_extractor → content_patterns (success rates)
    ↓
idea_generator (Claude haiku) → ideas (status: backlog)
    ↓ [human review optional]
script_generator (Claude sonnet) → scripts + hook_variants
    ↓ [human review optional]
tts_generator (ElevenLabs) → audio file
    ↓
renderer (FFmpeg/MoviePy) → video MP4
    ↓
metadata_generator (Claude haiku) → publish_queue (status: queued)
    ↓ [human approval]
uploader (YouTube API) → publish_queue.youtube_video_id (status: live)
    ↓
ingester (YouTube Analytics API) → performance_snapshots
    ↓
analyzer (Claude sonnet) → content_patterns updated + insights
    ↓ (feedback loop back to idea_generator)
```

---

## Security & Credentials

- All secrets in `.env` — never committed to git
- YouTube OAuth2 token stored in `config/youtube_token.json` — add to `.gitignore`
- API keys rotated if exposed
- No user data stored — channel data only

---

## Scaling Path

| Metric | V1 | V2 |
|--------|----|----|
| Videos/day | 2 | 5–10 |
| DB | SQLite | Postgres |
| Workers | Single process | Celery + Redis |
| Render | Local FFmpeg | Cloud render (Modal/RunPod) |
| Channels | 1 | Multi-channel |
| Analytics | YouTube API | BigQuery + Metabase |
