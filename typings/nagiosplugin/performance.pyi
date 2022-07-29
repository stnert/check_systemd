from dataclasses import dataclass
from typing import Any, Literal

def zap_none(val: Any | None) -> Any | Literal[""]: ...
def quote(label: str) -> str: ...
@dataclass
class Performance:

    label: str
    value: Any
    uom: str | None = None
    warn: float | None = None
    crit: float | None = None
    min: float | None = None
    max: float | None = None

    def __str__(self) -> str: ...
