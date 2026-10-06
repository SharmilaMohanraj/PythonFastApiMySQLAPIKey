"""Wire-format DTOs and API validation models."""
from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: NonEmptyText
    description: NonEmptyText
    priority: Priority


class FeedbackCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=65535)


class FeedbackResponse(BaseModel):
    id: int
    ticket_id: int
    rating: int
    comment: str | None
    created_at: datetime


class AgentSatisfactionResponse(BaseModel):
    agent_id: str
    average_rating: float | None


class LowRatedTicketResponse(BaseModel):
    ticket_id: int
    rating: int
    comment: str | None


class PendingFeedbackTicketResponse(BaseModel):
    ticket_id: int
    pending_feedback: bool


class OffsetPage(BaseModel):
    items: list
    total: int
    limit: int
    offset: int


class LowRatedTicketPage(OffsetPage):
    items: list[LowRatedTicketResponse]


class PendingFeedbackTicketPage(OffsetPage):
    items: list[PendingFeedbackTicketResponse]


class TicketAssignmentUpdate(BaseModel):
    assigned_agent_id: NonEmptyText


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class InternalNoteCreate(BaseModel):
    author_agent_id: NonEmptyText
    content: NonEmptyText


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    subject: str
    description: str
    priority: Priority
    status: TicketStatus
    assigned_agent_id: str | None
    customer_id: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None


class InternalNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    author_agent_id: str
    content: str
    created_at: datetime


class TicketDetailResponse(TicketResponse):
    notes: list[InternalNoteResponse] = Field(default_factory=list)


class AgentResolutionTimeResponse(BaseModel):
    assigned_agent_id: str
    average_resolution_seconds: float


class OpenTicketPriorityCountResponse(BaseModel):
    priority: Priority
    count: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    timestamp: datetime
    correlation_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
