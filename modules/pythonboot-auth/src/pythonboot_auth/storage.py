"""Atomic account-state storage contracts and application-owned memory backends."""

from abc import ABC, abstractmethod
from copy import deepcopy
import logging
from threading import RLock
import time
from typing import Any

logger = logging.getLogger(__name__)
State = dict[str, Any]


class SessionStore(ABC):
    @abstractmethod
    def get(self, account_id: str) -> State | None:
        raise NotImplementedError

    @abstractmethod
    def lookup(self, token_digest: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def compare_and_set(self, account_id: str, revision: str | None, state: State, ttl: int) -> bool:
        """Atomically replace account state and its token index if revision matches."""
        raise NotImplementedError


class AsyncSessionStore(ABC):
    @abstractmethod
    async def get(self, account_id: str) -> State | None:
        raise NotImplementedError

    @abstractmethod
    async def lookup(self, token_digest: str) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def compare_and_set(self, account_id: str, revision: str | None, state: State, ttl: int) -> bool:
        raise NotImplementedError


class MemorySessionStore(SessionStore):
    def __init__(self) -> None:
        self._lock = RLock()
        self._accounts: dict[str, tuple[float, State]] = {}
        self._tokens: dict[str, str] = {}

    def _prune(self) -> None:
        now = time.time()
        for account_id, (deadline, state) in tuple(self._accounts.items()):
            if deadline <= now:
                self._accounts.pop(account_id)
                for digest in state["tokens"]:
                    self._tokens.pop(digest, None)

    def get(self, account_id: str) -> State | None:
        with self._lock:
            self._prune()
            value = self._accounts.get(account_id)
            return deepcopy(value[1]) if value else None

    def lookup(self, token_digest: str) -> str | None:
        with self._lock:
            self._prune()
            account_id = self._tokens.get(token_digest)
            if account_id is None:
                return None
            record = self._accounts[account_id][1]["tokens"].get(token_digest)
            return account_id if record and record["expires_at"] > time.time() else None

    def compare_and_set(self, account_id: str, revision: str | None, state: State, ttl: int) -> bool:
        with self._lock:
            self._prune()
            previous = self._accounts.get(account_id)
            old = previous[1] if previous else None
            if (old["revision"] if old else None) != revision:
                return False
            for digest in old["tokens"] if old else ():
                self._tokens.pop(digest, None)
            if state["tokens"]:
                self._accounts[account_id] = (time.time() + ttl, deepcopy(state))
                for digest in state["tokens"]:
                    self._tokens[digest] = account_id
            else:
                self._accounts.pop(account_id, None)
            return True

    def close(self) -> None:
        with self._lock:
            self._accounts.clear()
            self._tokens.clear()
        logger.info("Closed authentication memory store.")


class AsyncMemorySessionStore(AsyncSessionStore):
    """Short in-memory critical sections contain no I/O and no awaited operations."""

    def __init__(self) -> None:
        self._store = MemorySessionStore()

    async def get(self, account_id: str) -> State | None:
        return self._store.get(account_id)

    async def lookup(self, token_digest: str) -> str | None:
        return self._store.lookup(token_digest)

    async def compare_and_set(self, account_id: str, revision: str | None, state: State, ttl: int) -> bool:
        return self._store.compare_and_set(account_id, revision, state, ttl)

    async def close(self) -> None:
        self._store.close()
