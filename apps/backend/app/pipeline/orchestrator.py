"""
Simple pipeline orchestrator.

Runs: Stage 1 (extract transcript + clean with AI)
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional
from uuid import uuid4

from shared import (
    PipelineArtifact,
    PipelineMeta,
    RawVideoRecord,
    Stage0Output,
    StageResult,
)

from app.config import PIPELINE_VERSION
from app.pipeline.stages import stage_1_clean_transcript
from app.storage.file_store import (
    read_stage_result,
    write_artifact,
    write_stage_result,
    write_status,
)


def _now() -> datetime:
    return datetime.utcnow()


def _stage_ref(run_id: str, stage: str) -> str:
    return f"data/runs/{run_id}/{stage}.json"


def initialize_run(
    record: RawVideoRecord,
    source: str,
    notes: Optional[str] = None,
) -> PipelineMeta:
    """Initialize a new pipeline run with Stage 0 (raw input)."""
    run_id = str(uuid4())
    meta = PipelineMeta(
        run_id=run_id,
        version=PIPELINE_VERSION,
        created_at=_now(),
        source=source,
        notes=notes,
    )
    stage0 = Stage0Output(meta=meta, record=record)
    stage_result = StageResult(
        run_id=run_id,
        stage="stage_0",
        created_at=_now(),
        input_refs={"source": source},
        data=stage0.model_dump(),
    )
    write_stage_result(run_id, "stage_0", stage_result.model_dump())
    write_status(
        run_id,
        {
            "run_id": run_id,
            "stage": "stage_0",
            "state": "pending",
            "updated_at": _now().isoformat(),
            "error": None,
        },
    )
    return meta


def process_run(record: RawVideoRecord, meta: PipelineMeta) -> str:
    """
    Run the pipeline.

    Stage 1: Extract transcript and clean with AI
    """
    run_id = meta.run_id
    stage_results: Dict[str, StageResult] = {}

    try:
        # ========================================
        # STAGE 1: Extract + Clean
        # ========================================
        write_status(
            run_id,
            {
                "run_id": run_id,
                "stage": "stage_1",
                "state": "running",
                "updated_at": _now().isoformat(),
                "error": None,
            },
        )

        stage1 = stage_1_clean_transcript(record)
        result1 = StageResult(
            run_id=run_id,
            stage="stage_1",
            created_at=_now(),
            input_refs={"stage_0": _stage_ref(run_id, "stage_0")},
            data=stage1.model_dump(),
        )
        write_stage_result(run_id, "stage_1", result1.model_dump())
        stage_results["stage_1"] = result1

        # ========================================
        # Output: Save to SQLite
        # ========================================
        markdown = f"""# {stage1.title}

{stage1.cleaned_transcript}
"""

        # Save artifact with markdown
        stage_results["stage_0"] = StageResult(
            **read_stage_result(run_id, "stage_0")
        )
        artifact = PipelineArtifact(
            run_id=run_id,
            meta=meta,
            stages=stage_results,
            markdown_path=f"db:outputs:{run_id}",
        )
        artifact_dict = artifact.model_dump()
        artifact_dict["markdown"] = markdown  # Include markdown in artifact
        write_artifact(run_id, artifact_dict)

        write_status(
            run_id,
            {
                "run_id": run_id,
                "stage": "complete",
                "state": "completed",
                "updated_at": _now().isoformat(),
                "error": None,
            },
        )

        return markdown

    except Exception as exc:
        write_status(
            run_id,
            {
                "run_id": run_id,
                "stage": "error",
                "state": "failed",
                "updated_at": _now().isoformat(),
                "error": str(exc),
            },
        )
        raise
