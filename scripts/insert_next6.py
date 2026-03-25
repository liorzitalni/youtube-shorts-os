import sqlite3, json
from datetime import datetime

ideas = [
    (
        'The Narcissist Knows Exactly What They Are Doing',
        'Narcissistic intentionality and the myth of the oblivious abuser. Research by Back et al. shows narcissists have intact self-awareness about manipulative behavior — they score high on intentional deception measures, are aware others see them as entitled and manipulative, and choose to continue anyway because the cost-benefit calculates in their favor. The "they do not know any better" narrative is a comfort story. Awareness is not the barrier. Consequence is.',
        'dark_psychology',
        'The narcissist is not confused. They are not acting from unresolved pain without realizing it. They know exactly what they are doing. What they have calculated is that you will not leave.',
        'dark_revelation',
        'vindication and clarity — removes the last remaining excuse the viewer was holding onto',
        'Prod 27: 10 subs, 82.1% retention — channel best. Same audience, deepest cut yet. Most validating thing we can say to a narcissist survivor.',
        0.87, 0.97,
        json.dumps(['narcissist intentional manipulation research', 'narcissist knows what they are doing', 'Back narcissism self-awareness study'])
    ),
    (
        'The Person Who Made You Feel Crazy Was the Unstable One',
        'Projection and gaslighting in unstable personalities. When someone is internally chaotic — high emotional dysregulation, fragmented self-concept, impulsive reactivity — they project that chaos outward. Their partner starts questioning their own sanity. The confused, anxious, hypervigilant person in the relationship is not the unstable one — they are a stable person responding to genuine instability. The stability reads as rigidity. The confusion reads as craziness. It is a perceptual inversion.',
        'dark_psychology',
        'If you spent years feeling like you were losing your mind in a relationship, consider this: you were not the unstable one. You were a stable person living inside someone else instability trying to make it make sense.',
        'authority_subversion',
        'deep vindication — restores sanity to people who were made to doubt it',
        'Jealousy (92.2% retention), You Were Never Too Much (93.4%), Empathy target (100.9% rewatch). Vindication + reframe = highest retention formula on channel.',
        0.86, 0.97,
        json.dumps(['projection unstable partner psychology', 'gaslighting stable person made crazy', 'emotional dysregulation partner projection'])
    ),
    (
        'You Were Not In Love — You Were In Rescue Mode',
        'Savior complex and the difference between love and emotional caretaking. Rescue-mode relationships feel intensely like love but the object of the feeling is not the person — it is the project. The brain releases oxytocin and dopamine in response to progress, not connection. When the person stops needing rescue — gets better, becomes independent, heals — the relationship often collapses. Not because love died. Because the function ended.',
        'relationship_psych',
        'The most intense feeling you have ever had in a relationship might not have been love. It might have been the feeling of being needed. They are not the same thing — and one of them ends when the other person gets better.',
        'trusted_concept_attack',
        'identity-level reframe — challenges what the viewer thought was their deepest love',
        'Prod 34 (Savior Complex): 78.3% retention, 3.3% like rate, 2 subs. Natural sequel — same audience, deeper cut.',
        0.85, 0.96,
        json.dumps(['savior complex not love psychology', 'rescue mode relationships', 'caretaking vs love psychology'])
    ),
    (
        'The Relationship That Left No Bruises',
        'Covert emotional abuse and the absence of visible evidence. Physical abuse leaves marks. Emotional and psychological abuse leaves nothing visible — no bruises, no hospital visits, no police reports. The victim cannot explain what happened because the abuse was cumulative, subtle, deniable. Covert abusers choose tactics impossible to prove — tone, silence, withdrawal, implication, facial expressions. The lack of evidence is not proof that nothing happened. It is proof of how sophisticated the abuse was.',
        'dark_psychology',
        'The most sophisticated abuse leaves no evidence. No bruises. No messages you can screenshot. No witnesses. Just a person who cannot explain why they feel so broken — because everything that broke them was designed to be deniable.',
        'dark_revelation',
        'profound vindication — speaks to survivors who were told nothing happened because there was no proof',
        'Coercive Control (prod 24): 3 subs, massive search volume. This is the companion piece — same cluster, the covert angle. Trending March 2026.',
        0.86, 0.97,
        json.dumps(['covert emotional abuse no evidence', 'psychological abuse invisible signs', 'deniable abuse tactics psychology'])
    ),
    (
        'The Emptiness Is Not Depression — It Is Disconnection',
        'Anhedonia vs existential emptiness. Clinical depression involves low mood and biological dysfunction. But a different emptiness comes from chronic disconnection from authentic self. People who spent years performing a version of themselves to please others or survive trauma often reach a point where nothing feels meaningful. Not because they are depressed but because they have been living someone else life. The emptiness is not a symptom to medicate. It is a signal.',
        'self_awareness',
        'If you have been feeling empty for years but it does not quite feel like depression, it might not be. It might be what happens when you have spent so long living for everyone else that you have completely lost the thread back to yourself.',
        'authority_subversion',
        'names something millions feel but cannot diagnose — immediately shareable',
        'Why Achievement Feels Empty trending up. Google Trends: emptiness + disconnection spiking March 2026. Same wound formula as channel leader prod 10.',
        0.84, 0.95,
        json.dumps(['emptiness not depression psychology', 'chronic disconnection from self', 'existential emptiness vs depression'])
    ),
    (
        'Your Attachment Style Was Set Before You Were 2 Years Old',
        'Early attachment formation and the Strange Situation experiments. Mary Ainsworth established that attachment style is largely determined by age 18 months, based on reliability and sensitivity of primary caregiver responses. The infant brain builds an internal working model — a template for how relationships work, whether people can be trusted, whether distress will be soothed or ignored. This model runs automatically in adult relationships. When you react with anxiety, avoidance, or chaos in intimacy, you are running a program installed before you had language.',
        'relationship_psych',
        'Your attachment style — why you chase, why you pull away, why you self-sabotage in love — was set before you were 2 years old. You have been running that same program in every relationship since.',
        'dark_revelation',
        'reframe that makes viewers see relationship patterns as a system not a character flaw',
        'Attachment content is fastest-growing cluster. Prod 29 (anxious attachment): 3 subs. This is the origin story. Ainsworth strange situation massively searched.',
        0.85, 0.96,
        json.dumps(['attachment style formed before age 2', 'Ainsworth strange situation psychology', 'early attachment internal working model'])
    ),
]

conn = sqlite3.connect('data/shorts_os.db')
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
inserted = []
for t in ideas:
    conn.execute('''INSERT INTO ideas (title, topic, topic_cluster, hook_angle, hook_style, emotional_trigger,
                    why_watch, originality_score, predicted_score, source_patterns, status, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                 (t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],'approved',now,now))
    inserted.append(conn.execute('SELECT last_insert_rowid()').fetchone()[0])
conn.commit()
conn.close()
print('Inserted IDs:', inserted)
