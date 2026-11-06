"""Public session metadata excludes credential digests and business session values."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionInfo:
    session_id: str
    login_id: str
    login_type: str
    device: str
    created_at: float
    last_activity: float
    expires_at: float
    status: str


@dataclass(frozen=True)
class LoginResult:
    token: str = field(repr=False)
    csrf_token: str = field(repr=False)
    session: SessionInfo
