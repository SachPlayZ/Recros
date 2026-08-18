from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProfileUpdate(BaseModel):
    preferred_domains: list[str] = Field(default_factory=list)
    genres: list[str] = Field(default_factory=list)
    themes: list[str] = Field(default_factory=list)
    moods: list[str] = Field(default_factory=list)
    disliked_terms: list[str] = Field(default_factory=list)
    exploration: float = Field(default=0.5, ge=0, le=1)
    seed_item_ids: list[str] = Field(default_factory=list)


class Feedback(BaseModel):
    item_id: str
    action: Literal["like", "dislike", "save", "skip", "consume"]


class Credentials(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=200)
