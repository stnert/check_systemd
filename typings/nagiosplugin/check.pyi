_log = ...

class Check:
    def __init__(self, *objects) -> None:
        """Creates and configures a check.

        Specialized *objects* representing resources, contexts,
        summary, or results are passed to the the :meth:`add` method.
        Alternatively, objects can be added later manually.
        """
        ...
    def add(self, *objects):  # -> Self@Check:
        """Adds domain objects to a check.

        :param objects: one or more objects that are descendants from
            :class:`~nagiosplugin.resource.Resource`,
            :class:`~nagiosplugin.context.Context`,
            :class:`~nagiosplugin.summary.Summary`, or
            :class:`~nagiosplugin.result.Results`.
        """
        ...
    def __call__(self):  # -> None:
        """Actually run the check.

        After a check has been called, the :attr:`results` and
        :attr:`perfdata` attributes are populated with the outcomes. In
        most cases, you should not use __call__ directly but invoke
        :meth:`main`, which delegates check execution to the
        :class:`Runtime` environment.
        """
        ...
    def main(self, verbose: bool = ..., timeout: int = ...) -> None: ...
    @property
    def state(self):  # -> Type[Unknown]:
        """Overall check state.

        The most significant (=worst) state seen in :attr:`results` to
        far. :obj:`~nagiosplugin.state.Unknown` if no results have been
        collected yet. Corresponds with :attr:`exitcode`. Read-only
        property.
        """
        ...
    @property
    def summary_str(self):  # -> str:
        """Status line summary string.

        The first line of output that summarizes that situation as
        perceived by the check. The string is usually queried from a
        :class:`Summary` object. Read-only property.
        """
        ...
    @property
    def verbose_str(self):  # -> list[Unknown] | Literal['']:
        """Additional lines of output.

        Long text output if check runs in verbose mode. Also queried
        from :class:`~nagiosplugin.summary.Summary`. Read-only property.
        """
        ...
    @property
    def exitcode(self):  # -> int:
        """Overall check exit code according to the Nagios API.

        Corresponds with :attr:`state`. Read-only property.
        """
        ...
