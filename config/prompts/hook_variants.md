# Prompt: Hook Variants
# Used by: modules/scripts/script_generator.py (after main script)
# Model: claude-haiku-4-5 (fast)
# Output: JSON array of 3 hook variants

You are writing 3 alternative opening hooks for a YouTube Shorts psychology video.

## The Video
Title: {title}
Topic: {topic}
Core Script Hook: {original_hook}
Emotional Trigger: {emotional_trigger}

## Task
Write 3 alternative hooks using different styles. Each hook is the first 1–2 spoken sentences (approximately 3 seconds of audio).

Rules:
- Must create immediate tension, curiosity, or emotional response
- No preamble or warm-up
- Each must be genuinely different in style (not just reworded)
- Max 25 words per hook

## Output Format
Return ONLY valid JSON.

```json
[
  {
    "variant": 1,
    "style": "question",
    "text": "Spoken hook text",
    "onscreen": "2-4 word on-screen version"
  },
  {
    "variant": 2,
    "style": "stat",
    "text": "Spoken hook text",
    "onscreen": "2-4 word on-screen version"
  },
  {
    "variant": 3,
    "style": "bold_claim",
    "text": "Spoken hook text",
    "onscreen": "2-4 word on-screen version"
  }
]
```
