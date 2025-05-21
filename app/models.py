from pydantic import BaseModel, Field, validator
from typing import List

class WeatherSummary(BaseModel):
    summary: str = Field(..., description="A summary of the weather conditions, suitable for kids. Can be a paragraph or HTML-formatted content with multiple sections.")

    @validator("summary")
    def validate_summary(cls, v):
        # Check if this is HTML content
        is_html = "<h3>" in v or "<p>" in v
        
        if is_html:
            # For HTML content, just ensure it's not empty
            if len(v.strip()) < 20:
                raise ValueError("Summary is too short; must have meaningful content.")
        else:
            # For plain text, ensure it's a proper paragraph
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
