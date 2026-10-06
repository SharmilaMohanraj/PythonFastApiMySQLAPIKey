"""Business rules for one-time ticket satisfaction feedback."""
import logging
from typing import Any

from app.auth import AuthenticatedPrincipal
from app.errors import AuthorizationDeniedError, FeedbackAlreadyExistsError, TicketNotClosedError, TicketNotFoundError
from app.feedback_repository import FeedbackRepository
from app.schemas import FeedbackCreate

logger = logging.getLogger(__name__)


class FeedbackService:
    """Coordinates feedback validation with repository operations."""

    def __init__(self, repository: FeedbackRepository) -> None:
        self._repository = repository

    def submit(self, ticket_id: int, payload: FeedbackCreate, principal: AuthenticatedPrincipal) -> dict[str, Any]:
        ticket = self._repository.get_ticket_for_feedback(ticket_id)
        if ticket is None:
            raise TicketNotFoundError(ticket_id)
        if ticket["status"] != "CLOSED":
            raise TicketNotClosedError(f"Ticket {ticket_id} has status {ticket['status']}")
        if ticket["customer_id"] != principal.identifier:
            raise AuthorizationDeniedError(f"Customer does not own ticket {ticket_id}")
        if self._repository.feedback_exists(ticket_id):
            raise FeedbackAlreadyExistsError(ticket_id)
        feedback = self._repository.create_feedback(ticket_id, payload.rating, payload.comment)
        logger.info("feedback submitted ticket_id=%s feedback_id=%s", ticket_id, feedback["id"])
        return feedback

    def agent_satisfaction(self, agent_id: str) -> dict[str, Any]:
        return {"agent_id": agent_id, "average_rating": self._repository.average_rating_for_agent(agent_id)}

    def low_rated_tickets(self, offset: int, limit: int) -> dict[str, Any]:
        items, total = self._repository.low_rated_tickets(offset, limit)
        return {"items": items, "total": total, "offset": offset, "limit": limit}

    def pending_feedback_tickets(self, offset: int, limit: int) -> dict[str, Any]:
        items, total = self._repository.pending_feedback_tickets(offset, limit)
        return {"items": items, "total": total, "offset": offset, "limit": limit}
