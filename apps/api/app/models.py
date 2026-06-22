from typing import Any

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    textbook_version: str = Field(min_length=1)
    volume: str = Field(min_length=1)
    lesson_type: str = Field(min_length=1)


class NodeGenerateRequest(BaseModel):
    model: str | None = None
    size: str | None = None
    mode: str | None = None
    full_run: bool | None = None
    knowledge_point_id: str | None = None
    image_limit: int | None = None
    min_successful_images: int | None = None
    image_quality: str | None = None
    image_size: str | None = None
    image_model: str | None = None
    video_shot_limit: int | None = None
    clip_limit: int | None = None

    def to_options(self) -> dict[str, Any]:
        return dump_model(self, exclude_none=True)


class NodeEditRequest(BaseModel):
    content: dict[str, Any]


class NodeApproveRequest(BaseModel):
    approve_note: str | None = None
    override_warning_rule_ids: list[str] = Field(default_factory=list)
    override_reason: str | None = None


class FeedbackRequest(BaseModel):
    feedback_type: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


def dump_model(model: BaseModel, *, exclude_none: bool = False) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=exclude_none)
    return model.dict(exclude_none=exclude_none)
