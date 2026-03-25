import sqlite3, json
from datetime import datetime

ideas = [
    (
        'The Narcissist\'s Love Was Never About You',
        'Love bombing as strategic grooming, not genuine emotion. Research by Durvasula and Hotchkiss shows that the idealization phase in narcissistic relationships serves a functional purpose: it establishes the target as a high-value source of narcissistic supply while creating a bond the narcissist can later exploit. The intense attention, affection, and connection the victim felt was real — but its object was the narcissist\'s own needs, not the victim. When the mask drops, victims grieve a relationship that was only real on one side. The love bombing was the lure. The real relationship began when it stopped.',
        'dark_psychology',
        'The most intense love you have ever felt might not have been real. Not because you imagined it — but because it was designed to make you feel it. The narcissist\'s idealization phase is not romance. It is recruitment.',
        'dark_revelation',
        'grief-to-clarity — shatters the idealized memory that keeps victims trapped',
        'Directly extends top converter (Narcissists Scan for One Trait, 10 subs). Love bombing is massively searched. Same audience, next layer of insight.',
        0.88, 0.97,
        json.dumps(['narcissist love bombing strategy', 'idealization phase grooming', 'narcissistic supply recruitment'])
    ),
    (
        'Your Gut Was Right the First Time',
        'Intuition as pre-conscious threat detection. Research by Ap Dijksterhuis on unconscious cognition shows that the gut feeling that something is wrong in a relationship often precedes conscious awareness by weeks or months. The nervous system processes social signals — microexpressions, tonal inconsistencies, behavioral patterns — below the threshold of conscious thought. Trauma survivors and people in covert abuse situations routinely report that they knew something was wrong early on but were talked out of it. Gaslighting and rationalization work by overriding accurate gut signals. The intuition was correct. The relationship taught them not to trust it.',
        'dark_psychology',
        'That feeling you had on the third date — the one you talked yourself out of — your gut was right. The relationship did not teach you that your instincts are wrong. The person in it did.',
        'vindication',
        'deep vindication + self-trust restoration — extremely shareable',
        'Extends covert abuse cluster. The "ignored gut feeling" is universally relatable for survivors. High comment/share potential. Evergreen.',
        0.86, 0.96,
        json.dumps(['gut feeling intuition psychology', 'unconscious threat detection relationships', 'gaslighting overrides intuition'])
    ),
    (
        'DARVO: When the Abuser Becomes the Victim',
        'DARVO — Deny, Attack, Reverse Victim and Offender — is a documented manipulation tactic identified by Jennifer Freyd in her betrayal trauma research. When confronted with harmful behavior, the abusive person denies it happened, attacks the person who raised it, then positions themselves as the real victim of the confrontation. The accuser becomes the aggressor. The pattern is so consistent and effective that it has a clinical acronym. Victims leave the confrontation apologizing for something that was done to them. DARVO is not accidental — it is a predictable, patterned response that suppresses accountability while inverting reality.',
        'dark_psychology',
        'There is a name for what happens when you confront someone about hurting you and somehow end up apologizing to them. It is called DARVO. It is a documented manipulation tactic — and you were not imagining it.',
        'dark_revelation',
        'vindication + naming the unnamed — extremely powerful for survivors who lived this',
        'High search volume for DARVO since 2024. Psychology-forward dark revelation. Gives victims clinical validation for something they experienced but never had words for.',
        0.87, 0.97,
        json.dumps(['DARVO manipulation tactic psychology', 'deny attack reverse victim offender', 'Freyd betrayal trauma DARVO'])
    ),
    (
        'Why You Keep Attracting the Same Person',
        'Repetition compulsion and trauma reenactment. Freud identified the repetition compulsion — the unconscious drive to recreate unresolved emotional situations from the past. Van der Kolk\'s research expanded this: trauma survivors do not seek out painful relationships because they enjoy pain, but because the unconscious mind is attempting to master an unresolved wound by recreating the context in which it occurred. The familiar dynamic feels like home even when it is harmful. The pattern is not a character flaw or bad luck. It is the nervous system trying to rewrite an old story — in the wrong venue.',
        'relationship_psych',
        'You keep ending up with the same kind of person. You think it is bad luck, or you think something is wrong with you. It is neither. Your nervous system is trying to finish a story that started long before you met any of them.',
        'reframe',
        'identity-level reframe — removes self-blame, creates deep recognition',
        'Trauma reenactment is massively searched. Connects directly to attachment content (3 subs) and abuse victim return (315% rewatch). High repeat-viewer potential.',
        0.86, 0.96,
        json.dumps(['repetition compulsion trauma reenactment', 'why attract same type person psychology', 'van der Kolk repetition compulsion'])
    ),
    (
        'Why Leaving Does Not Feel Like Freedom',
        'Post-separation trauma response and the emptiness after escape. Research on trauma bonding shows that when the intermittent reinforcement cycle ends — whether by the victim leaving or the abuser discarding — the brain experiences a withdrawal syndrome physiologically identical to ending an addiction. No conflict. No reconciliation rush. No tension cycle. The nervous system, calibrated to hypervigilance and intermittent reward, reads calm as wrong. Victims who leave describe not relief but numbness, flatness, disorientation. They miss the abuser. Not because they love them — but because the brain was trained to function inside that cycle.',
        'dark_psychology',
        'You finally left. And instead of freedom, you feel empty. You miss them. You wonder if you made a mistake. This is not love. This is what withdrawal from a trauma bond feels like. Your brain was addicted to the cycle — not the person.',
        'validation_reframe',
        'profound validation — speaks to the most confusing part of escape: missing the abuser',
        'Directly follows trauma bond (prev. video). Why abuse victims return hit 315% rewatch. This is the companion piece: the internal experience of leaving. Massively searched.',
        0.87, 0.97,
        json.dumps(['trauma bond withdrawal leaving abuser', 'why miss abuser after leaving psychology', 'post separation trauma response'])
    ),
    (
        'The Apology That Was Actually an Attack',
        'Non-apology psychology and covert retaliation through apology language. Research on accountability avoidance identifies several pseudo-apology structures that function as continued aggression: the conditional apology ("I am sorry you feel that way"), the blame-shift apology ("I am sorry I reacted like that, but if you had not..."), and the martyrdom apology ("Fine, I am always the bad guy"). Each structure mimics the form of apology while denying wrongdoing, reassigning fault, or positioning the apologizer as victimized by the expectation of accountability. Recipients feel worse after the apology than before. That is not an accident. That is the function.',
        'dark_psychology',
        'There is a type of apology that is designed to make you feel worse than before you asked for it. You have heard it. Psychology has catalogued every version of it. None of them are accidents.',
        'dark_revelation',
        'recognition + controlled anger — instantly relatable, high share potential',
        'Non-apology is one of the most searched relationship psychology terms. Extends dark psychology cluster. High comment potential — everyone has a story.',
        0.85, 0.95,
        json.dumps(['fake apology psychology', 'non-apology apology narcissist', 'apology as attack covert aggression'])
    ),
    (
        'You Were Not Too Sensitive — You Were Accurately Detecting Danger',
        'High sensitivity as calibrated threat detection, not emotional weakness. Research by Elaine Aron on Highly Sensitive People (HSP) and trauma research by Peter Levine shows that heightened emotional sensitivity in interpersonal contexts often reflects an accurate nervous system response to real threat signals — subtle aggression, inconsistency, contempt — that less attuned people miss. Partners and environments routinely pathologize this sensitivity as a character flaw to suppress the accurate threat detection. "You are too sensitive" is one of the most documented gaslighting scripts in coercive control literature. The sensitivity was not the problem. The environment that required it was.',
        'dark_psychology',
        'Every time you were told you were too sensitive, they were telling you that your ability to detect what they were doing to you was inconvenient. Your sensitivity was not the problem. It was the most accurate thing about you.',
        'vindication',
        'deep vindication + identity restoration — among the most shareable reframes for survivors',
        'HSP and sensitivity content is surging on TikTok/YouTube 2026. Directly validates one of the most common gaslighting scripts. High emotional resonance. Evergreen.',
        0.87, 0.96,
        json.dumps(['too sensitive gaslighting psychology', 'highly sensitive person HSP threat detection', 'sensitivity as accurate perception trauma'])
    ),
    (
        'Emotional Unavailability Is Not a Personality — It Is a Defense',
        'Emotional unavailability as a learned protective strategy, not a fixed trait. Attachment research by Bartholomew and Horowitz identifies dismissive-avoidant attachment as a strategy developed in response to consistently unmet attachment needs — the child learned that needing connection produces pain, so the need was suppressed. The adult who is emotionally unavailable is not broken or incapable of intimacy. They are protecting themselves from the pain that intimacy caused early on. The tragedy: the strategy that protected them from pain in childhood creates the very abandonment they fear in adulthood. Emotional unavailability pushes away the connection the person is terrified to lose.',
        'relationship_psych',
        'The emotionally unavailable person in your life is not broken. They are not incapable of love. They are protecting themselves from something that happened long before you arrived. The wall was not built to keep you out. It was built to survive.',
        'reframe',
        'empathy reframe — changes how viewer sees avoidant partners, creates compassion + clarity',
        'Avoidant attachment is one of the highest-traffic psychology terms. Builds on anxious attachment video (3 subs). Pairs perfectly with channel formula.',
        0.84, 0.95,
        json.dumps(['emotional unavailability avoidant attachment defense', 'dismissive avoidant attachment strategy psychology', 'emotionally unavailable person childhood wound'])
    ),
    (
        'Manipulation Does Not Always Look Like Manipulation',
        'Covert manipulation tactics that bypass conscious detection. Research on social influence and dark triad behavior identifies a cluster of manipulation tactics that are specifically designed to avoid detection: love withdrawal as punishment (not explicit threat), strategic incompetence to offload labor, feigned vulnerability to activate caretaking, and selective memory lapses to escape accountability. Unlike overt manipulation, these tactics allow the perpetrator to maintain deniability while achieving the same outcomes. The victim cannot name what is happening because nothing happened. That is the design. The manipulation that is hardest to escape is the kind that cannot be pointed to.',
        'dark_psychology',
        'The manipulation you experienced may not have had a face. No screaming. No obvious cruelty. Just a slow confusion about what was real — and a growing sense that everything was somehow your fault. That is the most sophisticated kind.',
        'dark_revelation',
        'recognition of invisible manipulation — names the hardest form to prove or escape',
        'Covert manipulation is a massive search cluster. Extends the no-evidence abuse content. High share potential — survivors find language for what they lived.',
        0.86, 0.96,
        json.dumps(['covert manipulation tactics psychology', 'manipulation without obvious abuse', 'strategic incompetence manipulation dark triad'])
    ),
    (
        'Hypervigilance Is Not Anxiety — It Is Memory',
        'Hypervigilance as a trauma-adaptive response, not a disorder. Van der Kolk and Bessel research on PTSD shows that the hypervigilant state — scanning for threat, difficulty relaxing, startle response, reading micro-expressions — is not a malfunction. It is a nervous system that learned that danger arrives without warning and that not noticing it has catastrophic consequences. In a safe environment, hypervigilance reads as anxiety or paranoia. But the behavior was acquired in an environment where it was necessary. The person is not overreacting. They are reacting to an accurate historical record. The nervous system did not get the memo that the environment changed.',
        'self_awareness',
        'If you are always waiting for something to go wrong — always scanning, always tense, always braced — that is not anxiety. That is a nervous system that learned to survive. It saved you once. It just has not been told that it does not have to anymore.',
        'reframe',
        'deep recognition + compassion reframe — reframes "anxiety" as adaptive survival response',
        'Hypervigilance is trending in trauma content. Massively relatable for abuse survivors. Reframes pathology as survival — consistent with channel formula. Highly shareable.',
        0.85, 0.96,
        json.dumps(['hypervigilance trauma response not anxiety', 'nervous system hypervigilance survival', 'van der Kolk hypervigilance PTSD adaptation'])
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
