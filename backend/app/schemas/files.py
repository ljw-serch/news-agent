"""文件上传模型。"""

from pydantic import BaseModel


class UploadResponse(BaseModel):
    url: str
    filename: str
    size: int
