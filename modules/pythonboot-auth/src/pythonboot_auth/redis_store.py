"""Redis CAS updates account state and token indexes in one namespace hash slot."""

import hashlib
import json
import logging
from typing import Any

from redis.exceptions import RedisError
from pythonboot_redis import AsyncRedisClient, RedisClient
from pythonboot_auth.exceptions import AuthStorageError
from pythonboot_auth.storage import AsyncSessionStore, SessionStore, State

logger = logging.getLogger(__name__)

_CAS = """
local previous = redis.call('GET', KEYS[1])
local old = nil
if previous then
    old = cjson.decode(previous)
    if old.revision ~= ARGV[1] then return 0 end
elseif ARGV[1] ~= '' then
    return 0
end
local state = cjson.decode(ARGV[2])
local now = tonumber(redis.call('TIME')[1])
if old then
    for digest, _ in pairs(old.tokens) do
        if not state.tokens[digest] then redis.call('DEL', ARGV[5] .. digest) end
    end
end
local count = 0
for digest, record in pairs(state.tokens) do
    local ttl = math.ceil(record.expires_at - now)
    if ttl > 0 then
        redis.call('SET', ARGV[5] .. digest, ARGV[4], 'EX', ttl)
        count = count + 1
    else
        redis.call('DEL', ARGV[5] .. digest)
    end
end
if count == 0 then
    redis.call('DEL', KEYS[1])
else
    redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
end
return 1
"""


class _RedisKeys:
    def __init__(self, key_prefix: str) -> None:
        if not key_prefix or "{" in key_prefix or "}" in key_prefix:
            raise ValueError("Auth Redis key_prefix must be non-empty and contain no hash-tag braces")
        tag = hashlib.sha256(key_prefix.encode()).hexdigest()[:24]
        self.prefix = f"{key_prefix}{{{tag}}}:"

    def account_key(self, account_id: str) -> str:
        return f"{self.prefix}account:{account_id}"

    def token_key(self, digest: str) -> str:
        return f"{self.prefix}token:{digest}"

    def arguments(self, account_id: str, revision: str | None, state: State, ttl: int) -> tuple[Any, ...]:
        return (
            _CAS, 1, self.account_key(account_id), revision or "",
            json.dumps(state, allow_nan=False, separators=(",", ":")), ttl,
            account_id, f"{self.prefix}token:",
        )

    @staticmethod
    def decode(value: Any) -> State | None:
        if value is None:
            return None
        try:
            state = json.loads(value)
            if not isinstance(state, dict) or not isinstance(state.get("tokens"), dict):
                raise ValueError("Invalid account state")
            return state
        except (TypeError, ValueError, UnicodeError) as error:
            raise AuthStorageError("Invalid authentication state in Redis") from error

    @staticmethod
    def identity(value: Any) -> str | None:
        if value is None:
            return None
        return value.decode("utf-8") if isinstance(value, bytes) else value


class RedisSessionStore(_RedisKeys, SessionStore):
    """The injected client remains owned and closed by its original provider."""

    def __init__(self, client: RedisClient, *, key_prefix: str = "pythonboot:auth:") -> None:
        super().__init__(key_prefix)
        self.client = client

    def get(self, account_id: str) -> State | None:
        try:
            return self.decode(self.client.get(self.account_key(account_id)))
        except RedisError as error:
            logger.error("Authentication Redis state read failed.")
            raise AuthStorageError("Authentication Redis state read failed") from error

    def lookup(self, token_digest: str) -> str | None:
        try:
            return self.identity(self.client.get(self.token_key(token_digest)))
        except RedisError as error:
            logger.error("Authentication Redis token lookup failed.")
            raise AuthStorageError("Authentication Redis token lookup failed") from error

    def compare_and_set(self, account_id: str, revision: str | None, state: State, ttl: int) -> bool:
        try:
            return bool(self.client.eval(*self.arguments(account_id, revision, state, ttl)))
        except RedisError as error:
            logger.error("Authentication Redis atomic update failed.")
            raise AuthStorageError("Authentication Redis atomic update failed") from error


class AsyncRedisSessionStore(_RedisKeys, AsyncSessionStore):
    def __init__(self, client: AsyncRedisClient, *, key_prefix: str = "pythonboot:auth:") -> None:
        super().__init__(key_prefix)
        self.client = client

    async def get(self, account_id: str) -> State | None:
        try:
            return self.decode(await self.client.get(self.account_key(account_id)))
        except RedisError as error:
            logger.error("Authentication Redis state read failed.")
            raise AuthStorageError("Authentication Redis state read failed") from error

    async def lookup(self, token_digest: str) -> str | None:
        try:
            return self.identity(await self.client.get(self.token_key(token_digest)))
        except RedisError as error:
            logger.error("Authentication Redis token lookup failed.")
            raise AuthStorageError("Authentication Redis token lookup failed") from error

    async def compare_and_set(self, account_id: str, revision: str | None, state: State, ttl: int) -> bool:
        try:
            return bool(await self.client.eval(*self.arguments(account_id, revision, state, ttl)))
        except RedisError as error:
            logger.error("Authentication Redis atomic update failed.")
            raise AuthStorageError("Authentication Redis atomic update failed") from error
