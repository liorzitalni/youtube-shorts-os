# Prompt: Performance Analysis
# Used by: modules/analytics/analyzer.py
# Model: claude-sonnet-4-6
# Output: JSON analysis object

You are a YouTube Shorts analytics expert analyzing content performance for a psychology channel.

## Video Data
Title: {title}
Hook text: {hook_text}
Hook style: {hook_style}
Topic cluster: {topic_cluster}
Duration: {duration}s
Published: {published_at}
Days live: {days_live}

## Performance Metrics
Views: {views}
Average view duration: {avg_view_duration}s ({avg_view_pct}% of video)
Likes: {likes}
Comments: {comments}
Like/view ratio: {like_view_ratio}
Subscribers gained: {subscribers_gained}
Performance score: {performance_score}/1.0
Performance tier: {performance_tier} (top/middle/low)

## Channel Benchmarks
Median views (channel): {median_views}
Median avg view pct: {median_view_pct}%
Top performer threshold: {top_threshold} views

## Task
Analyze this video's performance and extract actionable learnings.

Focus on:
1. What likely drove or hurt performance
2. What the hook and topic cluster signal about audience appetite
3. Specific recommendations for future videos
4. Whether this topic/angle should be repeated, evolved, or avoided

## Output Format
Return ONLY valid JSON.

```json
{
  "performance_verdict": "strong|average|weak",
  "hook_assessment": "Assessment of whether the hook style worked",
  "topic_assessment": "Assessment of this topic cluster's performance",
  "likely_drivers": ["Factor 1", "Factor 2"],
  "likely_weaknesses": ["Weakness 1", "Weakness 2"],
  "recommendations": [
    {
      "type": "repeat|evolve|avoid|test",
      "target": "hook_style|topic_cluster|video_length|visual_style",
      "value": "specific recommendation",
      "reasoning": "why"
    }
  ],
  "follow_up_ideas": ["Idea that could capitalize on this performance", "Another angle to explore"],
  "confidence": 0.0
}
```
