"""文件上传接口。"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from starlette.concurrency import run_in_threadpool

from app.common.exceptions import BusinessException
from app.common.response import Response
from app.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.files import UploadResponse

router = APIRouter(prefix="/files", tags=["文件"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise BusinessException(
            message=f"不支持的文件类型，仅支持 {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    content = await file.read()
    if not content:
        raise BusinessException(message="上传文件为空")
    if len(content) > MAX_FILE_SIZE:
        raise BusinessException(message="文件不能超过 10MB")

    filename = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}{suffix}"
    target = UPLOAD_DIR / filename
    await run_in_threadpool(target.write_bytes, content)

    return Response.success(
        message="上传成功",
        data=UploadResponse(
            url=f"/uploads/{filename}", filename=file.filename or filename, size=len(content)
        ),
    )
