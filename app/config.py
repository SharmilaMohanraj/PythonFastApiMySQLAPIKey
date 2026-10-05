"""Environment-backed service configuration without connection side effects."""
from dataclasses import dataclass
import os

URGENT_SLA_HOURS = 2
HIGH_SLA_HOURS = 8


@dataclass(frozen=True)
class Settings:
    mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "ticket_user")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "ticket_password")
    mysql_database: str = os.getenv("MYSQL_DATABASE", "ticket_db")


settings = Settings()
