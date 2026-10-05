"""Ticket resource endpoints with request parsing only."""
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.dependencies import get_ticket_service
from app.schemas import (InternalNoteCreate, InternalNoteResponse, TicketAssignmentUpdate,
                         TicketCreate, TicketDetailResponse, TicketResponse, TicketStatusUpdate)
from app.services import TicketService

router = APIRouter(tags=["tickets"])
TicketServiceDependency = Annotated[TicketService, Depends(get_ticket_service)]


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, service: TicketServiceDependency) -> dict:
    return service.create_ticket(payload)


@router.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(ticket_id: int, service: TicketServiceDependency) -> dict:
    return service.get_ticket_detail(ticket_id)


@router.patch("/tickets/{ticket_id}/assignment", response_model=TicketResponse)
def assign_ticket(ticket_id: int, payload: TicketAssignmentUpdate, service: TicketServiceDependency) -> dict:
    return service.assign_ticket(ticket_id, payload)


@router.patch("/tickets/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(ticket_id: int, payload: TicketStatusUpdate, service: TicketServiceDependency) -> dict:
    return service.update_ticket_status(ticket_id, payload)


@router.post("/tickets/{ticket_id}/notes", response_model=InternalNoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(ticket_id: int, payload: InternalNoteCreate, service: TicketServiceDependency) -> dict:
    return service.create_note(ticket_id, payload)
