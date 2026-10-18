from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TaskPriority(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.media
    completed: bool = False

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str) -> str:
        title = title.strip()
        if not title:
            raise ValueError("O título não pode ficar vazio.")
        return title


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority | None = None
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str | None) -> str | None:
        if title is not None:
            title = title.strip()
            if not title:
                raise ValueError("O título não pode ficar vazio.")
        return title

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> "TaskUpdate":
        for field in ("title", "priority", "completed"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"O campo '{field}' não pode ser nulo.")
        return self


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    priority: TaskPriority
    completed: bool
    created_at: datetime
