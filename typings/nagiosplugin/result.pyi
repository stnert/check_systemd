from dataclasses import dataclass
from typing import List

from nagiosplugin.context import Context
from nagiosplugin.metric import Metric
from nagiosplugin.resource import Resource
from nagiosplugin.state import ServiceState

@dataclass
class Result:

    state: ServiceState
    hint: str | None = None
    metric: Metric | None = None

    @property
    def resource(self) -> Resource | None: ...
    @property
    def context(self) -> Context | None:
        """Reference to the metric used to generate this result."""
        ...

class ScalarResult(Result):
    """Special-case result for evaluation in a ScalarContext.

    DEPRECATED: use Result instead.
    """

    def __new__(cls, state, hint, metric): ...

class Results:
    """Container for result sets.

    Basically, this class manages a set of results and provides
    convenient access methods by index, name, or result state. It is
    meant to make queries in :class:`~.summary.Summary`
    implementations compact and readable.

    The constructor accepts an arbitrary number of result objects and
    adds them to the container.
    """

    def __init__(self, *results) -> None: ...
    def add(self, *results):  # -> Self@Results:
        """Adds more results to the container.

        Besides passing :class:`Result` objects in the constructor,
        additional results may be added after creating the container.

        :raises ValueError: if `result` is not a :class:`Result` object
        """
        ...
    def __iter__(self):  # -> Generator[Unknown, None, None]:
        """Iterates over all results.

        The iterator is sorted in order of decreasing state
        significance (unknown > critical > warning > ok).

        :returns: result object iterator
        """
        ...
    def __len__(self):  # -> int:
        """Number of results in this container."""
        ...
    def __getitem__(self, item):
        """Access result by index or name.

        If *item* is an integer, the itemth element in the
        container is returned. If *item* is a string, it is used to
        look up a result with the given name.

        :returns: :class:`Result` object
        :raises KeyError: if no matching result is found
        """
        ...
    def __contains__(self, name):  # -> bool:
        """Tests if a result with given name is present.

        :returns: boolean
        """
        ...
    @property
    def most_significant_state(self) -> ServiceState: ...
    @property
    def most_significant(self) -> List[Result]: ...
    @property
    def first_significant(self) -> Result: ...
