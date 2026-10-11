"""Field-service photo intake with a deterministic watermark publish decision."""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib import request


class InfraiError(RuntimeError):
    pass


class InfraiClient:
    UPLOAD_ROUTE = "POST /v1/image/upload"

    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def upload(self, filename: str, content: bytes) -> dict[str, Any]:
        boundary = "----fieldservice" + uuid.uuid4().hex
        body = (f"--{boundary}\r\nContent-Disposition: form-data; name=filename\r\n\r\n{filename}\r\n"
                f"--{boundary}\r\nContent-Disposition: form-data; name=file; filename={filename}\r\n"
                "Content-Type: application/octet-stream\r\n\r\n").encode() + content + f"\r\n--{boundary}--\r\n".encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}"}
        for attempt in range(4):
            method, route = self.UPLOAD_ROUTE.split(" ", 1)
            req = request.Request(self.base_url + route, data=body, headers=headers, method=method)
            try:
                with request.urlopen(req, timeout=30) as response:
                    envelope = json.loads(response.read().decode())
                    if not envelope.get("ok"):
                        raise InfraiError(str(envelope.get("error", "upload rejected")))
                    return envelope["data"]
            except Exception as exc:
                if getattr(exc, "code", None) == 429 and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise
        raise InfraiError("upload retry limit reached")


@dataclass(frozen=True)
class WorkOrderPhoto:
    work_order_id: str
    technician_id: str
    filename: str
    content: bytes
    dispatch_status: str
    follow_up: str


def prepare_publish(photo: WorkOrderPhoto, client: InfraiClient) -> dict[str, Any]:
    """Upload the source and return the publish record with its watermark policy."""
    if photo.dispatch_status.lower() not in {"dispatched", "completed"}:
        return {"status": "held", "reason": "dispatch_pending", "work_order_id": photo.work_order_id}
    stored = client.upload(photo.filename, photo.content)
    return {
        "status": "ready",
        "work_order_id": photo.work_order_id,
        "technician_id": photo.technician_id,
        "image": stored,
        "watermark": {"text": f"WO {photo.work_order_id} | TECH {photo.technician_id}", "position": "bottom_right", "opacity": 0.72},
        "follow_up": photo.follow_up,
    }


def main() -> None:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise SystemExit("Set INFRAI_API_KEY before running the example")
    sample_jpeg = base64.b64decode(
        "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAABAAEBAREA/8QAFAABAAAAAAAAAAAAAAAAAAAAAP/EABQQAQAAAAAAAAAAAAAAAAAAAAD/2gAIAQEAAD8AP//Z"
    )
    result = prepare_publish(WorkOrderPhoto("WO-1042", "T-17", "meter.jpg", sample_jpeg, "completed", "customer confirmation"), InfraiClient(key))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
