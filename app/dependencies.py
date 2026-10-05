"""FastAPI dependency factories; no database work occurs until a request."""
from app.repositories import InternalNoteRepository, TicketRepository
from app.services import TicketService


def get_ticket_service() -> TicketService:
    return TicketService(TicketRepository(), InternalNoteRepository())
