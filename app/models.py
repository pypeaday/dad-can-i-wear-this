from pydantic import BaseModel, Field, validator
from typing import List

class WeatherSummary(BaseModel):
    summary: str = Field(..., description="A paragraph summary of the weather conditions, suitable for kids.")

    @validator("summary")
    def summary_is_paragraph(cls, v):
        # Ensure summary is a paragraph (not a list, not too short)
        if len(v.split()) < 12:
            raise ValueError("Summary is too short; must be a full paragraph.")
        if "\n" in v and v.count("\n") > 2:
            raise ValueError("Summary should be a single paragraph, not a list.")
        return v

class ClothingRecommendations(BaseModel):
    safety: List[str] = Field(..., description="List of safety recommendations.")
    clothing: List[str] = Field(..., description="List of clothing recommendations, each with an emoji and clear language.")

    @validator("clothing", each_item=True)
    def clothing_format(cls, v):
        # Ensure each item starts with an emoji and category
        if not v or not v[0].encode('utf-8').isalpha() and not v[0].isascii():
            raise ValueError("Each clothing recommendation should start with an emoji.")
        if ":" not in v:
            raise ValueError("Each clothing recommendation should contain a category, e.g., 'Base Layer: ...'")
        return v
