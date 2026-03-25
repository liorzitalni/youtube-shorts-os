import sqlite3, json
from datetime import datetime

ideas = [
    (
        'The Narcissist\'s Silent Treatment Is a Punishment, Not Withdrawal',
        'Silent treatment as calculated punishment in narcissistic relationships. Research on narcissistic aggression distinguishes between genuine emotional withdrawal — which occurs in avoidant attachment — and the silent treatment deployed by narcissists. In avoidant withdrawal, the person is managing overwhelm. In narcissistic silent treatment, the goal is punishment, control, and inducing anxiety in the target to force pursuit. The narcissist is not emotionally flooded — studies show their physiological arousal drops during silent treatment while the recipient spikes. They are watching. They are waiting for pursuit. The silence is not absence. It is pressure.',
        'dark_psychology',
        'When a narcissist goes silent, they are not overwhelmed. They are not processing. They are watching to see how long it takes you to break. The silent treatment is not withdrawal. It is a punishment designed to teach you what happens when you disappoint them.',
        'dark_revelation',
        'rage-to-clarity — names something survivors experienced but could not explain',
        'Direct extension of #1 converter (Narcissists Scan for One Trait, 11 subs). Silent treatment is one of the most searched narcissism topics. High comment potential — this is personally identifiable for survivors.',
        0.89, 0.98,
        json.dumps(['narcissist silent treatment punishment', 'silent treatment vs avoidant withdrawal', 'narcissist uses silence as control'])
    ),
    (
        'Covert Narcissists Look Like the Victim',
        'Vulnerable narcissism and the victim-as-abuser pattern. Covert or vulnerable narcissists differ from grandiose narcissists in presentation: they present as sensitive, wounded, misunderstood, and chronically mistreated. Research by Dickinson and Pincus identifies vulnerable narcissism as marked by hypersensitivity to criticism, passive aggression, and victimhood as a tool for control. The covert narcissist does not boast — they elicit sympathy. They do not demand admiration directly — they demand it through suffering. Their fragility is the manipulation. Recognizing covert narcissism is harder than grandiose because it exploits the target\'s empathy and the observer\'s sympathy instinct.',
        'dark_psychology',
        'The most dangerous narcissist in your life may not look entitled or arrogant. They may look like the most wounded person in the room. Covert narcissists weaponize victimhood. The fragility is the trap.',
        'dark_revelation',
        'pattern recognition shock — many viewers are currently in this dynamic without knowing it',
        'Covert narcissism is one of fastest-growing psychology search terms 2025-2026. Extends narcissist cluster perfectly. The "victim as abuser" reframe is highly shareable and deeply validating.',
        0.88, 0.97,
        json.dumps(['covert narcissist victim psychology', 'vulnerable narcissism weaponized victimhood', 'covert narcissist vs grandiose narcissist'])
    ),
    (
        'You Cannot Reason With Someone Who Benefits From Your Confusion',
        'Epistemic abuse and strategic confusion maintenance. Research on coercive control by Evan Stark identifies a pattern in abusive relationships where the abuser actively maintains the target in a state of confusion and self-doubt — not because they are confused themselves, but because a confused, self-doubting partner is more controllable. Logic, evidence, and communication attempts fail not because the abuser does not understand the argument but because understanding the argument would end their leverage. The target\'s attempts to explain, clarify, and convince are the mechanism of their own entrapment.',
        'dark_psychology',
        'You have spent years trying to explain yourself clearly enough for them to finally understand. Here is what no one tells you: they understand. They just benefit from pretending they do not.',
        'dark_revelation',
        'profound vindication — removes the last reason to keep trying to explain',
        'Extends the "narcissist knows what they are doing" thesis (top performer). High conversion potential. The "logic fails because they benefit from confusion" reframe is non-obvious and immediately shareable.',
        0.88, 0.97,
        json.dumps(['cannot reason with narcissist psychology', 'epistemic abuse strategic confusion', 'abuser benefits from your confusion'])
    ),
    (
        'Why You Still Defend the Person Who Hurt You',
        'Cognitive dissonance and trauma-bonded defense of abusers. Research on cognitive dissonance by Festinger shows that when behavior is inconsistent with held beliefs — in this case, staying with someone harmful — the mind resolves the dissonance by adjusting the belief rather than the behavior. The longer a person stays in an abusive relationship, the more elaborate the justifications become. They defend the abuser because the alternative is confronting that they have been harmed by someone they chose, loved, and trusted. The defense is not denial. It is the mind protecting itself from an unbearable truth. The defense is proportional to the harm.',
        'dark_psychology',
        'The more someone hurt you, the harder you will work to defend them. That is not weakness or stupidity. It is the mind protecting itself from having to believe that the person you loved most was hurting you on purpose.',
        'reframe',
        'deep vindication — removes shame from one of the most misunderstood trauma responses',
        'High personal resonance — extends trauma bond cluster (305% rewatch on return video). Cognitive dissonance + abuse is massively searched. High comment and share potential.',
        0.87, 0.97,
        json.dumps(['why defend person who hurt you psychology', 'cognitive dissonance abusive relationship', 'trauma bond defense of abuser'])
    ),
    (
        'Your Body Flinches Before Your Brain Knows Why',
        'Somatic memory and pre-conscious threat detection in trauma survivors. Van der Kolk\'s research establishes that traumatic memories are stored somatically — in the body\'s sensory and motor systems — before and independently of verbal memory. The body registers threat cues — a tone of voice, a posture, a smell — and initiates a physiological response (flinch, freeze, accelerated heart rate) before the conscious mind has processed what triggered it. Trauma survivors often describe inexplicable physical reactions to seemingly neutral stimuli. The body is not overreacting. It is pattern-matching against an archive of stored danger the conscious mind cannot access.',
        'self_awareness',
        'If your body reacts to something before you can explain why — a tone of voice, a look, a feeling in a room — that is not anxiety. That is your nervous system running a threat archive your conscious mind cannot read. Your body remembers what your brain protects you from knowing.',
        'dark_revelation',
        'deep recognition — speaks to a physical experience millions have but cannot explain',
        'Extends "Body Won\'t Forget the War" (71.2% retention, 2 subs). Somatic trauma content is surging. The pre-conscious flinch is universally felt by trauma survivors. High rewatch potential.',
        0.87, 0.96,
        json.dumps(['somatic memory trauma body flinch', 'body remembers trauma before brain', 'van der Kolk somatic threat detection'])
    ),
    (
        'Anxious Attachment Was Not Born With You — It Was Built',
        'The developmental origins of anxious attachment and caregiver inconsistency. Bowlby and Ainsworth\'s foundational research shows that anxious (preoccupied) attachment develops in response to caregivers who are inconsistently responsive — sometimes warm and attuned, sometimes absent, emotionally unavailable, or frightening. The infant learns that connection is available but unreliable, which produces hyperactivation of the attachment system: constant vigilance, heightened distress signals, protest behaviors. The adult with anxious attachment who fears abandonment, monitors partners obsessively, and cannot tolerate uncertainty is running a survival program built from a childhood where love was real but not dependable.',
        'relationship_psych',
        'You were not born anxious in relationships. You were born to a person whose love was real — but not consistent. Your nervous system learned that love exists but can disappear without warning. Everything you do in relationships now is trying to make sure that does not happen again.',
        'reframe',
        'identity-level reframe — removes shame from anxious attachment, replaces it with origin story',
        'Anxious attachment: Why you chase avoidants = 3 subs, high traffic. This is the origin story video. Deep emotional resonance for the channel\'s core audience. High rewatch potential.',
        0.86, 0.96,
        json.dumps(['anxious attachment origin childhood psychology', 'anxious attachment caregiver inconsistency', 'Bowlby Ainsworth anxious preoccupied attachment'])
    ),
    (
        'The Narcissist\'s Pity Play Is a Trap',
        'Weaponized vulnerability as a narcissistic manipulation tactic. Research on narcissistic supply acquisition identifies a subset of tactics where the narcissist does not demand admiration directly but instead elicits it through performed suffering: the strategic breakdown, the moment of confessed vulnerability, the revelation of past wounds. These disclosures achieve two functions simultaneously — they disarm the target\'s defenses (it is hard to maintain boundaries with someone who is crying) and they generate obligation. The target who is given access to the narcissist\'s vulnerability feels specially trusted and therefore responsible. The vulnerability was the hook. The obligation is the trap.',
        'dark_psychology',
        'When the narcissist finally showed you their wound — their childhood, their pain, their fear — something in you softened. That was the trap. Vulnerability in a narcissist is not an opening. It is a closing — of yours.',
        'dark_revelation',
        'recognition + reframe — targets the moment when many victims were fully hooked',
        'Extends narcissist cluster dominating channel. Pity play is widely searched. The "vulnerability as trap" reframe is counterintuitive and emotionally powerful. High share potential.',
        0.87, 0.96,
        json.dumps(['narcissist pity play manipulation', 'weaponized vulnerability narcissist', 'narcissist fake vulnerability trap'])
    ),
    (
        'Freeze Is Not Cowardice — It Is Your Nervous System Saving Your Life',
        'The freeze response as an adaptive survival mechanism, not a character failure. Polyvagal theory by Stephen Porges and trauma research by Peter Levine identify the freeze response — dissociation, immobility, inability to act or speak during threat — as a conserved biological survival mechanism. When fight and flight are assessed as unavailable or likely to increase danger, the nervous system defaults to freeze: metabolic shutdown, analgesia, dissociation. Trauma survivors who froze during abuse routinely carry shame about their inability to act. The freeze response did not fail them. It was selected over millions of years of evolution precisely because it works. Shame is the wrong response to a correctly functioning nervous system.',
        'self_awareness',
        'If you froze when it happened — could not speak, could not move, could not fight back — and you have spent years ashamed of that: your nervous system did not fail you. It made the same calculation a mammal makes when escape is not possible. It chose survival. You survived.',
        'vindication',
        'profound vindication — one of the deepest shame points for trauma and assault survivors',
        'Freeze response shame is among the most searched trauma topics. Polyvagal theory is trending. Directly vindicates one of the most painful and silent shame points. Extremely high share and save potential.',
        0.88, 0.97,
        json.dumps(['freeze response not cowardice trauma', 'polyvagal theory freeze survival mechanism', 'trauma freeze response shame vindication'])
    ),
    (
        'The Relationship Did Not Break You — It Revealed a Break That Was Already There',
        'Trauma activation vs. trauma creation in painful relationships. Research on relational trauma distinguishes between relationships that create new wounds and those that activate pre-existing ones. When a difficult relationship produces a level of pain disproportionate to its circumstances, it is often because it mirrors and activates an earlier unresolved wound — typically from childhood attachment disruptions. The relationship does not create the abandonment terror, the annihilation anxiety, or the desperate clinging. It finds the door that was already there and opens it. This reframe shifts the therapeutic target from the relationship to the origin wound and changes what healing looks like.',
        'self_awareness',
        'The relationship that broke you may not have broken you. It may have found the break that was already there — from somewhere long before them — and opened it all the way. That is not their damage you are carrying. It is your oldest wound, finally visible.',
        'reframe',
        'deep identity reframe — shifts self-blame toward origin wound, opens healing pathway',
        'Extends attachment + trauma cluster. Reframes "they broke me" into an empowering origin story. High therapist/coach share potential. Extremely relatable for channel core audience.',
        0.85, 0.95,
        json.dumps(['relationship revealed existing wound psychology', 'relational trauma activation not creation', 'relationship breaks open old wound attachment'])
    ),
    (
        'The Avoidant Does Not Fear You — They Fear Need Itself',
        'Dismissive-avoidant attachment and the suppression of the attachment system. Research by Bartholomew and Horowitz on dismissive-avoidant attachment shows that the avoidant\'s characteristic behavior — emotional distance, minimizing intimacy, discomfort with dependency — is not rejection of the specific partner but a deactivating strategy applied to the attachment system itself. The infant who learned that expressing need produced negative responses (withdrawal, irritation, unavailability) suppressed the need rather than the expression. The adult avoidant who pulls away when intimacy increases is not pulling away from you. They are running the same protective shutdown that once protected them from the pain of needing and not receiving. The tragedy: they want connection. They fear what connection requires.',
        'relationship_psych',
        'The avoidant in your life is not pulling away from you specifically. They are pulling away from need itself — because somewhere in childhood, needing someone cost them something they could not afford to lose again. It is not rejection. It is survival.',
        'reframe',
        'deep empathy reframe — creates compassion for avoidant behavior while validating the partner\'s pain',
        'Avoidant attachment is highest-traffic attachment topic. "Emotionally Unavailable" video just uploaded — this is the companion piece going deeper. Pairs with anxious attachment for complete picture.',
        0.86, 0.96,
        json.dumps(['avoidant attachment fears need not you', 'dismissive avoidant deactivating strategy', 'avoidant pulls away from need childhood'])
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
