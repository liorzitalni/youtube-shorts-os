"""
Batch 10: Workplace Psychology Series
10 high-quality shorts on office dynamics, raises, credit stealing, bad managers.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import execute, fetchone
from loguru import logger

ideas = [
    {
        "title": "The Competence Trap: Why Being Great at Your Job Can Hurt You",
        "hook": "The better you are at your job, the more of it they give you — and the less they feel they need to pay you.",
        "angle": "Expose the competence trap: high performers become 'irreplaceable' which means they get loaded with work but denied promotions. Being irreplaceable sounds like a compliment — it's actually a cage.",
        "target_emotion": "recognition + quiet rage",
        "keywords": ["workplace psychology", "career", "promotion", "high performer", "office"],
        "predicted_score": 0.94,
    },
    {
        "title": "Your 3% Raise Was Actually a Pay Cut",
        "hook": "They gave you 3%. Inflation was 6%. They did the math and decided you should work for less than last year — and hoped you wouldn't notice.",
        "angle": "The psychology of the symbolic raise — a pacifier, not a reward. A raise below inflation isn't a raise. It's a polite pay cut with a bow on it.",
        "target_emotion": "betrayal + analytical vindication",
        "keywords": ["salary", "raise", "inflation", "workplace", "negotiation"],
        "predicted_score": 0.96,
    },
    {
        "title": "How Your Manager Steals Credit Without You Realizing",
        "hook": "Your manager didn't steal your idea. They waited for you to prove it worked — then took ownership of the result.",
        "angle": "The anatomy of workplace credit theft — it's a slow drip, not a single moment. 'We' instead of 'you' in meetings. Your name disappearing as the project climbs the hierarchy.",
        "target_emotion": "righteous anger + pattern recognition",
        "keywords": ["credit stealing", "workplace", "manager", "office politics", "career"],
        "predicted_score": 0.95,
    },
    {
        "title": "Every Fake Deadline Has This One Tell",
        "hook": "Your manager just said this is urgent. Here's the 30-second test for whether that's actually true.",
        "angle": "Manufactured urgency as a management control tool — the deadline that never had a reason, the crisis that evaporates after you cancel your evening. Urgency without consequence is a test of your boundaries, not your calendar.",
        "target_emotion": "empowerment + relief",
        "keywords": ["workplace boundaries", "manager", "urgency", "work-life balance", "office"],
        "predicted_score": 0.93,
    },
    {
        "title": "Corporate Loyalty Is a One-Way Street",
        "hook": "You've been loyal to this company for six years. Watch how long it takes them to let you go when the numbers change.",
        "angle": "Companies legally cannot return loyalty the way humans experience it. They cultivate it through language — 'family,' 'team,' 'we're in this together' — while maintaining zero structural loyalty. Loyalty to a company is a feeling. Loyalty to your career is a strategy.",
        "target_emotion": "grief + clarifying anger + forward agency",
        "keywords": ["corporate loyalty", "layoffs", "workplace", "career", "job security"],
        "predicted_score": 0.95,
    },
    {
        "title": "The Hidden Ranking System in Your Office",
        "hook": "There's a hidden ranking system in every office. How hard you work has almost nothing to do with where you land.",
        "angle": "Favoritism as an invisible layer over the formal performance system. Proximity to power, social compatibility, being seen vs. actually productive. The performance review measures what you did. The promotion decision measures who noticed.",
        "target_emotion": "recognition + strategic recalibration",
        "keywords": ["workplace favoritism", "office politics", "promotion", "career", "manager"],
        "predicted_score": 0.93,
    },
    {
        "title": "What 'You're Not Ready' Actually Means",
        "hook": "They said you're not ready for a promotion. Here's what that phrase actually means — and it's almost never what you think.",
        "angle": "Deconstruct the 'not ready' response. It usually means: we haven't budgeted for it, promoting you creates a backfill problem, or you're too useful where you are. If they can't give you the exact criteria for 'ready' in writing — it's a delay tactic, not a development plan.",
        "target_emotion": "clarifying insight + redirected energy",
        "keywords": ["promotion", "career growth", "workplace", "manager", "salary negotiation"],
        "predicted_score": 0.94,
    },
    {
        "title": "You're Not Lazy. You're Finally Working the Job You're Paid For.",
        "hook": "You're not disengaged. You're finally working the job you're actually being paid for.",
        "angle": "Acting your wage reframed — not disengagement but accurate calibration. Above-and-beyond effort is an unspoken negotiation the company accepts without matching. Giving 110% to a company paying for 80% isn't dedication. It's a subsidy — and you're the one funding it.",
        "target_emotion": "permission + relief + self-reclamation",
        "keywords": ["act your wage", "quiet quitting", "workplace", "work-life balance", "burnout"],
        "predicted_score": 0.96,
    },
    {
        "title": "The Moment a Company Decides It Doesn't Need to Keep You Happy",
        "hook": "There's a specific moment when a company decides they don't need to keep you happy anymore. Here's how to know when it's already happened.",
        "angle": "The behavioral signals of this shift: your input stops being solicited, your manager stops advocating for your requests, internal opportunities stop being surfaced to you. These aren't random — they're the withdrawal of retention effort. When they stop trying to keep you, that's your exit interview three months early.",
        "target_emotion": "clarity + preemptive control",
        "keywords": ["job security", "workplace", "career", "layoff signs", "manager"],
        "predicted_score": 0.94,
    },
    {
        "title": "There Are Two Jobs at Your Company. Nobody Told You About the Second One.",
        "hook": "There are two jobs in every office. The one on your job description — and the invisible one that actually determines your future.",
        "angle": "The invisible second job: relationship management, visibility cultivation, managing perceptions upward, emotional labor for leadership. The brilliant employee doing only Job 1 loses to the adequate employee who masters Job 2. No one mentions this in the interview. Everyone is evaluated on it from day one.",
        "target_emotion": "revelation + strategic empowerment",
        "keywords": ["office politics", "career", "workplace", "promotion", "visibility at work"],
        "predicted_score": 0.95,
    },
]

inserted = 0
for idea in ideas:
    existing = fetchone("SELECT id FROM ideas WHERE title = ?", (idea["title"],))
    if existing:
        logger.info(f"Already exists: {idea['title']}")
        continue
    import json
    execute(
        """INSERT INTO ideas (title, topic, topic_cluster, hook_angle, hook_style, emotional_trigger, why_watch, predicted_score, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'approved', datetime('now'))""",
        (
            idea["title"],
            idea["title"],
            "workplace_psychology",
            idea["hook"],
            "reframe",
            idea["target_emotion"],
            idea["angle"],
            idea["predicted_score"],
        ),
    )
    row = fetchone("SELECT id FROM ideas WHERE title = ?", (idea["title"],))
    logger.info(f"Inserted idea {row['id']}: {idea['title']}")
    inserted += 1

logger.info(f"Done. Inserted {inserted} new ideas.")
