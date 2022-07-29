from types import TracebackType
from typing import Generator, Optional, Type

from nagiosplugin.cookie import Cookie

class LogTail:
    def __init__(self, path: str, cookie: Cookie) -> None: ...
    def __enter__(self) -> Generator[bytes, None, None]: ...
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...
