# YouTube Shorts OS

An automated operating system for building a faceless YouTube Shorts channel.

**Channel**: Psychology & Human Behavior
**Target**: 2 Shorts/day, monetizable, faceless, automation-first

---

## Architecture

```
Research Engine  →  Idea Engine  →  Script Engine  →  Production Engine
     ↓                   ↑               ↓                    ↓
content_patterns    (feedback)      TTS Audio             Render Pipeline
     ↑                   |               ↓                    ↓
Analytics Engine  ←  YouTube API   Publish Engine  ←   Metadata Engine
```

Full details: [docs/architecture.md](docs/architecture.md)
Product requirements: [docs/prd.md](docs/prd.md)

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup
```bash
python scripts/setup.py
```
Fill in `.env` with your API keys.

### 3. Set up YouTube OAuth2
- Enable YouTube Data API v3 + YouTube Analytics API in Google Cloud Console
- Download `client_secrets.json` → `config/client_secrets.json`

### 4. Run the dashboard
```bash
streamlit run modules/dashboard/app.py
```

### 5. Run your first production cycle
```bash
# Populate idea backlog
python scripts/run_pipeline.py generate-ideas

# Review ideas in dashboard, approve the best ones

# Generate scripts for approved ideas
python scripts/run_pipeline.py produce

# Review scripts in dashboard, approve

# Run again to proceed through TTS → render → metadata
python scripts/run_pipeline.py produce

# Upload approved videos
python scripts/run_pipeline.py upload
```

### 6. Start the scheduler (daily automation)
```bash
python scripts/run_pipeline.py scheduler
```

---

## Pipeline CLI

```bash
python scripts/run_pipeline.py research        # Scrape competitors, extract patterns
python scripts/run_pipeline.py produce         # Full production run
python scripts/run_pipeline.py analytics       # Ingest YouTube Analytics
python scripts/run_pipeline.py upload          # Upload approved videos
python scripts/run_pipeline.py generate-ideas  # Generate idea batch only
python scripts/run_pipeline.py generate-script <idea_id>  # Script one idea
python scripts/run_pipeline.py scheduler       # Start cron daemon
```

---

## Repo Structure

```
youtube/
├── config/
│   ├── settings.py              # Central config (pydantic-settings)
│   ├── prompts/
│   │   ├── idea_generation.md   # Prompt: bulk idea generation
│   │   ├── script_generation.md # Prompt: retention-optimized scripts
│   │   ├── hook_variants.md     # Prompt: 3 hook alternatives
│   │   ├── metadata_generation.md # Prompt: titles, description, hashtags
│   │   └── performance_analysis.md # Prompt: analytics insights
│   └── client_secrets.json      # YouTube OAuth (not committed)
├── data/
│   ├── schema.sql               # Full SQLite schema
│   ├── shorts_os.db             # Database (not committed)
│   └── assets/
│       ├── audio/               # TTS-generated MP3s
│       ├── music/               # Background music tracks
│       └── broll/               # Downloaded B-roll clips
├── db/
│   └── connection.py            # DB connection, query utils, job queue
├── docs/
│   ├── architecture.md          # Full system architecture
│   └── prd.md                   # Product requirements + roadmap
├── jobs/
│   ├── daily_research.py        # Weekly research job
│   ├── daily_production.py      # Daily production job
│   └── daily_analytics.py       # Daily analytics job
├── modules/
│   ├── research/
│   │   ├── channel_analyzer.py  # Competitor channel scraping
│   │   └── pattern_extractor.py # Claude-powered pattern analysis
│   ├── ideas/
│   │   └── idea_generator.py    # Claude idea generation + backlog mgmt
│   ├── scripts/
│   │   └── script_generator.py  # Claude script + hook variant generation
│   ├── production/
│   │   └── tts_generator.py     # ElevenLabs voiceover generation
│   ├── render/
│   │   └── renderer.py          # FFmpeg/MoviePy video assembly
│   ├── publish/
│   │   ├── metadata_generator.py # Claude metadata generation
│   │   └── uploader.py          # YouTube Data API v3 upload
│   ├── analytics/
│   │   ├── ingester.py          # YouTube Analytics API ingestion
│   │   └── analyzer.py          # Performance scoring + feedback loop
│   └── dashboard/
│       └── app.py               # Streamlit control panel
├── output/                      # Rendered videos (not committed)
├── scripts/
│   ├── setup.py                 # First-run setup script
│   └── run_pipeline.py          # CLI for all pipeline operations
├── .env.example                 # Environment variable template
├── .gitignore
└── requirements.txt
```

---

## Environment Variables

See `.env.example` for all variables. Required to fill in:

| Variable | Where to get it |
|----------|----------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `ELEVENLABS_API_KEY` | elevenlabs.io |
| `ELEVENLABS_VOICE_ID` | ElevenLabs voice library |
| `YOUTUBE_CHANNEL_ID` | YouTube Studio > Settings > Channel > Advanced |
| `PEXELS_API_KEY` | pexels.com/api |

---

## Human Review Gates

By default, two human review checkpoints are active:

1. **Script review** (`HUMAN_REVIEW_SCRIPTS=true`)
   After scripts are generated, they wait in `draft` status.
   Go to dashboard → Script Review → approve or reject.

2. **Video review** (`HUMAN_REVIEW_VIDEOS=true`)
   After render, videos wait in `queued` status.
   Go to dashboard → Publish Queue → approve for upload.

Set both to `false` in `.env` for fully automated operation (not recommended initially).

---

## Adding Background Music

Place royalty-free MP3 tracks (no attribution required, commercial use OK) in:
```
data/assets/music/dark_ambient/    # for dark psychology content
data/assets/music/tense/           # for cognitive bias / social dynamics
data/assets/music/calm/            # for self-awareness content
```

Recommended sources: Pixabay Music, Free Music Archive (CC0), Uppbeat (free tier).
