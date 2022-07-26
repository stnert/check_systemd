from dataclasses import dataclass
from typing import Dict, Generator, List, Literal

from nagiosplugin.context import Context
from nagiosplugin.metric import Metric
from nagiosplugin.resource import Resource
from nagiosplugin.state import ServiceState

@dataclass
class Result:

    state: ServiceState
    hint: str | None = None
    metric: Metric | None = None
    def __new__(
        cls, state: ServiceState, hint: str | None = ..., metric: Metric | None = ...
    ) -> Result: ...
    def __str__(self) -> str: ...
    @property
    def resource(self) -> Resource | None: ...
    @property
    def context(self) -> Context | None: ...

class ScalarResult(Result):
    def __new__(
        cls, state: ServiceState, hint: str | None = ..., metric: Metric | None = ...
    ) -> ScalarResult: ...

class Results:
    results: List[Result]
    by_state: Dict[Literal[0, 1, 2, 3], Result]
    by_name: Dict[str, Result]

    def __init__(self, *results: Result) -> None: ...
    def add(self, *results: Result) -> Results: ...
    def __iter__(self) -> Generator[Result, None, None]: ...
    def __len__(self) -> int: ...
    def __getitem__(self, item: int | str) -> Result: ...
    def __contains__(self, name: str) -> bool: ...
    @property
    def most_significant_state(self) -> ServiceState: ...
    @property
    def most_significant(self) -> List[Result]: ...
    @property
    def first_significant(self) -> Result: ...
