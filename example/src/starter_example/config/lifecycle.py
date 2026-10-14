"""Initialize only the demo schema during the managed startup lifecycle."""

import logging

from sqlalchemy.ext.asyncio import AsyncEngine

from pythonboot import autowired, component, ondestroy, postconstruct
from starter_example.domain.user import Base

logger = logging.getLogger(__name__)


@component
class DemoSchema:
    engine: AsyncEngine = autowired()
    ready: bool = False

    @postconstruct
    async def initialize(self) -> None:
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        self.ready = True
        logger.info("Example schema initialized")

    @ondestroy
    def close(self) -> None:
        self.ready = False
        logger.info("Example lifecycle closed")
