from nagiosplugin.metric import Metric
from nagiosplugin.performance import Performance
from nagiosplugin.resource import Resource
from nagiosplugin.result import Result

class Context:
    name: str
    result_cls: Result
    def __init__(self, name: str, fmt_metric=..., result_cls: Result = ...) -> None:
        """Creates generic context identified by `name`.

        Generic contexts just format associated metrics and evaluate
        always to :obj:`~nagiosplugin.state.Ok`. Metric formatting is
        controlled with the :attr:`fmt_metric` attribute. It can either
        be a string or a callable. See the :meth:`describe` method for
        how formatting is done.

        :param name: context name that is matched by the context
            attribute of :class:`~nagiosplugin.metric.Metric`
        :param fmt_metric: string or callable to convert
            context and associated metric to a human readable string
        :param result_cls: use this class (usually a
            :class:`~.result.Result` subclass) to represent the
            evaluation outcome
        """
        ...
    def evaluate(self, metric: Metric, resource: Resource) -> Result: ...
    def performance(self, metric: Metric, resource: Resource) -> Performance: ...
    def describe(self, metric: Metric) -> str | None: ...

class ScalarContext(Context):
    def __init__(
        self, name, warning=..., critical=..., fmt_metric=..., result_cls=...
    ) -> None:
        """Ready-to-use :class:`Context` subclass for scalar values.

        ScalarContext models the common case where a single scalar is to
        be evaluated against a pair of warning and critical thresholds.

        :attr:`name`, :attr:`fmt_metric`, and :attr:`result_cls`,
        are described in the :class:`Context` base class.

        :param warning: Warning threshold as
            :class:`~nagiosplugin.range.Range` object or range string.
        :param critical: Critical threshold as
            :class:`~nagiosplugin.range.Range` object or range string.
        """
        ...
    def evaluate(self, metric, resource):
        """Compares metric with ranges and determines result state.

        The metric's value is compared to the instance's :attr:`warning`
        and :attr:`critical` ranges, yielding an appropropiate state
        depending on how the metric fits in the ranges. Plugin authors
        may override this method in subclasses to provide custom
        evaluation logic.

        :param metric: metric that is to be evaluated
        :param resource: not used
        :returns: :class:`~nagiosplugin.result.Result` object
        """
        ...
    def performance(self, metric, resource):  # -> Performance:
        """Derives performance data.

        The metric's attributes are combined with the local
        :attr:`warning` and :attr:`critical` ranges to get a
        fully populated :class:`~nagiosplugin.performance.Performance`
        object.

        :param metric: metric from which performance data are derived
        :param resource: not used
        :returns: :class:`~nagiosplugin.performance.Performance` object
        """
        ...

class Contexts:
    """Container for collecting all generated contexts."""

    def __init__(self) -> None: ...
    def add(self, context): ...
    def __getitem__(self, context_name): ...
    def __contains__(self, context_name): ...
    def __iter__(self): ...
