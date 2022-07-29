from typing import Generator

from nagiosplugin.metric import Metric

class Resource:

    name: str

    def probe(self) -> list[Metric] | Metric | Generator[Metric, None, None]: ...
