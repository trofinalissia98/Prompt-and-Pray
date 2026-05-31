from pydantic import BaseModel, Field
from typing import List

class ScenaVideo(BaseModel):
    numar_scena: int = Field(description="Numărul scenei")
    naratiune: str = Field(description="Textul narativ pentru TTS")
    text_ecran: str = Field(description="Text scurt pentru idee-cheie")
    emoji_vizual: str = Field(description="Emoji de fallback")
    culoare_fundal: List[int] = Field(description="Culoare de fundal RGB")
    prompt_imagine: str = Field(
        default="",
        description="Prompt în engleză pentru generarea unei imagini reprezentative"
    )

class ScriptVideo(BaseModel):
    titlu: str
    scene: List[ScenaVideo]