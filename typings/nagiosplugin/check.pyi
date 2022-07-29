from typing import Literal

from nagiosplugin.context import Context, Contexts
from nagiosplugin.resource import Resource
from nagiosplugin.result import Results
from nagiosplugin.state import ServiceState
from nagiosplugin.summary import Summary

class Check:
    resources: list[Resource]
    contexts: Contexts
    summary: Summary
    results: Results
    perfdata: list[str]
    name: str

    def __init__(self, *objects: Resource | Context | Summary | Results) -> None: ...
    def add(self, *objects: Resource | Context | Summary | Results) -> Check: ...
    def __call__(self) -> None: ...
    def main(self, verbose: bool = ..., timeout: int = ...) -> None: ...
    @property
    def state(self) -> ServiceState: ...
    @property
    def summary_str(self) -> str: ...
    @property
    def verbose_str(self) -> list[str] | str: ...
    @property
    def exitcode(self) -> Literal[0, 1, 2, 3]: ...
