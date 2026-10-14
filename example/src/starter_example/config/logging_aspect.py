"""Log synchronous and asynchronous business calls without changing their signatures."""

import logging

from pythonboot import JoinPoint, after_throwing, annotation, aspect, before

logger = logging.getLogger(__name__)
logged = annotation("starter_example_logged")


@aspect
class LoggingAspect:
    @before(logged)
    def call(self, join_point: JoinPoint) -> None:
        logger.info("Calling %s", join_point.qualified_name)

    @after_throwing(logged)
    def failed(self, join_point: JoinPoint, error: BaseException) -> None:
        logger.warning("Call failed %s: %s", join_point.qualified_name, error)
