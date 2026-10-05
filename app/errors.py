"""Domain errors deliberately translated at the HTTP boundary."""


class DomainError(Exception):
    status_code = 400
    code = "domain_error"
    client_message = "The request could not be completed."


class TicketNotFoundError(DomainError):
    status_code = 404
    code = "ticket_not_found"
    client_message = "The requested ticket was not found."

    def __init__(self, ticket_id: int):
        super().__init__(f"Ticket {ticket_id} was not found")
        self.ticket_id = ticket_id
