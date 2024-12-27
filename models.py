from pydantic import BaseModel
from typing import List, Optional

# todo : 데이터 형식 알게 되면 형식 변경
class MetaData(BaseModel):
    cow_id: Optional[str] = "Unknown"
    birth_date: Optional[str] = "Unknown"
    breed: Optional[str] = "Unknown"
    weight: Optional[int] = 0

class DataField(BaseModel):
    type: Optional[str] = "Unknown"
    content: Optional[str] = "Unknown"
    description: Optional[str]

class CowData(BaseModel):
    barcode: str
    meta: MetaData
    data: List[DataField]

class TextData(BaseModel):
    content: str