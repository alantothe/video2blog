import pytest

from shared import RawVideoRecord

from app.pipeline.stages import stage_1_clean_transcript


def sample_record() -> RawVideoRecord:
    return RawVideoRecord(
        video_id="vid123",
        title="Test Video",
        description="Test description",
        channel_title="Test Channel",
        channel_id="ch123",
        video_url="https://youtube.com/watch?v=vid123",
        published_at="2024-01-01T00:00:00Z",
        transcript=(
            "HOST: Hello world.\nHOST: Hello world.\n[Music] Intro segment."
        ),
        transcript_status="completed",
        transcript_extracted_at="2024-01-01T00:00:00Z",
        feed_display_name="Test Feed",
        channel_summary="Channel covers AI workflows.",
        primary_topics='["AI", "Pipelines"]',
        audience="Builders",
        language_region="en-US",
        hosts='["Host"]',
        formats='["Interview"]',
        tone_style='["Analytical", "Direct"]',
        expertise_background="Industry practitioner",
        credibility_bias_notes="None",
    )


def test_stage_1_requires_project_env(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    record = sample_record()

    with pytest.raises(RuntimeError, match="GOOGLE_CLOUD_PROJECT"):
        stage_1_clean_transcript(record)


def test_stage_1_clean_transcript_uses_ai_output(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "test-project")

    class StubVertexAI:
        last_prompt = ""

        def __init__(self, *args, **kwargs):
            pass

        def invoke(self, prompt: str) -> str:
            StubVertexAI.last_prompt = prompt
            return "Cleaned transcript output."

    monkeypatch.setattr("app.pipeline.stages.VertexAI", StubVertexAI)

    record = sample_record()
    output = stage_1_clean_transcript(record)

    assert output.cleaned_transcript == "Cleaned transcript output."
    assert output.video_id == record.video_id
    assert record.transcript in StubVertexAI.last_prompt
