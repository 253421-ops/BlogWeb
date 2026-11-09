"""Traductores HTTP de métricas (Pydantic)."""
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Slug = Annotated[str, StringConstraints(max_length=80, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")]
Host = Annotated[str, StringConstraints(max_length=120, pattern=r"^[A-Za-z0-9.:-]+$")]


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")      # no se aceptan datos de más (no se puede colar una IP)
    event_id: UUID
    type: Literal["page_view", "scroll_depth", "time_on_page", "link_click"]
    session_id: UUID
    visitor_id: UUID = Field(default=None)
    path: Annotated[str, StringConstraints(max_length=300, pattern=r"^/\S*$")]
    post_slug: Slug = Field(default=None)
    referrer_host: Host = Field(default=None)
    target_host: Host = Field(default=None)
    value: int = Field(default=None, ge=0, le=3600)

    @model_validator(mode="after")
    def _by_type(self):
        if self.type == "scroll_depth" and self.value not in (25, 50, 75, 100):
            raise ValueError("scroll_depth requiere value 25, 50, 75 o 100")
        if self.type == "time_on_page" and self.value is None:
            raise ValueError("time_on_page requiere value (segundos)")
        if self.type == "link_click" and not self.target_host:
            raise ValueError("link_click requiere target_host")
        return self


class IngestIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[EventIn] = Field(min_length=1, max_length=20)


class IngestOut(BaseModel):
    received: int
    stored: int
