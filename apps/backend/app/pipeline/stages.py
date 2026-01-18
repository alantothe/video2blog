"""
Pipeline stages.

Stage 1: Extract transcript from CSV and clean with AI (combined)
Stage 2: Classify article type using AI
"""
from .stages.stage_1 import stage_1_clean_transcript as _stage_1_clean_transcript
from .stages.stage_2 import stage_2_classify_article_type as _stage_2_classify_article_type

# All 42 allowed article types for classification
ALLOWED_ARTICLE_TYPES = [
    "How-to Guides",
    "Disqualifiers",
    "Opinion Piece",
    "In-depth Analysis",
    "Interview",
    "News Article",
    "Feature Story",
    "Case Study",
    "Listicle",
    "Explainer",
    "Beginner's Guide",
    "FAQ Article",
    "Myth-Busting Article",
    "Comparison Article",
    "Pros & Cons Breakdown",
    "Buyer's Guide",
    "Review",
    "Roundup",
    "Best Of",
    "Cost Breakdown",
    "Checklist",
    "Resource List",
    "Survival Guide",
    "Destination Guide",
    "Itinerary Article",
    "Travel Diary",
    "Where to Stay Guide",
    "When to Visit Article",
    "Budget Travel Guide",
    "Luxury Travel Guide",
    "Solo Travel Guide",
    "Family Travel Guide",
    "Digital Nomad Guide",
    "Packing Guide",
    "Visa & Entry Guide",
    "Safety Guide",
    "Cultural Etiquette Guide",
    "Transportation Guide",
    "Travel Inspiration Piece",
    "Hidden Gems Article",
    "Food Travel Guide",
    "Adventure Guide",
]


def stage_1_clean_transcript(record):
    """Wrapper for stage 1 function."""
    return _stage_1_clean_transcript(record)


def stage_2_classify_article_type(stage1):
    """Wrapper for stage 2 function."""
    return _stage_2_classify_article_type(stage1, ALLOWED_ARTICLE_TYPES)
