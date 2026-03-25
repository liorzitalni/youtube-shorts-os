-- ============================================================
-- YouTube Shorts OS — Database Schema
-- SQLite v1. All JSON fields use TEXT with [] or {} defaults.
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;

-- ============================================================
-- SECTION 1: RESEARCH LAYER
-- ============================================================

CREATE TABLE IF NOT EXISTS competitor_channels (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    youtube_channel_id  TEXT    NOT NULL UNIQUE,
    handle              TEXT,
    display_name        TEXT    NOT NULL,
    niche_tags          TEXT    NOT NULL DEFAULT '[]',   -- JSON array of strings
    subscriber_count    INTEGER,
    avg_views_per_short INTEGER,
    upload_frequency    TEXT,                            -- e.g. "daily", "2x/day"
    last_scraped_at     DATETIME,
    is_active           INTEGER NOT NULL DEFAULT 1,
    notes               TEXT,
    created_at          DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at          DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS competitor_videos (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    competitor_channel_id   INTEGER NOT NULL REFERENCES competitor_channels(id),
    youtube_video_id        TEXT    NOT NULL UNIQUE,
    title                   TEXT    NOT NULL,
    description             TEXT,
    duration_seconds        INTEGER,
    view_count              INTEGER,
    like_count              INTEGER,
    comment_count           INTEGER,
    published_at            DATETIME,
    scraped_at              DATETIME NOT NULL DEFAULT (datetime('now')),
    -- Derived analysis fields (populated by pattern_extractor)
    hook_style              TEXT,    -- question|stat|bold_claim|story|challenge
    hook_text               TEXT,    -- first sentence/line of the video
    topic_cluster           TEXT,    -- e.g. "dark_psychology", "cognitive_bias"
    has_captions            INTEGER,
    caption_style           TEXT,    -- word_by_word|full_sentence|none
    visual_style            TEXT,    -- stock_footage|animation|text_only|dark_bg
    cta_type                TEXT,    -- subscribe|comment|none|question
    estimated_retention     REAL,    -- 0.0–1.0, derived from comments + view signals
    performance_tier        TEXT,    -- top|middle|low (top = top 20% in channel)
    raw_analysis            TEXT     -- JSON blob from AI analysis
);

CREATE INDEX IF NOT EXISTS idx_competitor_videos_channel ON competitor_videos(competitor_channel_id);
CREATE INDEX IF NOT EXISTS idx_competitor_videos_views ON competitor_videos(view_count DESC);
CREATE INDEX IF NOT EXISTS idx_competitor_videos_topic ON competitor_videos(topic_cluster);

CREATE TABLE IF NOT EXISTS content_patterns (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_name    TEXT    NOT NULL UNIQUE,
    pattern_type    TEXT    NOT NULL,  -- hook_style|topic_cluster|visual_style|cta_type
    description     TEXT    NOT NULL,
    example_titles  TEXT    NOT NULL DEFAULT '[]',  -- JSON array
    avg_view_count  INTEGER,
    sample_size     INTEGER,
    success_rate    REAL,              -- % of videos using this pattern in top tier
    last_updated    DATETIME NOT NULL DEFAULT (datetime('now')),
    is_active       INTEGER NOT NULL DEFAULT 1
);

-- ============================================================
-- SECTION 2: IDEA ENGINE
-- ============================================================

CREATE TABLE IF NOT EXISTS ideas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    title               TEXT    NOT NULL,
    topic               TEXT    NOT NULL,
    topic_cluster       TEXT    NOT NULL,
    hook_angle          TEXT    NOT NULL,   -- the specific angle/spin
    hook_style          TEXT    NOT NULL,   -- question|stat|bold_claim|story
    emotional_trigger   TEXT    NOT NULL,   -- curiosity|fear|validation|surprise|outrage
    why_watch           TEXT    NOT NULL,   -- one sentence on the value prop
    originality_score   REAL    DEFAULT 0.5, -- 0.0–1.0, AI-assigned
    predicted_score     REAL    DEFAULT 0.5, -- 0.0–1.0, composite ranking score
    source_patterns     TEXT    DEFAULT '[]', -- JSON: pattern IDs that inspired this
    status              TEXT    NOT NULL DEFAULT 'backlog',
    -- statuses: backlog | approved | scripting | scripted | rejected | archived
    rejection_reason    TEXT,
    created_at          DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at          DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ideas_status ON ideas(status);
CREATE INDEX IF NOT EXISTS idx_ideas_score ON ideas(predicted_score DESC);

-- ============================================================
-- SECTION 3: SCRIPT ENGINE
-- ============================================================

CREATE TABLE IF NOT EXISTS scripts (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_id             INTEGER NOT NULL REFERENCES ideas(id),
    version             INTEGER NOT NULL DEFAULT 1,
    -- Core content
    hook_text           TEXT    NOT NULL,   -- First 3 seconds, spoken text
    hook_onscreen       TEXT,               -- On-screen text for hook (may differ)
    body_text           TEXT    NOT NULL,   -- Full voiceover script body
    close_text          TEXT    NOT NULL,   -- CTA / close line
    full_script         TEXT    NOT NULL,   -- Concatenated final voiceover text
    -- On-screen text
    onscreen_segments   TEXT    NOT NULL DEFAULT '[]', -- JSON array of {text, start_sec, end_sec}
    -- Production notes
    visual_notes        TEXT,   -- Director notes on B-roll, visuals, pacing
    music_mood          TEXT,   -- e.g. "dark ambient", "tense", "calm curiosity"
    estimated_duration  REAL,   -- seconds, estimated before TTS
    word_count          INTEGER,
    -- Status
    status              TEXT    NOT NULL DEFAULT 'draft',
    -- statuses: draft | review | approved | rejected | in_production
    review_notes        TEXT,
    model_used          TEXT,
    prompt_version      TEXT,
    created_at          DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at          DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hook_variants (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id   INTEGER NOT NULL REFERENCES scripts(id),
    variant     INTEGER NOT NULL,   -- 1, 2, 3
    style       TEXT    NOT NULL,   -- question|stat|bold_claim
    text        TEXT    NOT NULL,
    onscreen    TEXT,
    selected    INTEGER NOT NULL DEFAULT 0,  -- 1 = chosen hook
    created_at  DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- SECTION 4: PRODUCTION ENGINE
-- ============================================================

CREATE TABLE IF NOT EXISTS productions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id       INTEGER NOT NULL REFERENCES scripts(id),
    -- Assets
    audio_path      TEXT,       -- TTS-generated voiceover .mp3
    subtitle_path   TEXT,       -- .srt or .ass file path
    broll_paths     TEXT DEFAULT '[]',  -- JSON array of resolved B-roll file paths
    thumbnail_path  TEXT,
    -- Render
    video_path      TEXT,       -- Final rendered .mp4 path
    duration_actual REAL,       -- Actual video duration after render
    resolution      TEXT DEFAULT '1080x1920',
    -- Status
    status          TEXT    NOT NULL DEFAULT 'pending',
    -- statuses: pending | audio_ready | rendering | rendered | review | approved | rejected
    render_log      TEXT,
    error_message   TEXT,
    created_at      DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME NOT NULL DEFAULT (datetime('now'))
);

-- ============================================================
-- SECTION 5: PUBLISH ENGINE
-- ============================================================

CREATE TABLE IF NOT EXISTS publish_queue (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    production_id       INTEGER NOT NULL REFERENCES productions(id),
    -- Metadata
    title               TEXT    NOT NULL,
    description         TEXT    NOT NULL,
    hashtags            TEXT    NOT NULL DEFAULT '[]',  -- JSON array
    title_variants      TEXT    NOT NULL DEFAULT '[]',  -- JSON array (for testing)
    -- Schedule
    scheduled_for       DATETIME,
    slot                TEXT,       -- morning | evening
    -- Upload result
    youtube_video_id    TEXT,       -- populated after successful upload
    youtube_url         TEXT,
    upload_status       TEXT    NOT NULL DEFAULT 'queued',
    -- statuses: queued | pending_review | approved | uploading | live | failed
    upload_error        TEXT,
    uploaded_at         DATETIME,
    created_at          DATETIME NOT NULL DEFAULT (datetime('now')),
    updated_at          DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_publish_queue_status ON publish_queue(upload_status);
CREATE INDEX IF NOT EXISTS idx_publish_queue_scheduled ON publish_queue(scheduled_for);

-- ============================================================
-- SECTION 6: ANALYTICS ENGINE
-- ============================================================

CREATE TABLE IF NOT EXISTS performance_snapshots (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    publish_queue_id    INTEGER NOT NULL REFERENCES publish_queue(id),
    youtube_video_id    TEXT    NOT NULL,
    snapshot_date       DATE    NOT NULL,
    -- Core metrics
    views               INTEGER DEFAULT 0,
    watch_time_minutes  REAL    DEFAULT 0,
    avg_view_duration   REAL    DEFAULT 0,   -- seconds
    avg_view_pct        REAL    DEFAULT 0,   -- % of video watched on avg
    likes               INTEGER DEFAULT 0,
    comments            INTEGER DEFAULT 0,
    shares              INTEGER DEFAULT 0,
    subscribers_gained  INTEGER DEFAULT 0,
    -- Derived
    ctr                 REAL,   -- click-through rate (if available)
    retention_30s       REAL,   -- % retention at 30s mark
    -- Scoring (computed by analytics engine)
    performance_score   REAL,   -- composite 0.0–1.0
    created_at          DATETIME NOT NULL DEFAULT (datetime('now')),
    UNIQUE(publish_queue_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_perf_video ON performance_snapshots(youtube_video_id);
CREATE INDEX IF NOT EXISTS idx_perf_date ON performance_snapshots(snapshot_date DESC);

-- ============================================================
-- SECTION 7: EXPERIMENTATION
-- ============================================================

CREATE TABLE IF NOT EXISTS experiments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT    NOT NULL,
    description     TEXT,
    variable        TEXT    NOT NULL,   -- hook_style|video_length|topic_cluster|caption_style
    hypothesis      TEXT    NOT NULL,
    control_value   TEXT    NOT NULL,
    test_value      TEXT    NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'active',  -- active|complete|paused
    start_date      DATE,
    end_date        DATE,
    min_sample_size INTEGER DEFAULT 10,
    result_summary  TEXT,
    winner          TEXT,
    created_at      DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS experiment_videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id   INTEGER NOT NULL REFERENCES experiments(id),
    publish_id      INTEGER NOT NULL REFERENCES publish_queue(id),
    variant         TEXT    NOT NULL  -- control | test
);

-- ============================================================
-- SECTION 8: JOB QUEUE
-- ============================================================

CREATE TABLE IF NOT EXISTS jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_type        TEXT    NOT NULL,
    -- Types: research_channels | extract_patterns | generate_ideas |
    --        generate_script | generate_tts | render_video |
    --        generate_metadata | schedule_upload | upload_video |
    --        ingest_analytics | analyze_performance
    payload         TEXT    NOT NULL DEFAULT '{}',  -- JSON
    status          TEXT    NOT NULL DEFAULT 'pending',
    -- statuses: pending | running | complete | failed | cancelled
    priority        INTEGER NOT NULL DEFAULT 5,     -- 1 = highest, 10 = lowest
    attempts        INTEGER NOT NULL DEFAULT 0,
    max_attempts    INTEGER NOT NULL DEFAULT 3,
    error_message   TEXT,
    result          TEXT,   -- JSON result blob
    run_after       DATETIME,
    started_at      DATETIME,
    completed_at    DATETIME,
    created_at      DATETIME NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status, priority, run_after);

-- ============================================================
-- SEED: Initial content patterns for psychology niche
-- ============================================================

INSERT OR IGNORE INTO content_patterns (pattern_name, pattern_type, description, example_titles, success_rate) VALUES
('question_hook',       'hook_style',    'Opens with a direct question to the viewer', '["Why do you always feel tired?","What happens in your brain when you lie?"]', 0.72),
('stat_hook',           'hook_style',    'Opens with a surprising statistic',          '["95% of people never realize this about themselves","Studies show 1 in 3 people experience this"]', 0.68),
('bold_claim_hook',     'hook_style',    'Opens with a provocative statement',         '["Your memory is lying to you","The reason people stop liking you"]', 0.81),
('story_hook',          'hook_style',    'Opens with a short relatable scenario',      '["You sent a message and they left you on read...","You walk into a room and forget why..."]', 0.75),
('dark_psychology',     'topic_cluster', 'Manipulation tactics, influence, control',   '["Signs someone is manipulating you","Dark psychology tricks used on you daily"]', 0.79),
('cognitive_bias',      'topic_cluster', 'Mental shortcuts and thinking errors',       '["Why your brain makes the same mistake","The bias that controls every decision you make"]', 0.74),
('social_dynamics',     'topic_cluster', 'Why people behave in groups and relationships', '["Why people ghost you","The real reason people become distant"]', 0.77),
('self_awareness',      'topic_cluster', 'Understanding your own behavior and patterns', '["Signs you are more insecure than you think","Why you sabotage yourself"]', 0.71),
('relationship_psych',  'topic_cluster', 'Psychology of attraction, attachment, conflict', '["Why you attract the wrong people","The attachment style that ruins relationships"]', 0.76);
