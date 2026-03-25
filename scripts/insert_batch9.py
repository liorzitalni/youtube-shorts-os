import sqlite3, json
from datetime import datetime

ideas = [
    (
        'Hoovering: Why They Come Back Right When You\'re Healing',
        'Narcissistic hoovering — named after the Hoover vacuum cleaner — is the documented pattern where the narcissist attempts to re-establish contact and control precisely when the target has begun to heal, go no-contact, or show signs of independence. Research on coercive control by Evan Stark and clinical observations by Lundy Bancroft establish that the narcissist does not monitor the calendar — they monitor supply. When their current sources dry up, when the new relationship fails, or when the target\'s emotional distance signals lost control, the hoover begins. The timing feels miraculous — as though they sensed healing — because they did. The reconnection attempt is not love. It is a supply emergency.',
        'dark_psychology',
        'They always come back right when you are finally starting to feel okay. That is not a coincidence. It is not love. There is a documented name for what they are doing — and understanding it will make sure it never works again.',
        'dark_revelation',
        'recognition shock + protection — names the pattern that has pulled millions back in',
        'Hoovering resources trending March 2026. Directly addresses the most dangerous moment in narcissistic abuse recovery. High search volume. The "why now" question is searched by millions of survivors. Extreme share potential.',
        0.89, 0.98,
        json.dumps(['narcissist hoovering why they come back', 'hoovering after no contact psychology', 'narcissist returns when you heal'])
    ),
    (
        'The Grey Rock Method: How to Make a Narcissist Lose Interest in You',
        'The Grey Rock Method is a documented self-protection strategy for people who cannot fully cut contact with a narcissist — shared custody, family, workplace. The technique involves making all interactions as emotionally flat, factual, and unstimulating as possible. Narcissists feed on emotional reactions — positive or negative. Without emotional supply, the target ceases to be interesting. Grey rock removes the reward. Research on operant conditioning supports the mechanism: behavior that is not reinforced is extinguished. The grey rock practitioner does not fight, cry, defend, explain, or react. They become boring. Boring is the exit.',
        'dark_psychology',
        'You cannot always go no contact. But there is a method — documented and researched — that makes a narcissist lose interest in you on its own. It is called the Grey Rock Method. And once you understand why it works, you will never be interesting to them again.',
        'authority_subversion',
        'empowerment + practical solution — gives survivors a tool, not just understanding',
        'Grey Rock trending March 2026 — new clinical resources published. Actionable content outperforms theory in saves and shares. High practical value for survivors in unavoidable contact situations. Massive search volume.',
        0.88, 0.97,
        json.dumps(['grey rock method narcissist', 'how to grey rock a narcissist', 'grey rock method no contact impossible'])
    ),
    (
        'Future Faking: The Promise Was Never a Plan',
        'Future faking is a documented narcissistic manipulation tactic in which the narcissist makes detailed, emotionally compelling promises about the future — moving in together, getting married, building a life — with no intention of following through. The promises are not aspirational mistakes. They are strategic tools: they keep the target invested, prevent exit, and create the illusion of a shared future that justifies the present mistreatment. Research on narcissistic relationship tactics by Craig Malkin identifies future faking as a primary retention tool. The target who stays because of what was promised is being held by a future that was designed to never arrive.',
        'dark_psychology',
        'They talked about your future together like they had already decided. The house. The life. The children. And then it never came. That was not indecision. That was a strategy called future faking — and the promise was never a plan.',
        'dark_revelation',
        'grief-to-clarity — explains the specific confusion of why "the plan" never materialized',
        'Future faking trending alongside grey rock and hoovering in March 2026 recovery content. Named tactic with high search volume. The recognition moment when survivors hear this for the first time is extremely powerful.',
        0.88, 0.97,
        json.dumps(['future faking narcissist psychology', 'narcissist promises never happen', 'Craig Malkin future faking manipulation'])
    ),
    (
        'The Fawn Response: When You Learned Love Requires Performance',
        'The fawn response — identified by Pete Walker as the fourth trauma response alongside fight, flight, and freeze — is a survival strategy in which the person preemptively appeases, placates, and prioritizes others\' needs to avoid conflict or punishment. It develops in childhood environments where expressing authentic needs or emotions was punished, ignored, or produced worse outcomes than compliance. The fawn-adapted adult is often described as "so kind," "so giving," "so easy to be with" — precisely because they have learned that their emotional survival depends on being useful and pleasant. What looks like generosity is a nervous system managing a threat. The kindness is armor.',
        'self_awareness',
        'There is a fourth trauma response that nobody talks about. It is not fight, flight, or freeze. It is fawn — and if you have spent your whole life making yourself agreeable, easy, and small to keep the peace, you have been living inside it.',
        'dark_revelation',
        'identity-level recognition — names the invisible trauma response millions are living in without knowing',
        'Fawn response is fastest growing trauma response search term 2025-2026. Pete Walker content surging. Fourth trauma response = natural viral hook. Deep identity resonance for people-pleasers and abuse survivors.',
        0.88, 0.97,
        json.dumps(['fawn response trauma fourth Pete Walker', 'fawn response people pleasing survival', 'fawn response vs fight flight freeze'])
    ),
    (
        'Narcissistic Rage Is Not Anger — It Is Control',
        'Narcissistic rage is distinct from normal anger and from the anger of other personality presentations. Research by Heinz Kohut, who first described the phenomenon, identifies narcissistic rage as triggered not by genuine grievance but by narcissistic injury — any perceived slight, criticism, or evidence of the narcissist\'s fallibility. The rage is disproportionate because it is not responding to what happened. It is responding to the threat of exposure. The target who witnesses narcissistic rage and attempts to de-escalate, apologize, and prevent recurrence is being trained. Each successful rage episode teaches the target that the narcissist\'s emotional stability is their responsibility. That is the function.',
        'dark_psychology',
        'When the narcissist exploded over something small, you thought you had triggered something deep in them. You had. But not grief or pain. What you triggered was the fear of being seen as ordinary. Narcissistic rage is not anger. It is a control mechanism — and every time you apologized, it worked.',
        'dark_revelation',
        'vindication + reframe — removes the shame of having apologized for things that were not your fault',
        'Narcissistic rage is consistently one of the most searched narcissism terms. Extends channel\'s top-performing narcissist cluster. Kohut research gives clinical credibility. High retention and share potential.',
        0.88, 0.97,
        json.dumps(['narcissistic rage not anger control', 'Kohut narcissistic rage injury', 'narcissist explodes disproportionate reaction'])
    ),
    (
        'Why You Feel Guilty When You Set a Boundary',
        'Boundary guilt as a conditioned response in people raised in environments where boundaries were punished. Research on enmeshed family systems by Murray Bowen and on emotional coercion in intimate relationships shows that people who grew up in boundary-violating environments internalize the violator\'s perspective — meaning they experience their own boundary-setting as aggression. The guilt is not evidence that the boundary was wrong. It is evidence that the person learned that self-protection was a form of harm. The discomfort of setting a boundary is not conscience. It is conditioning. The people who feel the guiltiest about setting boundaries are the ones who needed them most and were punished for trying.',
        'self_awareness',
        'The reason setting a boundary feels like you are doing something wrong is not your conscience. It is conditioning. You were taught that your own self-protection was a form of cruelty. The guilt is not a signal. It is a scar.',
        'reframe',
        'deep self-compassion reframe — removes the guilt that prevents boundary maintenance',
        '38% of Americans set mental health resolutions in 2026 — boundaries is top term. High shareability among therapy audiences. Reframes the most common obstacle to recovery. Extremely actionable and relatable.',
        0.86, 0.96,
        json.dumps(['guilt setting boundaries psychology', 'why boundary setting feels wrong conditioning', 'Bowen enmeshed family boundary guilt'])
    ),
    (
        'The Narcissist\'s Discard: Why They Replace You Instantly',
        'The narcissistic discard and immediate replacement is one of the most psychologically destabilizing aspects of narcissistic relationships. It appears to prove that the relationship meant nothing. Research on object relations in narcissistic personalities by Otto Kernberg explains the mechanism: narcissists experience people as functions, not as individuals with inherent worth. The replacement is not about the new person\'s qualities — it is about supply availability. The speed and apparent ease of replacement reflects how the narcissist processed the relationship from the beginning: as a supply source, not a person. The target who is devastated by the replacement is experiencing the collision between how they experienced the relationship and how the narcissist did. Both are real. They describe completely different relationships.',
        'dark_psychology',
        'They moved on instantly. New person, same declarations, same future promises — within weeks. That did not mean the relationship meant nothing. It meant they experienced it differently than you did. You were in a relationship. They were managing a supply source. You were not replaced. You were reclassified.',
        'dark_revelation',
        'grief-to-clarity — the most painful narcissistic experience finally explained in a way that restores dignity',
        'Narcissist discard and replacement is one of highest search volume narcissism topics. Kernberg object relations = clinical credibility. The "reclassified not replaced" reframe is non-obvious and deeply vindicating. Extreme share potential.',
        0.89, 0.98,
        json.dumps(['narcissist discard replace instantly psychology', 'Kernberg narcissist object relations supply', 'narcissist moves on immediately explanation'])
    ),
    (
        'Triangulation: Why the Narcissist Always Needs a Third Person',
        'Triangulation is a documented manipulation tactic in which the narcissist introduces a third party — real or implied — into the relationship dynamic to create jealousy, insecurity, and competition. Research on narcissistic relationship tactics identifies triangulation as serving multiple functions simultaneously: it destabilizes the target\'s confidence, creates competition that generates more emotional engagement, provides a backup supply source, and gives the narcissist leverage. The third person is not a rival. They are a prop. The narcissist does not want the third person — they want what the threat of the third person produces in you: pursuit, compliance, and increased effort to prove your worth.',
        'dark_psychology',
        'The other person your ex always mentioned — the friend, the colleague, the ex they stayed close with — was not competition. They were a tool. Triangulation is a documented narcissistic tactic. You were not losing to someone better. You were being managed.',
        'dark_revelation',
        'recognition + reframe — removes jealousy shame, names the tactic, restores self-worth',
        'Triangulation is high-search narcissism term. Named tactic content consistently outperforms general content. Jealousy video hit 91.4% retention — this is the "why" behind that content. Natural pairing.',
        0.87, 0.97,
        json.dumps(['narcissist triangulation third person manipulation', 'triangulation jealousy narcissistic tactic', 'why narcissist uses triangulation psychology'])
    ),
    (
        'You Were Never Too Much — You Were Given Too Little',
        'The "too much" narrative in emotionally abusive relationships — you are too sensitive, too needy, too emotional, too intense — is a projection that functions as a supply-protection mechanism. Research on coercive control by Stark and on emotional invalidation by Linehan identifies the "too much" narrative as a consistent feature of controlling relationships: it relocates the problem from the relationship\'s inadequacy to the target\'s excess. The partner who is "too needy" is often simply a securely attached person asking for normal levels of emotional availability. The partner who is "too sensitive" is often accurately detecting genuine cruelty. The target was not too much. The relationship was too little — and naming the target as excessive concealed that.',
        'dark_psychology',
        'Every time they told you that you were too much — too sensitive, too needy, too emotional — they were relocating the problem. You were not too much. You were asking for something normal from someone who could not give it. The excess was not in you. It was in what you deserved and did not receive.',
        'vindication',
        'deep vindication — one of the most searched survivor experiences, names the inversion',
        'Channel has already proven "You Were Never Too Much" format (prod 3 — early channel hit). This is the darker, more specific version with the narcissism angle. High rewatch + share potential. Directly addresses top survivor wound.',
        0.87, 0.97,
        json.dumps(['you were never too much narcissist psychology', 'too sensitive too needy narcissist gaslighting', 'too much projection coercive control'])
    ),
    (
        'The Trauma Response You Were Told Was a Personality Flaw',
        'Hypervigilance, people-pleasing, difficulty trusting, emotional dysregulation, conflict avoidance, inability to receive love — these are routinely pathologized as personality flaws, relationship incompatibilities, or character deficits. Research by Judith Herman on complex PTSD and van der Kolk on developmental trauma establishes these as predictable, coherent adaptations to chronic threat environments. The person who cannot stop scanning for danger was taught that danger arrives without warning. The person who cannot accept kindness was taught that kindness has a cost. The person who becomes small in conflict learned that smallness was survival. None of these are flaws. They are the exact responses a functional nervous system produces when a human being is not safe.',
        'self_awareness',
        'The things you hate most about yourself in relationships — the hypervigilance, the people-pleasing, the inability to just relax and trust — are not character flaws. They are a nervous system that learned the rules of a different environment. You are not broken. You were adapting.',
        'vindication',
        'profound vindication + identity restoration — reframes self-hatred into adaptive intelligence',
        'Complex PTSD and developmental trauma content surging 2026. Herman and van der Kolk are most-cited trauma researchers. The "flaw vs. adaptation" reframe is the deepest vindication available. High rewatch potential. Directly addresses 18-34 audience making mental health resolutions.',
        0.88, 0.97,
        json.dumps(['trauma response not personality flaw psychology', 'complex PTSD adaptations Herman van der Kolk', 'hypervigilance people pleasing trauma adaptation'])
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
