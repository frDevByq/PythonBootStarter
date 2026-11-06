"""Business-owned dynamic role and permission lookup contracts."""

from abc import ABC, abstractmethod
from collections.abc import Sequence


class StpInterface(ABC):
    @abstractmethod
    def get_permission_list(self, login_id: str, login_type: str) -> Sequence[str]:
        raise NotImplementedError

    @abstractmethod
    def get_role_list(self, login_id: str, login_type: str) -> Sequence[str]:
        raise NotImplementedError


class AsyncStpInterface(ABC):
    @abstractmethod
    async def get_permission_list(self, login_id: str, login_type: str) -> Sequence[str]:
        raise NotImplementedError

    @abstractmethod
    async def get_role_list(self, login_id: str, login_type: str) -> Sequence[str]:
        raise NotImplementedError
