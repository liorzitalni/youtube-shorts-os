# YouTube Shorts OS — Product Requirements Document

**Version**: 1.0
**Channel model**: Psychology & Human Behavior (Model A)
**Goal**: 2 publish-ready Shorts/day, faceless, automated pipeline, monetization-safe

---

## 1. Problem Statement

Building a successful YouTube Shorts channel requires consistent daily publishing, data-driven content decisions, and rapid iteration — none of which are sustainable manually. This system replaces manual operations with an automated pipeline that treats content production as a repeatable software process.

---

## 2. Channel Strategy

### Positioning
**"The psychology channel for people who want to understand humans — starting with themselves."**

Not self-help fluff. Not academic theory. Sharp, slightly dark, evidence-grounded insights delivered in under 60 seconds.

### Content pillars
| Pillar | Share | Why |
|--------|-------|-----|
| Dark Psychology | 25% | Highest engagement, share rate |
| Cognitive Biases | 25% | Educational, evergreen, high search |
| Social Dynamics | 20% | Relationship-adjacent, highly relatable |
| Self-Awareness | 20% | Growth audience, good CPM |
| Relationship Psychology | 10% | High comment rate, community building |

### Target KPIs (3-month horizon)
- Average view percentage: >50%
- Like/view ratio: >3%
- Subscriber growth: >500/month by month 2
- Videos reaching 100k views: 1+ per month by month 3

### Monetization path
1. **YouTube Partner Program**: 1,000 subscribers + 4,000 watch hours (or 10M Shorts views in 90 days)
2. **Brand deals**: Psychology apps (Headspace, BetterHelp), book publishers, productivity tools
3. **Affiliate**: Psychology books, courses, self-improvement tools

---

## 3. Functional Requirements

### Must Have (MVP)
- [ ] Database schema and initialization
- [ ] Idea generation via Claude API
- [ ] Script generation via Claude API (with hook variants)
- [ ] TTS audio via ElevenLabs
- [ ] Basic video render (voiceover + text on dark background) via FFmpeg/MoviePy
- [ ] Metadata generation via Claude API
- [ ] YouTube upload via Data API v3
- [ ] Analytics ingestion via YouTube Analytics API
- [ ] Streamlit dashboard (backlog, script review, publish queue, basic analytics)
- [ ] Human review gates for scripts and videos
- [ ] CLI pipeline runner
- [ ] APScheduler daemon for automated runs

### Should Have (v1.1)
- [ ] Pexels/Pixabay B-roll fetching based on script visual_notes
- [ ] Word-level subtitle timing (aligned to TTS audio)
- [ ] Content calendar with scheduled upload slots
- [ ] A/B experiment tracking
- [ ] Pattern success rate auto-update from analytics
- [ ] Dashboard analytics charts

### Nice to Have (v2)
- [ ] ML-based idea ranking (beyond predicted_score from Claude)
- [ ] Automated competitor monitoring (weekly diff of new top videos)
- [ ] Multi-voice TTS (different voices for different content moods)
- [ ] Thumbnail generation (via AI image gen)
- [ ] Email/Slack alerts when videos hit performance milestones
- [ ] Multi-channel support

---

## 4. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| End-to-end pipeline time | < 30 min for 2 videos |
| Render time per video | < 5 min on standard laptop |
| API error handling | All calls wrapped with retry (3 attempts, exponential backoff) |
| Data integrity | SQLite WAL + foreign keys enabled |
| Secrets | Never committed to git |
| Human override | All automation gates have a manual override path |

---

## 5. Experimentation Framework

### What to test
Priority order of what to A/B test first:

1. **Hook style** (bold_claim vs. question vs. stat)
   - Hypothesis: bold_claim hooks drive higher 3s retention
   - Metric: avg_view_pct, view count

2. **Video length** (30s vs. 45s vs. 60s)
   - Hypothesis: 45s is the sweet spot for psychology content
   - Metric: avg_view_pct, shares

3. **Topic cluster** (dark_psychology vs. cognitive_bias vs. social_dynamics)
   - Hypothesis: dark_psychology has highest share rate
   - Metric: shares, comments, view velocity

4. **Posting time** (9am vs. 5pm)
   - Metric: view count at 24h

### Experiment rules
- Minimum 5 videos per variant before drawing conclusions
- Control the non-test variable (e.g., when testing hook style, keep topic cluster constant)
- Record all experiments in the `experiments` table
- Mark the winning variant and apply to content_patterns

---

## 6. Content Quality Rules

These rules are enforced at the script generation prompt level:

1. **Factual accuracy**: All psychological claims must be real (no fabricated studies)
2. **No harmful framing**: No content that glorifies manipulation, abuse, or harm
3. **No medical advice**: Frame as "psychology" not "therapy"
4. **Originality**: System tracks recently generated ideas to avoid repetition
5. **Hook quality gate**: Every script gets 3 hook variants — the weakest are never published
6. **Word count target**: 120–150 words (55–60 seconds at natural pace)

---

## 7. MVP Roadmap

### Week 1: Foundation
- [x] Repo structure
- [x] Database schema
- [x] Settings + .env
- [x] db/connection.py
- [ ] `python scripts/setup.py` runs cleanly
- [ ] Database initializes from schema.sql

### Week 2: AI Pipeline
- [ ] Idea generator working end-to-end (generates + saves to DB)
- [ ] Script generator working end-to-end
- [ ] Both reviewable in dashboard

### Week 3: Production
- [ ] ElevenLabs TTS integration working
- [ ] Basic video render (dark background + text + voiceover)
- [ ] First video rendered locally

### Week 4: Publish
- [ ] YouTube OAuth2 set up
- [ ] First video uploaded manually via CLI
- [ ] Metadata generation working

### Month 2: Automation
- [ ] Full pipeline running daily via scheduler
- [ ] 2 videos/day publishing cadence established
- [ ] Analytics ingestion working
- [ ] Dashboard fully operational

### Month 3: Optimization
- [ ] Performance feedback loop active (patterns updated from analytics)
- [ ] First A/B experiment complete
- [ ] Content decisions driven by data, not guesswork

---

## 8. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| YouTube API quota exhaustion | Medium | High | Cache API responses, batch requests, monitor quota daily |
| ElevenLabs voice quality degradation | Low | Medium | Test multiple voice IDs, keep fallback voice |
| Claude output not parsing to JSON | Medium | Medium | JSON retry logic, prompt hardening, output validation |
| Video render failures (FFmpeg) | Medium | Medium | Error logging, fallback to simpler render (text-only) |
| YPP rejection due to content quality | Low | High | Human review gates, content quality checklist |
| Channel strike for content policy | Low | High | No sensationalism, no misleading health claims, factual grounding |
| Niche saturation before monetization | Medium | Medium | Differentiation through quality and originality, not volume |
| ElevenLabs rate limits | Low | Medium | Exponential backoff + retry, cache audio by script hash |

---

## 9. What to Build Now vs. Later

### Build Now
- Everything in the MVP roadmap (Weeks 1–4)
- Human review gates (do not skip these)
- Core dashboard pages (backlog, scripts, queue)
- CLI runner for manual ops

### Build Later (after first 30 videos published)
- B-roll fetching automation (manual B-roll selection is fine initially)
- Advanced subtitle timing (basic on-screen text works for v1)
- ML idea ranking (Claude predicted_score is sufficient for v1)
- Multi-channel support (validate single channel first)
- Thumbnail generation (YouTube auto-selects from video for Shorts)
- Email/Slack alerts (dashboard is sufficient for v1)

### Never Build (for this project)
- Social listening scraper (legal risk, not worth it)
- Comment auto-reply bot (inauthentic, damages channel trust)
- Cross-platform reposting automation (dilutes brand, different algorithm)
- Clickbait optimization (short-term views, long-term channel damage)
