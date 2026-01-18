"""
Pipeline stages.

Stage 1: Extract transcript from CSV and clean with AI (combined)
Stage 2: Classify article type using AI
"""
import json
import logging
import os
import re

from langchain.prompts import PromptTemplate
from langchain_google_vertexai import VertexAI

from shared import RawVideoRecord, Stage1Output, Stage2Output

logger = logging.getLogger(__name__)

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


def stage_1_clean_transcript(record: RawVideoRecord) -> Stage1Output:
    """
    Stage 1: Extract transcript from CSV and clean it with AI.

    Removes:
    - Intros/outros
    - Ad reads/sponsor segments
    - Calls to action
    - Filler content

    Returns cleaned transcript ready for further processing.
    """
    logger.info("=" * 60)
    logger.info("STAGE 1: Cleaning transcript with AI")
    logger.info("=" * 60)
    logger.info(f"  Video: {record.title}")
    logger.info(f"  Input transcript: {len(record.transcript)} chars")

    # Check for required env var
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT environment variable is required")

    # Initialize Vertex AI
    llm = VertexAI(
        model_name="gemini-2.5-pro",
        temperature=0.1,
        max_tokens=8000,
        project=project,
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )

    prompt = PromptTemplate(
        input_variables=["transcript"],
        template="""You are a transcript cleaner. Extract ONLY the core content from this video transcript.

REMOVE:
- Intros and outros ("Hey everyone, welcome back...")
- Ad reads and sponsor segments ("This video is sponsored by...")
- Calls to action ("Don't forget to like and subscribe...")
- Off-topic tangents
- Filler phrases and repetition

KEEP:
- Main educational/informational content
- Key examples and explanations
- Important quotes and insights

Return ONLY the cleaned transcript text. No JSON, no explanations - just the cleaned content.

Transcript:
{transcript}"""
    )

    logger.info("  Sending to Vertex AI...")
    result = llm.invoke(prompt.format(transcript=record.transcript))
    logger.info("  Received response from Vertex AI")

    cleaned_transcript = result.strip()

    output = Stage1Output(
        video_id=record.video_id,
        title=record.title,
        cleaned_transcript=cleaned_transcript,
    )

    logger.info(f"  Output transcript: {len(output.cleaned_transcript)} chars")
    reduction = 100 - (
        len(output.cleaned_transcript) / max(1, len(record.transcript)) * 100
    )
    logger.info(f"  Reduction: {reduction:.1f}%")
    logger.info("=" * 60)

    return output


def stage_2_classify_article_type(stage1: Stage1Output) -> Stage2Output:
    """
    Stage 2: Classify the cleaned transcript into one of 42 article types.

    Uses AI to determine the best article format based on transcript content.
    Returns classification, confidence score, and reasoning.
    """
    logger.info("=" * 60)
    logger.info("STAGE 2: Classifying article type")
    logger.info("=" * 60)
    logger.info(f"  Video: {stage1.title}")
    logger.info(f"  Transcript length: {len(stage1.cleaned_transcript)} chars")

    # Truncate very long transcripts for classification (15k chars is enough)
    MAX_CLASSIFICATION_CHARS = 15000
    transcript_for_classification = stage1.cleaned_transcript
    if len(transcript_for_classification) > MAX_CLASSIFICATION_CHARS:
        transcript_for_classification = transcript_for_classification[:MAX_CLASSIFICATION_CHARS]
        logger.info(f"  Truncated transcript to {MAX_CLASSIFICATION_CHARS} chars for classification")

    # Check for required env var
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT environment variable is required")

    # Initialize Vertex AI
    llm = VertexAI(
        model_name="gemini-2.5-pro",
        temperature=0.1,
        max_tokens=2048,  # Increased to avoid truncation
        project=project,
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    )

    # Build the article types list for the prompt
    article_types_list = "\n".join(f"- {t}" for t in ALLOWED_ARTICLE_TYPES)

    prompt = PromptTemplate(
        input_variables=["transcript", "article_types"],
        template="""You are an article-intent classification engine.

Your ONLY task is to analyze a cleaned YouTube transcript and classify
what type of article it can most naturally be converted into.

You MUST choose exactly ONE primary classification from the list below.

You are NOT allowed to:
- Write an article
- Suggest multiple primary types
- Invent content not present in the transcript
- Optimize for SEO
- Add tone, outline, or formatting suggestions

Your job is classification ONLY.

---

ALLOWED ARTICLE TYPES (EXACT MATCH REQUIRED):

{article_types}

If none apply clearly, choose the closest fit based on dominant intent.

---

CLASSIFICATION DEFINITIONS (USE THESE INTERNALLY):

- How-to Guides → Teaches a process, steps, or methods to achieve an outcome.
- Disqualifiers → Warns who should NOT do something or filters an audience.
- Opinion Piece → Expresses personal beliefs, judgments, or persuasion.
- In-depth Analysis → Explains causes, systems, trade-offs, or frameworks deeply.
- Interview → Structured Q&A between two or more speakers.
- News Article → Reports timely facts or announcements neutrally.
- Feature Story → Narrative-driven, human-focused storytelling.
- Case Study → Real example showing problem → action → result.
- Listicle → Content structured primarily as a list or ranked items.
- Explainer → Breaks down a concept simply (e.g., "What Is Travel Insurance?").
- Beginner's Guide → Assumes zero knowledge to introduce a topic.
- FAQ Article → Question-driven education answering common queries.
- Myth-Busting Article → Corrects common misconceptions.
- Comparison Article → Evaluates multiple options against each other (A vs. B).
- Pros & Cons Breakdown → Balanced evaluation of advantages and disadvantages.
- Buyer's Guide → Helps readers choose between products or services.
- Review → Evaluates a single product, service, or place in depth.
- Roundup → Summarizes multiple options with brief evaluations.
- Best Of → Curates top recommendations in a category.
- Cost Breakdown → Transparently details prices or budgets.
- Checklist → Actionable, scannable to-do or packing lists.
- Resource List → Curated list of tools, links, or services.
- Survival Guide → Provides practical advice for challenging situations.
- Destination Guide → Comprehensive overview of a place's highlights, logistics, and tips.
- Itinerary Article → Day-by-day travel plan or sequence of activities.
- Travel Diary → Personal narrative or trip report recounting experiences chronologically.
- Where to Stay Guide → Advises on neighborhoods, lodging types, and accommodation tips.
- When to Visit Article → Covers seasons, weather, crowds, and timing considerations.
- Budget Travel Guide → Focuses on saving money and cost-effective strategies.
- Luxury Travel Guide → Highlights premium experiences and upscale options.
- Solo Travel Guide → Tailors advice for individual travelers, safety, and logistics.
- Family Travel Guide → Offers kid-friendly planning and tips for all ages.
- Digital Nomad Guide → Blends work and travel logistics for long-term stays.
- Packing Guide → Recommends essential items to bring for specific trips.
- Visa & Entry Guide → Outlines visa requirements, paperwork, and border protocols.
- Safety Guide → Addresses risks, scams, and precautions.
- Cultural Etiquette Guide → Explains local customs, do's and don'ts.
- Transportation Guide → Describes getting around (trains, buses, rentals, passes).
- Travel Inspiration Piece → Emotional or aspirational content to spark wanderlust.
- Hidden Gems Article → Uncovers lesser-known or off-the-beaten-path spots.
- Food Travel Guide → Explores culinary highlights, local dishes, and dining tips.
- Adventure Guide → Focuses on activities like hiking, diving, trekking, or other adventures.

---

ANALYSIS RULES:

1. Base classification ONLY on the transcript content.
2. Identify the dominant intent (teach, warn, persuade, analyze, report, tell, inspire, plan, review).
3. Ignore intros, ads, or calls-to-action unless they dominate the transcript.
4. Do NOT assume the creator's intent — infer from language and structure.
5. Choose the classification that best represents the majority of the transcript.

---

CONFIDENCE GUIDELINES:

- 0.80 – 1.00 → Clear, dominant signals
- 0.60 – 0.79 → Strong but mixed signals
- 0.40 – 0.59 → Ambiguous, best-fit choice
- Below 0.40 → Weak match (still must choose one)

---

OUTPUT FORMAT (STRICT JSON ONLY):

{{
  "classification": "<ONE article type from the allowed list>",
  "confidence": <float between 0.00 and 1.00>,
  "reasoning": "<1-2 sentence explanation of why this classification fits>"
}}

---

TRANSCRIPT:

{transcript}"""
    )

    # Build the full prompt for debugging
    full_prompt = prompt.format(
        transcript=transcript_for_classification,
        article_types=article_types_list,
    )
    logger.info(f"  Full prompt length: {len(full_prompt)} chars")

    logger.info("  Sending to Vertex AI for classification...")
    result = llm.invoke(full_prompt)
    logger.info("  Received response from Vertex AI")
    logger.info(f"  Raw response length: {len(result) if result else 0} chars")
    logger.info(f"  Raw response: {result[:1000] if result else 'EMPTY'}...")

    # Handle empty response
    if not result or not result.strip():
        logger.error("  Vertex AI returned empty response")
        raise RuntimeError("Classification failed: LLM returned empty response")

    # Parse JSON response
    result_text = result.strip()
    logger.info(f"  Raw response preview: {result_text[:200]}...")

    # Strategy 1: Extract from complete markdown code block
    json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", result_text, re.DOTALL)
    if json_match:
        result_text = json_match.group(1).strip()
        logger.info("  Extracted JSON from complete markdown code block")
    else:
        # Strategy 2: Handle truncated markdown block (no closing ```)
        truncated_match = re.search(r"```(?:json)?\s*(\{.*)", result_text, re.DOTALL)
        if truncated_match:
            result_text = truncated_match.group(1).strip()
            logger.info("  Extracted JSON from truncated markdown block")
        # Strategy 3: Find raw JSON object
        elif not result_text.startswith("{"):
            json_obj_match = re.search(r"\{.*", result_text, re.DOTALL)
            if json_obj_match:
                result_text = json_obj_match.group(0).strip()
                logger.info("  Extracted JSON object from response")

    if not result_text or not result_text.startswith("{"):
        logger.error(f"  No JSON found in response: {result[:500]}")
        raise RuntimeError(f"No JSON found in LLM response. Raw response: {result[:300]}...")

    # Strategy 4: Try to fix truncated JSON by adding missing closing braces
    try:
        parsed = json.loads(result_text)
    except json.JSONDecodeError as e:
        logger.warning(f"  Initial JSON parse failed: {e}")
        # Count braces to try to fix truncation
        open_braces = result_text.count("{")
        close_braces = result_text.count("}")
        if open_braces > close_braces:
            # Try adding closing braces and quotes
            fixed_text = result_text.rstrip()
            # If ends mid-string, close the string
            if fixed_text.count('"') % 2 == 1:
                fixed_text += '"'
            # Add missing closing braces
            fixed_text += "}" * (open_braces - close_braces)
            logger.info(f"  Attempting to fix truncated JSON (added {open_braces - close_braces} braces)")
            try:
                parsed = json.loads(fixed_text)
                logger.info("  Successfully parsed fixed JSON")
            except json.JSONDecodeError as e2:
                logger.error(f"  Failed to parse fixed JSON: {fixed_text[:500]}")
                raise RuntimeError(f"JSON parse failed after fix attempt. Response: {result_text[:300]}...") from e2
        else:
            logger.error(f"  Failed to parse JSON response: {result_text[:500]}")
            raise RuntimeError(f"JSON parse failed: {e}. Response: {result_text[:300]}...") from e

    classification = parsed.get("classification", "")
    confidence = float(parsed.get("confidence", 0.0))
    reasoning = parsed.get("reasoning", "")

    # Validate classification is in allowed list
    if classification not in ALLOWED_ARTICLE_TYPES:
        logger.warning(
            f"  Classification '{classification}' not in allowed list, "
            f"using closest match"
        )
        # Find closest match (case-insensitive)
        for allowed in ALLOWED_ARTICLE_TYPES:
            if allowed.lower() == classification.lower():
                classification = allowed
                break
        else:
            # Default to first type if no match found
            logger.warning(f"  No match found, defaulting to 'How-to Guides'")
            classification = "How-to Guides"

    output = Stage2Output(
        video_id=stage1.video_id,
        title=stage1.title,
        classification=classification,
        confidence=confidence,
        reasoning=reasoning,
        debug_prompt=full_prompt,
        debug_raw_response=result,
    )

    logger.info(f"  Classification: {output.classification}")
    logger.info(f"  Confidence: {output.confidence:.2f}")
    logger.info(f"  Reasoning: {output.reasoning}")
    logger.info("=" * 60)

    return output
