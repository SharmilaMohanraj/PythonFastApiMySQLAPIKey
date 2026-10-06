"""API-key authentication and role authorization dependencies."""
from dataclasses import dataclass
import hmac
import json
import os
from typing import Annotated, Callable

from fastapi import Depends, Header

from app.errors import AuthenticationRequiredError, AuthorizationDeniedError

_ALLOWED_ROLES = frozenset({"customer", "agent", "supervisor"})


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Identity resolved from a server-configured opaque API key."""

    identifier: str
    role: str


def _configured_principals() -> dict[str, AuthenticatedPrincipal]:
    """Parse configured API keys without accepting caller-provided identity claims."""
    raw_keys = os.getenv("AUTH_API_KEYS")
    if not raw_keys:
        raise AuthenticationRequiredError("API-key authentication is not configured")
    try:
        configured_keys = json.loads(raw_keys)
    except json.JSONDecodeError as error:
        raise AuthenticationRequiredError("API-key authentication is not configured") from error

    if not isinstance(configured_keys, dict):
        raise AuthenticationRequiredError("API-key authentication is not configured")

    principals: dict[str, AuthenticatedPrincipal] = {}
    for api_key, principal in configured_keys.items():
        if not isinstance(api_key, str) or not isinstance(principal, dict):
            continue
        identifier = principal.get("id")
        role = principal.get("role")
        if isinstance(identifier, str) and identifier and isinstance(role, str) and role.lower() in _ALLOWED_ROLES:
            principals[api_key] = AuthenticatedPrincipal(identifier=identifier, role=role.lower())
    if not principals:
        raise AuthenticationRequiredError("API-key authentication is not configured")
    return principals


def get_authenticated_principal(
    api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> AuthenticatedPrincipal:
    """Authenticate an opaque API key against the server-side principal mapping."""
    if not api_key:
        raise AuthenticationRequiredError("Missing API key")

    # Compare every configured key so a malformed request cannot select an identity claim.
    matched_principal: AuthenticatedPrincipal | None = None
    for configured_key, principal in _configured_principals().items():
        if hmac.compare_digest(api_key, configured_key):
            matched_principal = principal
    if matched_principal is None:
        raise AuthenticationRequiredError("Invalid API key")
    return matched_principal


def require_roles(*allowed_roles: str) -> Callable[[AuthenticatedPrincipal], AuthenticatedPrincipal]:
    """Build a dependency that permits only the supplied application roles."""
    def authorize(
        principal: Annotated[AuthenticatedPrincipal, Depends(get_authenticated_principal)],
    ) -> AuthenticatedPrincipal:
        if principal.role not in allowed_roles:
            raise AuthorizationDeniedError(f"Role {principal.role} is not permitted")
        return principal

    return authorize
