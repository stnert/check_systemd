from dataclasses import dataclass
from typing import Any

from nagiosplugin.context import Context
from nagiosplugin.performance import Performance
from nagiosplugin.resource import Resource
from nagiosplugin.result import Result

@dataclass
class Metric:

    name: str | None
    value: Any | None
    uom: str | None = None
    min: float | None = None
    max: float | None = None
    context: str | None = None
    contextobj: Context | None = None
    resource: Resource | None = None

    def replace(self, **attr):  # -> Self@Metric:
        """Creates new instance with updated attributes."""
        ...
    @property
    def description(self) -> str: ...
    @property
    def valueunit(self) -> str: ...
    def evaluate(self) -> Result: ...
    def performance(self) -> Performance: ...
