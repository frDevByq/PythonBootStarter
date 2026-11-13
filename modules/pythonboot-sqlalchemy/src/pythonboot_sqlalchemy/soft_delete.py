"""Application-scoped logical deletion for native SQLAlchemy Sessions."""

from typing import Any

from sqlalchemy import Select, event, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria

from pythonboot_sqlalchemy.properties import SoftDeleteProperties


class SoftDeleteMixin:
    """Mark a mapped model for logical deletion; the application declares its column."""


class SoftDeleteSession(Session):
    """Keep native transactions while filtering and converting opt-in model deletions."""

    def __init__(self, *args: Any, soft_delete: SoftDeleteProperties | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.soft_delete = soft_delete or SoftDeleteProperties()
        self._physical_deletions: set[Any] = set()
        if self.soft_delete.enabled:
            event.listen(self, "do_orm_execute", self._filter_statement)
            event.listen(self, "before_flush", self._convert_deletions)
            event.listen(self, "after_soft_rollback", self._clear_physical_deletions)
            event.listen(self, "after_commit", self._clear_physical_deletions)

    def _filter_statement(self, state: ORMExecuteState) -> None:
        settings = self.soft_delete
        if state.is_delete:
            if any(issubclass(mapper.class_, SoftDeleteMixin) for mapper in state.all_mappers):
                if not state.execution_options.get("hard_delete", False):
                    raise ValueError(
                        "Bulk DELETE of a soft-delete model requires hard_delete=True; "
                        "use Session.delete(instance) for logical deletion",
                    )
            return
        if not state.is_select or state.execution_options.get("include_deleted", False):
            return
        state.statement = self._apply_filters(state.statement, state.all_mappers)

    def _apply_filters(self, statement: Any, mappers: Any) -> Any:
        settings = self.soft_delete
        # Construct a SQL expression per concrete model, avoiding cached closure settings.
        registries = {mapper.registry for mapper in mappers}
        for registry in registries:
            for mapper in registry.mappers:
                model = mapper.class_
                if not issubclass(model, SoftDeleteMixin):
                    continue
                if settings.field not in mapper.column_attrs:
                    raise ValueError(f"Soft-delete model {model.__name__} has no mapped field {settings.field}")
                statement = statement.options(with_loader_criteria(
                    model, getattr(model, settings.field) == settings.active_value,
                    include_aliases=True,
                ))
        return statement

    def filter_select(self, statement: Select[Any]) -> Select[Any]:
        """Apply model criteria before a Select is wrapped in a pagination subquery."""
        if not self.soft_delete.enabled or statement.get_execution_options().get("include_deleted", False):
            return statement
        return self._apply_filters(statement, self._selected_mappers(statement))

    def filter_count(self, count: Select[Any], statement: Select[Any]) -> Select[Any]:
        """Apply model criteria to a pagination COUNT wrapping ``statement`` as a subquery.

        Loader criteria attached to the inner Select are not compiled once it becomes a
        subquery, so the outer COUNT must carry them to match the filtered rows.
        """
        if not self.soft_delete.enabled or statement.get_execution_options().get("include_deleted", False):
            return count
        return self._apply_filters(count, self._selected_mappers(statement))

    @staticmethod
    def _selected_mappers(statement: Select[Any]) -> list[Any]:
        mappers = []
        for description in statement.column_descriptions:
            entity = description.get("entity")
            if entity is not None:
                inspected = inspect(entity)
                mappers.append(inspected.mapper if hasattr(inspected, "mapper") else inspected)
        return mappers

    def _convert_deletions(self, session: Session, flush_context: Any, instances: Any) -> None:
        settings = self.soft_delete
        for instance in tuple(self.deleted):
            if not isinstance(instance, SoftDeleteMixin):
                continue
            if inspect(instance) in self._physical_deletions:
                continue
            if settings.field not in inspect(instance).mapper.column_attrs:
                raise ValueError(f"Soft-delete model has no mapped field {settings.field}")
            self.add(instance)
            setattr(instance, settings.field, settings.deleted_value)

    def _clear_physical_deletions(self, *args: Any) -> None:
        self._physical_deletions.clear()

    def get(self, entity: Any, ident: Any, **kwargs: Any) -> Any:
        instance = super().get(entity, ident, **kwargs)
        if (
            self.soft_delete.enabled
            and isinstance(instance, SoftDeleteMixin)
            and not kwargs.get("execution_options", {}).get("include_deleted", False)
            and getattr(instance, self.soft_delete.field) != self.soft_delete.active_value
        ):
            return None
        return instance

    def hard_delete(self, instance: Any) -> None:
        """Request physical deletion, including ORM delete cascades, without committing."""
        pending = set(self.deleted)
        super().delete(instance)
        self._physical_deletions.update(
            inspect(item) for item in self.deleted if item not in pending or item is instance
        )

    def close(self) -> None:
        try:
            super().close()
        finally:
            self._physical_deletions.clear()


class AsyncSoftDeleteSession(AsyncSession):
    """Use the same session-local logical deletion rules in asynchronous operations."""

    sync_session_class = SoftDeleteSession

    async def hard_delete(self, instance: Any) -> None:
        """Request physical deletion using the native async greenlet bridge."""
        await self.run_sync(lambda session: session.hard_delete(instance))
