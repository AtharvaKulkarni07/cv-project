"""SSE streaming endpoint for the panorama stitching pipeline."""

import json
import time
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from services.image_utils import read_upload
from services.panorama import run_pipeline

router = APIRouter()


@router.post("/stream")
async def stitch_stream(images: list[UploadFile] = File(...)):
    """
    Accept 2+ images, run the full panorama pipeline, and
    stream each step as an SSE event.
    """
    if len(images) < 2:
        raise HTTPException(status_code=400, detail="Upload at least 2 images.")

    # Read all uploads into memory
    decoded = []
    for img_file in images:
        raw = await img_file.read()
        try:
            decoded.append(read_upload(raw))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Could not decode {img_file.filename}",
            )

    session_id = uuid.uuid4().hex[:12]

    def event_stream():
        start = time.time()
        try:
            for step_data in run_pipeline(decoded, session_id):
                # Inject elapsed time into the complete event
                if step_data.get("event") == "complete":
                    step_data["elapsed_seconds"] = round(time.time() - start, 2)
                yield f"data: {json.dumps(step_data)}\n\n"
        except Exception as exc:
            payload = {"event": "error", "detail": str(exc)}
            yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
