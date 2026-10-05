"""Supervisor-oriented report endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies import get_ticket_service
from app.schemas import AgentResolutionTimeResponse, OpenTicketPriorityCountResponse, TicketResponse
from app.services import TicketService

router = APIRouter(prefix="/reports", tags=["reports"])
TicketServiceDependency = Annotated[TicketService, Depends(get_ticket_service)]


@router.get("/sla-breaches", response_model=list[TicketResponse])
def list_sla_breaches(service: TicketServiceDependency) -> list[dict]:
    return service.list_sla_breaches()


@router.get("/agent-resolution-times", response_model=list[AgentResolutionTimeResponse])
def average_agent_resolution_times(service: TicketServiceDependency) -> list[dict]:
    return service.average_resolution_times()


@router.get("/open-ticket-counts-by-priority", response_model=list[OpenTicketPriorityCountResponse])
def open_ticket_counts_by_priority(service: TicketServiceDependency) -> list[dict]:
    return service.open_ticket_counts_by_priority()
