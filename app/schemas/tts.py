from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(min_length=1)
    return_visemes: bool = True
