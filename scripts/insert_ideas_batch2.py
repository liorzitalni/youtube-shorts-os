import sqlite3
from datetime import datetime

ideas = [
    {
        "title": "You Are Grieving a Version of Yourself You Have Not Met Yet",
        "topic": "Anticipatory nostalgia — longing for a future self you cannot yet access. Research by Sedikides on nostalgia shows it is not exclusively backward-looking; people experience nostalgia for imagined future states ('prospective nostalgia'). The 'Sunshine Boy' TikTok trend (Rihanna's Kiss It Better) captures this: people grieving their summer/warmer self during winter — not a past self, but an anticipated identity they feel cut off from. This connects to seasonal affective patterns, identity foreclosure, and the psychology of self-discontinuity. The insight: what feels like nostalgia for the past is often grief for a self you are not yet allowed to be.",
        "topic_cluster": "self_awareness",
        "hook_angle": "That feeling when you hear a summer song in winter and something in you aches — that is not nostalgia. You are grieving a version of yourself you have not met yet. Psychology has a name for it.",
        "hook_style": "reframe",
        "emotional_trigger": "deep recognition and melancholy — universally felt but never named",
        "why_watch": "Rihanna Sunshine Boy audio trending on TikTok now. Anticipatory nostalgia is deeply relatable for 18-35. The reframe from past-nostalgia to future-self grief is counterintuitive and emotionally resonant. Evergreen after trend.",
        "originality_score": 0.82,
        "predicted_score": 0.93,
    },
    {
        "title": "The Trauma Bond Cycle: Why Your Brain Will Not Let You Leave",
        "topic": "Trauma bonding neurochemistry — the intermittent reinforcement of abuse creates a neurochemical dependency indistinguishable from addiction. Bessel van der Kolk's research shows that the stress hormones released during conflict (cortisol, adrenaline) followed by reconciliation (oxytocin, dopamine) create a powerful bonding cycle. The brain learns to associate the abuser with relief from the very pain they cause. This is why logic, advice, and even knowing the relationship is harmful does not produce escape. The cycle: tension buildup → incident → reconciliation → honeymoon → tension buildup. Each reconciliation phase deepens the neurological bond.",
        "topic_cluster": "dark_psychology",
        "hook_angle": "You are not weak for staying. Your brain has been chemically conditioned to need the person who is hurting you. That is not a character flaw — it is neuroscience.",
        "hook_style": "validation_reframe",
        "emotional_trigger": "profound validation — removes self-blame, explains an experience millions cannot articulate",
        "why_watch": "Directly feeds the audience already watching Alpine Divorce and Sledging videos. Neurochemical explanation is credible and non-obvious. High comment potential — people share personal stories. Evergreen.",
        "originality_score": 0.75,
        "predicted_score": 0.94,
    },
    {
        "title": "Narcissists Do Not Choose You Randomly — Here Are the Exact Traits They Hunt",
        "topic": "Narcissistic victim selection is not random — research by Durvasula and others identifies specific trait clusters that narcissists (high in entitlement, low in empathy) systematically target: high empathy, external locus of control, people-pleasing tendencies, fear of abandonment, strong sense of loyalty, and boundary ambiguity. These traits signal to a narcissist that the target will tolerate mistreatment, provide narcissistic supply, and not leave easily. The cruel irony: the qualities that make someone a good partner — empathy, loyalty, commitment — are the exact traits that make them a narcissist's preferred target.",
        "topic_cluster": "dark_psychology",
        "hook_angle": "Narcissists do not choose people at random. They are scanning for a very specific set of traits. The cruelest part — every trait they look for is something good in you.",
        "hook_style": "dark_revelation",
        "emotional_trigger": "recognition, reframe of victimhood — turns shame into understanding",
        "why_watch": "Highest-scoring untouched backlog idea. Dark psychology is the channel's strongest performer. The 'good traits as target traits' reframe is non-obvious and emotionally powerful. Extremely high comment and share potential.",
        "originality_score": 0.78,
        "predicted_score": 0.94,
    },
    {
        "title": "Silence Is Not Neutral — It Is a Weapon",
        "topic": "Stonewalling psychology — the Gottman Institute's research identifies stonewalling (withdrawal, silence, emotional shutdown) as one of the Four Horsemen predictors of relationship dissolution, more damaging than fighting. Physiologically, the stonewalling partner's heart rate drops while the receiving partner's spikes — creating a power inversion through apparent passivity. Silence in conflict is not neutral: it communicates contempt, withholds resolution, and forces the other person to pursue, which reinforces the dynamic. Research shows that recipients of stonewalling experience it as more emotionally painful than verbal aggression.",
        "topic_cluster": "relationship_psych",
        "hook_angle": "When someone goes silent in a fight, it feels like they are doing nothing. They are not. Silence in conflict is one of the most studied and destructive tactics in relationship psychology — and it is almost never passive.",
        "hook_style": "reframe",
        "emotional_trigger": "recognition and controlled anger — many viewers have experienced this and never had language for it",
        "why_watch": "Pairs perfectly with the Sledging and Alpine Divorce content already live. Gottman research is highly credible. The 'silence as active weapon' reframe stops scrollers. Extremely high relatability for 18-35.",
        "originality_score": 0.72,
        "predicted_score": 0.92,
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
