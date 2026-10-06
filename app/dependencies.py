"""FastAPI dependency factories; no database work occurs until a request."""
from app.feedback_repository import FeedbackRepository
from app.feedback_service import FeedbackService
from app.repositories import InternalNoteRepository, TicketRepository
from app.services import TicketService


def get_ticket_service() -> TicketService:
    return TicketService(TicketRepository(), InternalNoteRepository())


def get_feedback_service() -> FeedbackService:
    return FeedbackService(FeedbackRepository())
