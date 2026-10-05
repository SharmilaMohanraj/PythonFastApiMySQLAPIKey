"""Direct MySQL connection and idempotent schema management."""
from contextlib import contextmanager
from collections.abc import Generator
from typing import Any

import mysql.connector
from mysql.connector import MySQLConnection

from app.config import Settings, settings


@contextmanager
def connection(config: Settings = settings) -> Generator[MySQLConnection, None, None]:
    database_connection: MySQLConnection | None = None
    try:
        database_connection = mysql.connector.connect(
            host=config.mysql_host, port=config.mysql_port, user=config.mysql_user,
            password=config.mysql_password, database=config.mysql_database,
        )
        yield database_connection
        database_connection.commit()
    except mysql.connector.Error:
        if database_connection is not None:
            database_connection.rollback()
        raise
    finally:
        if database_connection is not None and database_connection.is_connected():
            database_connection.close()


def initialize_database(config: Settings = settings) -> None:
    """Create the ticket schema on startup; safe to repeat on every boot."""
    statements: tuple[str, ...] = (
        """CREATE TABLE IF NOT EXISTS tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject VARCHAR(255) NOT NULL,
            description TEXT NOT NULL,
            priority ENUM('LOW','MEDIUM','HIGH','URGENT') NOT NULL,
            status ENUM('OPEN','IN_PROGRESS','RESOLVED','CLOSED') NOT NULL DEFAULT 'OPEN',
            assigned_agent_id VARCHAR(255) NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            resolved_at DATETIME NULL,
            INDEX idx_tickets_priority_status (priority, status),
            INDEX idx_tickets_assignee_resolution (assigned_agent_id, resolved_at)
        ) ENGINE=InnoDB""",
        """CREATE TABLE IF NOT EXISTS internal_notes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticket_id INT NOT NULL,
            author_agent_id VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME NOT NULL,
            CONSTRAINT fk_internal_notes_ticket FOREIGN KEY (ticket_id)
                REFERENCES tickets(id) ON DELETE CASCADE,
            INDEX idx_notes_ticket_created (ticket_id, created_at, id)
        ) ENGINE=InnoDB""",
    )
    with connection(config) as database_connection:
        cursor = database_connection.cursor()
        try:
            for statement in statements:
                cursor.execute(statement)
        finally:
            cursor.close()
