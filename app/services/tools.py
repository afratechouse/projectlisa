import logging
from typing import Dict, Any

logger = logging.getLogger("lisa.tools")

# ---------------------------------------------------------------------------
# Declarations / Executions for Lisa's Core Tools
# ---------------------------------------------------------------------------

async def publish_video_to_social_media(platform: str, caption: str, video_url: str) -> Dict[str, Any]:
    """
    Publish a video to social media platforms like YouTube, Instagram, or Facebook.
    
    Args:
        platform: The target platform (e.g., 'facebook', 'instagram', 'youtube').
        caption: The caption/title for the video post.
        video_url: The URL or path to the video asset.
    """
    logger.info(f"Executing publish_video_to_social_media on {platform}: {caption}")
    return {
        "status": "success",
        "platform": platform,
        "message": f"Video successfully scheduled/published to {platform} with caption: '{caption}'",
    }


async def boost_social_media_post(post_id: str, budget_usd: float, duration_days: int, target_audience: str) -> Dict[str, Any]:
    """
    Boost a social media post (Meta Ads).
    CRITICAL: This is a financial sensitive action requiring 4-digit Master PIN verification.
    
    Args:
        post_id: The ID of the post to boost.
        budget_usd: Budget in USD for the ad campaign.
        duration_days: Number of days the campaign will run.
        target_audience: Description of target audience demographics/interests.
    """
    logger.info(f"Executing boost_social_media_post for {post_id} with budget ${budget_usd}")
    return {
        "status": "success",
        "post_id": post_id,
        "budget_usd": budget_usd,
        "duration_days": duration_days,
        "target_audience": target_audience,
        "message": f"Post {post_id} boosted successfully with a budget of ${budget_usd} for {duration_days} days.",
    }


async def manage_calendar_and_reminders(action: str, title: str, start_time: str, duration_minutes: int = 30) -> Dict[str, Any]:
    """
    Schedule, inspect, or manage events and reminders on the user's executive calendar.
    
    Args:
        action: 'create', 'read', 'update', or 'delete'.
        title: The title or topic of the meeting/reminder.
        start_time: ISO-formatted date string or natural language description (e.g. 'Tomorrow at 3 PM').
        duration_minutes: Duration of the event in minutes.
    """
    logger.info(f"Executing manage_calendar_and_reminders: action={action}, title={title}")
    return {
        "status": "success",
        "action": action,
        "title": title,
        "start_time": start_time,
        "duration_minutes": duration_minutes,
        "message": f"Calendar event '{title}' on {start_time} ({duration_minutes}m) has been processed ({action}).",
    }


async def web_search_and_summarize(query: str) -> Dict[str, Any]:
    """
    Search the web for real-time market insights, news, or factual answers and return a summary.
    
    Args:
        query: The search query string.
    """
    logger.info(f"Executing web_search_and_summarize for query: {query}")
    return {
        "status": "success",
        "query": query,
        "summary": f"Search results for '{query}' retrieved and processed.",
    }


# Map of callable tools
AVAILABLE_TOOLS = [
    publish_video_to_social_media,
    boost_social_media_post,
    manage_calendar_and_reminders,
    web_search_and_summarize,
]

TOOL_MAPPING = {
    "publish_video_to_social_media": publish_video_to_social_media,
    "boost_social_media_post": boost_social_media_post,
    "manage_calendar_and_reminders": manage_calendar_and_reminders,
    "web_search_and_summarize": web_search_and_summarize,
}

# Tools that strictly require Human-in-the-Loop (HITL) PIN Authorization
HITL_PROTECTED_TOOLS = {
    "boost_social_media_post",
}
