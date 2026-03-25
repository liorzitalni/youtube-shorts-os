import sqlite3, json
from datetime import datetime

ideas = [
    {
        'title': "People Pleasers Are Not Nice — They Are Scared",
        'topic': "Fawn response as a trauma adaptation (Pete Walker). People pleasing is not a personality trait — it is a nervous system survival strategy developed in environments where conflict was dangerous. The brain learned that making others comfortable keeps you safe. In adulthood, it reads as niceness but functions as chronic self-abandonment. The cost: no authentic relationships, resentment buildup, vulnerability to exploitation.",
        'topic_cluster': 'dark_psychology',
        'hook_angle': "People pleasers are not kind. They are people who learned that keeping others comfortable was the only way to stay safe. That is not generosity. That is survival.",
        'hook_style': 'trusted_concept_attack',
        'emotional_trigger': 'recognition and reframe — the viewer has been calling their fear kindness their whole life',
        'why_watch': "Prod 2 (Your Empathy Is Being Used Against You) has 4.4% like rate — best quality engagement on channel. This is the same wound from a different angle. Fawn response is massively searched.",
        'originality_score': 0.82,
        'predicted_score': 0.95,
        'source_patterns': json.dumps(['fawn response psychology', 'people pleasing trauma', 'Pete Walker fawn']),
        'status': 'approved',
    },
    {
        'title': "Why You Cannot Stop Thinking About Someone Who Hurt You",
        'topic': "Rumination and the Zeigarnik effect. The brain treats unresolved emotional experiences like open loops — it keeps returning to them trying to close the file. When someone hurts you and there is no resolution, no acknowledgment, no closure, the hippocampus flags the memory as incomplete and the prefrontal cortex keeps scheduling review. This is why closure with a narcissist is neurologically impossible — they will never give you what your brain needs to close the loop.",
        'topic_cluster': 'dark_psychology',
        'hook_angle': "Your brain is not torturing you when you cannot stop thinking about someone who hurt you. It is trying to finish something. The problem is they will never give you what you need to finish it.",
        'hook_style': 'dark_revelation',
        'emotional_trigger': 'relief and recognition — finally an explanation for something deeply shameful',
        'why_watch': "Loneliness + narcissism = top two performing clusters. This bridges both. Enormous search volume: why cant I stop thinking about my ex, no closure narcissist.",
        'originality_score': 0.83,
        'predicted_score': 0.95,
        'source_patterns': json.dumps(['Zeigarnik effect rumination', 'closure narcissist impossible', 'intrusive thoughts psychology']),
        'status': 'approved',
    },
    {
        'title': "Silent Treatment Is Not Immaturity — It Is Abuse",
        'topic': "Stonewalling as psychological violence. The silent treatment activates the same neural pathways as physical pain (Eisenberger et al.). Being ignored by someone whose approval matters triggers the anterior cingulate cortex — the brain region that processes both social exclusion and bodily injury. Used deliberately, the silent treatment is a control mechanism: it punishes the target for asserting needs without the abuser having to articulate anything.",
        'topic_cluster': 'dark_psychology',
        'hook_angle': "When someone gives you the silent treatment, your brain processes it the same way it processes being hit. It is not immaturity. It is a calculated weapon.",
        'hook_style': 'authority_subversion',
        'emotional_trigger': 'validation + controlled outrage — names something the viewer endured without language for it',
        'why_watch': "Stonewalling prod 28 got 74 views but zero engagement — the angle was wrong. This reframe (abuse, not immaturity) is more provocative and more shareable. High search volume.",
        'originality_score': 0.78,
        'predicted_score': 0.93,
        'source_patterns': json.dumps(['silent treatment psychological abuse', 'stonewalling pain brain', 'Eisenberger social exclusion']),
        'status': 'approved',
    },
    {
        'title': "Your Standards Are Not High — You Are Traumatized",
        'topic': "Hypervigilance and relational threat detection. People with trauma histories develop hair-trigger threat detection in relationships — not because they have high standards but because their nervous system learned to treat intimacy as danger. They reject partners for small signals that the unconscious reads as early warning signs of past abuse patterns. This is often misread as being picky. It is actually a sophisticated but exhausting protection system.",
        'topic_cluster': 'self_awareness',
        'hook_angle': "If you keep leaving relationships over small things that feel like deal-breakers, it is not because your standards are high. Your nervous system is pattern-matching for danger.",
        'hook_style': 'authority_subversion',
        'emotional_trigger': 'relief and reframe — removes shame from a behavior the viewer has been judged for',
        'why_watch': "Self-awareness wound formula — same as prod 10 (1,245 views, channel leader). The shame-removal hook is highly shareable.",
        'originality_score': 0.81,
        'predicted_score': 0.94,
        'source_patterns': json.dumps(['trauma hypervigilance relationships', 'nervous system threat detection dating', 'high standards trauma response']),
        'status': 'approved',
    },
    {
        'title': "Gaslighting Works Because of How Memory Actually Works",
        'topic': "Memory reconsolidation and gaslighting neuroscience. Human memory is not a recording — it is reconstructed every time it is recalled, and it can be overwritten during that reconstruction window. Gaslighters exploit this: by introducing doubt immediately after an event, during the reconsolidation window, they can literally alter the stored memory. The target does not just doubt their interpretation — they doubt the actual events.",
        'topic_cluster': 'dark_psychology',
        'hook_angle': "Gaslighting does not just make you doubt your interpretation of events. It rewrites the memory itself. Your brain is not weak — it is being exploited at the neurological level.",
        'hook_style': 'dark_revelation',
        'emotional_trigger': 'vindication — the viewer has been told they are crazy; now they understand the mechanism',
        'why_watch': "Gaslighting is peak search territory. The neuroscience angle makes it shareable. Prod 40 (self-trust) already validated this audience.",
        'originality_score': 0.84,
        'predicted_score': 0.95,
        'source_patterns': json.dumps(['gaslighting memory reconsolidation', 'memory overwriting psychology', 'gaslighting neuroscience']),
        'status': 'approved',
    },
    {
        'title': "Emotional Immaturity Looks Exactly Like Confidence",
        'topic': "Alexithymia and emotional avoidance disguised as stoicism. Emotionally immature people often present as confident, decisive, and unaffected — because they are genuinely not accessing their emotional state. This is not emotional regulation. It is emotional absence. Partners mistake the absence of visible distress for emotional security.",
        'topic_cluster': 'relationship_psych',
        'hook_angle': "The most emotionally immature people you will ever meet do not look weak. They look confident, calm, and completely unbothered. That is not emotional strength. That is emotional absence.",
        'hook_style': 'trusted_concept_attack',
        'emotional_trigger': 'recognition — the viewer has dated someone like this and could not understand why it felt empty',
        'why_watch': "Attachment + narcissism audience overlap. The unbothered = emotionally unavailable reframe is highly shareable.",
        'originality_score': 0.79,
        'predicted_score': 0.92,
        'source_patterns': json.dumps(['emotional immaturity psychology', 'alexithymia relationships', 'emotionally unavailable confidence']),
        'status': 'approved',
    },
    {
        'title': "Loneliness Is Not About Being Alone — It Is About Being Unseen",
        'topic': "Mattering and invisibility theory (Rosenberg & McCullough). The most painful form of loneliness is not solitude — it is being in a room full of people and feeling invisible. Mattering theory: humans have a core need to feel they are noticed, important to others, and that they would be missed. When this need is unmet — emotionally unavailable parents, dismissive partners — the result is loneliness-in-company, more painful than physical isolation.",
        'topic_cluster': 'self_awareness',
        'hook_angle': "The loneliest feeling is not being alone. It is being in the room with the people who are supposed to love you and feeling completely invisible to them.",
        'hook_style': 'bold_claim',
        'emotional_trigger': 'deep recognition — this names an experience most people have never been able to articulate',
        'why_watch': "Loneliness is the top performing cluster (prod 10: 1,245 views). This takes it deeper and more personal. The invisibility angle is more emotionally charged than the neuroscience angle.",
        'originality_score': 0.83,
        'predicted_score': 0.96,
        'source_patterns': json.dumps(['loneliness invisibility psychology', 'mattering theory Rosenberg', 'lonely in company psychology']),
        'status': 'approved',
    },
    {
        'title': "Why You Apologize for Things That Are Not Your Fault",
        'topic': "Over-apologizing as a fawn trauma response and chronic shame. Excessive apologizing is not politeness — it is a symptom of chronic shame and a nervous system that learned that taking preemptive blame reduces conflict. In environments where others were volatile or critical, anticipating their anger by apologizing first was a survival strategy. In adulthood it signals low self-worth and perpetuates the internal belief that your existence is an imposition.",
        'topic_cluster': 'self_awareness',
        'hook_angle': "If you constantly apologize for things that are not your fault, you did not learn to be polite. You learned that taking the blame first stops the anger from coming.",
        'hook_style': 'origin_story',
        'emotional_trigger': 'deep recognition + vindication — names a behavior the viewer is ashamed of and explains the childhood origin',
        'why_watch': "Fake Apologies as weapons (prod 39) did 620 views. This is the mirror: why victims over-apologize. Same search territory, opposite perspective, high personal relevance.",
        'originality_score': 0.80,
        'predicted_score': 0.94,
        'source_patterns': json.dumps(['over apologizing psychology', 'apologizing trauma response', 'chronic apology shame']),
        'status': 'approved',
    },
]

conn = sqlite3.connect('data/shorts_os.db')
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
inserted = []
for idea in ideas:
    conn.execute('''INSERT INTO ideas (title, topic, topic_cluster, hook_angle, hook_style, emotional_trigger,
                    why_watch, originality_score, predicted_score, source_patterns, status, created_at, updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                 (idea['title'], idea['topic'], idea['topic_cluster'], idea['hook_angle'], idea['hook_style'],
                  idea['emotional_trigger'], idea['why_watch'], idea['originality_score'], idea['predicted_score'],
                  idea['source_patterns'], idea['status'], now, now))
    inserted.append(conn.execute('SELECT last_insert_rowid()').fetchone()[0])
conn.commit()
conn.close()
print('Inserted IDs:', inserted)
