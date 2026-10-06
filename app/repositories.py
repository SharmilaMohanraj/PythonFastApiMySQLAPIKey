"""Parameterized MySQL persistence repositories."""
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config import HIGH_SLA_HOURS, URGENT_SLA_HOURS
from app.db import connection


def _utc_values(record: dict[str, Any] | None) -> dict[str, Any] | None:
    if record is None:
        return None
    for field in ("created_at", "updated_at", "resolved_at"):
        value = record.get(field)
        if value is not None and value.tzinfo is None:
            record[field] = value.replace(tzinfo=timezone.utc)
    return record


class TicketRepository:
    def create_ticket(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.utcnow()
        sql = """INSERT INTO tickets (subject, description, priority, customer_id, status, created_at, updated_at)
                 VALUES (%s, %s, %s, %s, 'OPEN', %s, %s)"""
        with connection() as database_connection:
            cursor = database_connection.cursor()
            try:
                cursor.execute(sql, (payload["subject"], payload["description"], payload["priority"], payload.get("customer_id"), now, now))
                ticket_id = cursor.lastrowid
            finally:
                cursor.close()
        result = self.get_ticket(ticket_id)
        if result is None:
            raise RuntimeError("Created ticket could not be retrieved")
        return result

    def get_ticket(self, ticket_id: int) -> dict[str, Any] | None:
        with connection() as database_connection:
            cursor = database_connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
                return _utc_values(cursor.fetchone())
            finally:
                cursor.close()

    def assign_ticket(self, ticket_id: int, agent_id: str) -> dict[str, Any] | None:
        return self._update(ticket_id, "assigned_agent_id = %s, updated_at = %s", (agent_id, datetime.utcnow()))

    def update_ticket_status(self, ticket_id: int, status: str) -> dict[str, Any] | None:
        existing = self.get_ticket(ticket_id)
        if existing is None:
            return None
        resolved_at = existing["resolved_at"]
        if status == "RESOLVED":
            resolved_at = datetime.utcnow()
        return self._update(ticket_id, "status = %s, resolved_at = %s, updated_at = %s", (status, resolved_at, datetime.utcnow()))

    def _update(self, ticket_id: int, assignments: str, values: tuple[Any, ...]) -> dict[str, Any] | None:
        with connection() as database_connection:
            cursor = database_connection.cursor()
            try:
                cursor.execute(f"UPDATE tickets SET {assignments} WHERE id = %s", (*values, ticket_id))
                found = cursor.rowcount == 1
            finally:
                cursor.close()
        return self.get_ticket(ticket_id) if found else None

    def list_sla_breaches(self, now: datetime) -> list[dict[str, Any]]:
        urgent_deadline = now - timedelta(hours=URGENT_SLA_HOURS)
        high_deadline = now - timedelta(hours=HIGH_SLA_HOURS)
        sql = """SELECT * FROM tickets WHERE
            (priority = 'URGENT' AND ((resolved_at IS NULL AND created_at < %s)
                OR TIMESTAMPDIFF(SECOND, created_at, resolved_at) > %s))
            OR (priority = 'HIGH' AND ((resolved_at IS NULL AND created_at < %s)
                OR TIMESTAMPDIFF(SECOND, created_at, resolved_at) > %s))
            ORDER BY created_at, id"""
        return self._many(sql, (urgent_deadline, URGENT_SLA_HOURS * 3600, high_deadline, HIGH_SLA_HOURS * 3600))

    def average_resolution_times(self) -> list[dict[str, Any]]:
        return self._many("""SELECT assigned_agent_id, AVG(TIMESTAMPDIFF(MICROSECOND, created_at, resolved_at) / 1000000.0) AS average_resolution_seconds
            FROM tickets WHERE resolved_at IS NOT NULL AND assigned_agent_id IS NOT NULL
            GROUP BY assigned_agent_id ORDER BY assigned_agent_id""", ())

    def open_ticket_counts_by_priority(self) -> list[dict[str, Any]]:
        return self._many("SELECT priority, COUNT(*) AS count FROM tickets WHERE status = 'OPEN' GROUP BY priority ORDER BY priority", ())

    def _many(self, sql: str, values: tuple[Any, ...]) -> list[dict[str, Any]]:
        with connection() as database_connection:
            cursor = database_connection.cursor(dictionary=True)
            try:
                cursor.execute(sql, values)
                return [_utc_values(row) for row in cursor.fetchall()]
            finally:
                cursor.close()


class InternalNoteRepository:
    def create_note(self, ticket_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.utcnow()
        with connection() as database_connection:
            cursor = database_connection.cursor()
            try:
                cursor.execute("INSERT INTO internal_notes (ticket_id, author_agent_id, content, created_at) VALUES (%s, %s, %s, %s)",
                               (ticket_id, payload["author_agent_id"], payload["content"], now))
                note_id = cursor.lastrowid
                cursor.execute("UPDATE tickets SET updated_at = %s WHERE id = %s", (now, ticket_id))
            finally:
                cursor.close()
        results = self.list_for_ticket(ticket_id)
        return next(note for note in results if note["id"] == note_id)

    def list_for_ticket(self, ticket_id: int) -> list[dict[str, Any]]:
        with connection() as database_connection:
            cursor = database_connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT * FROM internal_notes WHERE ticket_id = %s ORDER BY created_at, id", (ticket_id,))
                return [_utc_values(row) for row in cursor.fetchall()]
            finally:
                cursor.close()
