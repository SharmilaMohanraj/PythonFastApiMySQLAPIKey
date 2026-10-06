"""MySQL data access for ticket satisfaction feedback."""
from datetime import datetime, timezone
from typing import Any

import mysql.connector

from app.db import connection
from app.errors import FeedbackAlreadyExistsError


def _with_utc_timestamp(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is not None:
        created_at = record.get("created_at")
        if created_at is not None and created_at.tzinfo is None:
            record["created_at"] = created_at.replace(tzinfo=timezone.utc)
    return record


class FeedbackRepository:
    """Encapsulates feedback persistence and reporting queries."""

    def get_ticket_for_feedback(self, ticket_id: int) -> dict[str, Any] | None:
        with connection() as database_connection:
            cursor = database_connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    "SELECT id, customer_id, status FROM tickets WHERE id = %s", (ticket_id,)
                )
                return cursor.fetchone()
            finally:
                cursor.close()

    def feedback_exists(self, ticket_id: int) -> bool:
        with connection() as database_connection:
            cursor = database_connection.cursor()
            try:
                cursor.execute("SELECT 1 FROM feedback WHERE ticket_id = %s", (ticket_id,))
                return cursor.fetchone() is not None
            finally:
                cursor.close()

    def create_feedback(self, ticket_id: int, rating: int, comment: str | None) -> dict[str, Any]:
        now = datetime.utcnow()
        try:
            with connection() as database_connection:
                cursor = database_connection.cursor()
                try:
                    cursor.execute(
                        "INSERT INTO feedback (ticket_id, rating, comment, created_at) VALUES (%s, %s, %s, %s)",
                        (ticket_id, rating, comment, now),
                    )
                    feedback_id = cursor.lastrowid
                finally:
                    cursor.close()
        except mysql.connector.IntegrityError as error:
            if error.errno == 1062:
                raise FeedbackAlreadyExistsError(ticket_id) from error
            raise
        with connection() as database_connection:
            cursor = database_connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM feedback WHERE id = %s", (feedback_id,))
                feedback = _with_utc_timestamp(cursor.fetchone())
            finally:
                cursor.close()
        if feedback is None:
            raise RuntimeError("Created feedback could not be retrieved")
        return feedback

    def average_rating_for_agent(self, agent_id: str) -> float | None:
        with connection() as database_connection:
            cursor = database_connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """SELECT AVG(f.rating) AS average_rating FROM feedback AS f
                    INNER JOIN tickets AS t ON t.id = f.ticket_id
                    WHERE t.assigned_agent_id = %s AND t.status IN ('RESOLVED', 'CLOSED')""",
                    (agent_id,),
                )
                value = cursor.fetchone()["average_rating"]
                return float(value) if value is not None else None
            finally:
                cursor.close()

    def low_rated_tickets(self, offset: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        return self._page(
            """SELECT t.id AS ticket_id, f.rating, f.comment FROM feedback AS f
            INNER JOIN tickets AS t ON t.id = f.ticket_id WHERE f.rating <= 2
            ORDER BY f.created_at, f.id LIMIT %s OFFSET %s""",
            "SELECT COUNT(*) AS total FROM feedback WHERE rating <= 2",
            offset,
            limit,
        )

    def pending_feedback_tickets(self, offset: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        return self._page(
            """SELECT t.id AS ticket_id, TRUE AS pending_feedback FROM tickets AS t
            LEFT JOIN feedback AS f ON f.ticket_id = t.id
            WHERE t.status = 'CLOSED' AND f.ticket_id IS NULL
            ORDER BY t.id LIMIT %s OFFSET %s""",
            """SELECT COUNT(*) AS total FROM tickets AS t LEFT JOIN feedback AS f ON f.ticket_id = t.id
            WHERE t.status = 'CLOSED' AND f.ticket_id IS NULL""",
            offset,
            limit,
        )

    def _page(self, page_sql: str, count_sql: str, offset: int, limit: int) -> tuple[list[dict[str, Any]], int]:
        with connection() as database_connection:
            cursor = database_connection.cursor(dictionary=True)
            try:
                cursor.execute(count_sql)
                total = cursor.fetchone()["total"]
                cursor.execute(page_sql, (limit, offset))
                return cursor.fetchall(), int(total)
            finally:
                cursor.close()
