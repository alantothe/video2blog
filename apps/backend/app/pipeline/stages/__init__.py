"""
Pipeline stages.

Stage 1: Extract transcript from CSV and clean with AI (combined)
Stage 2: Classify article type using AI
Stage 3: Compose article with coverage analysis
Stage 4: Generate article title
"""
from app.storage.file_store import read_article_type_names

# Load allowed article types from database
ALLOWED_ARTICLE_TYPES = read_article_type_names()


def stage_1_clean_transcript(record):
    """Wrapper for stage 1 function."""
    from .stage_1 import stage_1_clean_transcript as _stage_1_clean_transcript
    return _stage_1_clean_transcript(record)


def stage_2_classify_article_type(stage1):
    """Wrapper for stage 2 function."""
    from .stage_2 import stage_2_classify_article_type as _stage_2_classify_article_type
    return _stage_2_classify_article_type(stage1, ALLOWED_ARTICLE_TYPES)


def stage_3_compose_article(stage1, stage2):
    """Wrapper for stage 3 function."""
    from .stage_3 import stage_3_compose_article as _stage_3_compose_article
    return _stage_3_compose_article(stage1, stage2)


def stage_4_generate_title(stage3):
    """Wrapper for stage 4 function."""
    from .stage_4 import stage_4_generate_title as _stage_4_generate_title
    return _stage_4_generate_title(stage3)