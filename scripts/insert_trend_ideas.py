import sqlite3, json
from datetime import datetime

ideas = [
    {
        "title": "One Sentence Ended Her Oscar Night",
        "topic": "Halo Effect collapse psychology — the same cognitive bias that builds a celebrity up becomes the mechanism that destroys them. One perceived act of cruelty (Jessie Buckley demanding her now-husband give up his cats to stay with her) triggers a complete reversal of prior goodwill. Psychological research by Nisbett and Wilson shows the halo effect operates unconsciously — we assign global positive traits based on one salient feature, and its collapse is equally disproportionate. Oscars 2026 context: Buckley is a frontrunner for Best Actress and this single story triggered massive backlash hours before the ceremony.",
        "topic_cluster": "social_psychology",
        "hook_angle": "It took one sentence for the internet to go from loving her to hating her. That is not justice. That is the halo effect running in reverse — and your brain does it to everyone.",
        "hook_style": "viral_moment_lens",
        "emotional_trigger": "intellectual reframe — makes viewer question how fast they judged",
        "why_watch": "Oscars air tonight March 15. Peak search traffic on Buckley name. Halo effect is universally relatable. Psychology is non-obvious and slightly uncomfortable.",
        "originality_score": 0.76,
        "predicted_score": 0.95,
    },
    {
        "title": "They Were Never Staying — The Psychology of Sledging",
        "topic": "Sledging — entering a relationship with a premeditated exit plan by spring — maps directly onto subclinical psychopathy and dark triad trait expression. The sledger treats the partner as a utility object: warmth, companionship, sex. Research by Paulhus and Williams on the dark triad shows subclinical psychopathy specifically predicts short-term mating strategies with zero reciprocal investment. The spring breakup wave is happening in real-time as March 2026 arrives.",
        "topic_cluster": "dark_psychology",
        "hook_angle": "They chose you for winter. They were always leaving in spring. That is not a coincidence — it is a pattern psychology has a name for.",
        "hook_style": "dark_revelation",
        "emotional_trigger": "recognition and controlled anger — viewer has likely experienced this",
        "why_watch": "Spring breakup wave happening right now. Highly relatable for 18-35 demo. Dark triad angle is on-brand. Evergreen after the trend fades.",
        "originality_score": 0.80,
        "predicted_score": 0.93,
    },
    {
        "title": "Why BTS Fans Cannot Stop — The Slot Machine Your Brain Cannot Resist",
        "topic": "BTS ARIRANG album release is triggering parasocial obsession at scale — Spotify Easter egg hunts, Google quests, +2250% search growth. The psychological mechanism is variable ratio reinforcement (Skinner) — the same schedule that makes slot machines impossible to stop. K-pop fan engagement is engineered around this: unpredictable content drops, hidden messages, exclusive unlocks. Each discovery triggers dopamine. The unpredictability makes the behavior more resistant to extinction than any fixed schedule. Fans are not choosing to be obsessed — they are being behaviorally conditioned.",
        "topic_cluster": "dark_psychology",
        "hook_angle": "BTS is trending number one globally right now. Millions of fans cannot explain why they cannot stop. Your brain can. It is the same mechanism that makes gambling addictive.",
        "hook_style": "dark_revelation",
        "emotional_trigger": "recognition — fans feel seen but slightly exposed",
        "why_watch": "Trending number 1 on Google today. Broad K-pop audience crossover. Variable reward psychology is universally compelling. Non-fans find behavioral science angle fascinating.",
        "originality_score": 0.78,
        "predicted_score": 0.92,
    },
    {
        "title": "Leaving You on the Mountain Was Not an Accident",
        "topic": "Alpine divorce — abandoning a partner in a physically vulnerable situation — is coercive control that psychology classifies under intimate partner power dynamics. The 1893 short story origin reveals this is not new. Modern cases involve using terrain and physical disadvantage to establish dominance and induce fear. Research on coercive control (Stark, 2007) shows physical vulnerability is a key tool in the control cycle — it communicates that the partner is dependent and powerless. A viral TikTok moment with 3M+ views opened a cultural conversation about what counts as abuse when there are no visible bruises.",
        "topic_cluster": "dark_psychology",
        "hook_angle": "Leaving your partner on a dangerous hike has a name, a 130-year history, and a psychology. It is not an accident. It is a power move — and the research is disturbing.",
        "hook_style": "dark_revelation",
        "emotional_trigger": "controlled outrage and recognition",
        "why_watch": "Alpine divorce viral video at 3M+ views. Coercive control angle is dark and on-brand. Connects to broader relationship abuse conversation. Strong comment-driver.",
        "originality_score": 0.82,
        "predicted_score": 0.93,
    },
]

conn = sqlite3.connect("data/shorts_os.db")
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
inserted = []
for idea in ideas:
    conn.execute("""
        INSERT INTO ideas (title, topic, topic_cluster, hook_angle, hook_style, emotional_trigger, why_watch,
                           originality_score, predicted_score, source_patterns, status, created_at, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (idea["title"], idea["topic"], idea["topic_cluster"], idea["hook_angle"], idea["hook_style"],
          idea["emotional_trigger"], idea["why_watch"], idea["originality_score"], idea["predicted_score"],
          "[]", "approved", now, now))
    inserted.append(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
conn.commit()
conn.close()
print("Inserted IDs:", inserted)
