"""Ticket business operations composed from persistence repositories."""
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status

from app.repositories import InternalNoteRepository, TicketRepository
from app.schemas import InternalNoteCreate, TicketAssignmentUpdate, TicketCreate, TicketStatusUpdate


class TicketService:
    def __init__(self, ticket_repository: TicketRepository, note_repository: InternalNoteRepository) -> None:
        self._tickets = ticket_repository
        self._notes = note_repository

    def create_ticket(self, payload: TicketCreate) -> dict[str, Any]:
        return self._tickets.create_ticket(payload.model_dump(mode="json"))

    def get_ticket_detail(self, ticket_id: int) -> dict[str, Any]:
        ticket = self._require_ticket(ticket_id)
        ticket["notes"] = self._notes.list_for_ticket(ticket_id)
        return ticket

    def assign_ticket(self, ticket_id: int, payload: TicketAssignmentUpdate) -> dict[str, Any]:
        ticket = self._tickets.assign_ticket(ticket_id, payload.assigned_agent_id)
        return self._require_result(ticket, ticket_id)

    def update_ticket_status(self, ticket_id: int, payload: TicketStatusUpdate) -> dict[str, Any]:
        ticket = self._tickets.update_ticket_status(ticket_id, payload.status.value)
        return self._require_result(ticket, ticket_id)

    def create_note(self, ticket_id: int, payload: InternalNoteCreate) -> dict[str, Any]:
        self._require_ticket(ticket_id)
        return self._notes.create_note(ticket_id, payload.model_dump())

    def list_sla_breaches(self) -> list[dict[str, Any]]:
        return self._tickets.list_sla_breaches(datetime.now(timezone.utc).replace(tzinfo=None))

    def average_resolution_times(self) -> list[dict[str, Any]]:
        return self._tickets.average_resolution_times()

    def open_ticket_counts_by_priority(self) -> list[dict[str, Any]]:
        return self._tickets.open_ticket_counts_by_priority()

    def _require_ticket(self, ticket_id: int) -> dict[str, Any]:
        return self._require_result(self._tickets.get_ticket(ticket_id), ticket_id)

    @staticmethod
    def _require_result(ticket: dict[str, Any] | None, ticket_id: int) -> dict[str, Any]:
        if ticket is None:
            raise ticket_not_found_http_exception(ticket_id)
        return ticket


def ticket_not_found_http_exception(ticket_id: int) -> HTTPException:
    """Compatibility helper for callers needing a FastAPI-native 404."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket {ticket_id} not found")
