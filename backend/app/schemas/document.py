import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DocumentChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chunk_index: int
    content: str
    page_number: Optional[int]
    access_level: str


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str
    file_type: str
    department_id: int
    access_level: str
    uploaded_by: int
    status: str
    created_at: datetime.datetime
    chunks: Optional[List[DocumentChunkOut]] = None
