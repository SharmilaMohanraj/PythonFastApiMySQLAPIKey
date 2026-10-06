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


class AuthenticationRequiredError(DomainError):
    status_code = 401
    code = "authentication_required"
    client_message = "Authentication is required."


class AuthorizationDeniedError(DomainError):
    status_code = 403
    code = "authorization_denied"
    client_message = "You are not authorized to perform this action."


class TicketNotClosedError(DomainError):
    status_code = 409
    code = "ticket_not_closed"
    client_message = "Feedback can only be submitted for a closed ticket."


class FeedbackAlreadyExistsError(DomainError):
    status_code = 409
    code = "feedback_already_exists"
    client_message = "Feedback has already been submitted for this ticket."

    def __init__(self, ticket_id: int):
        super().__init__(f"Feedback already exists for ticket {ticket_id}")
        self.ticket_id = ticket_id
