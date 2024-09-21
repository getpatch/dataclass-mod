from logging import getLogger

logger = getLogger(__name__)

import dataclasses
import typing


EXC_WITH_NOTES = tuple[Exception | None, str, ...] | tuple[Exception | None, str] | tuple[Exception | None]


def add_exception_notes(exc: Exception | None, *notes: str) -> Exception | None:
    if exc is not None:
        for item in notes:
            exc.add_note(item)
    return exc


@dataclasses.dataclass
class ExceptionCollector:

    exc_list: list[Exception] = dataclasses.field(default_factory=list)

    def add(self, exc: Exception | None, *notes: str) -> typing.Self:
        exc = add_exception_notes(exc, *notes)
        if exc is not None:
            self.exc_list.append(exc)
        return self

    def extend(self, exc_list: typing.Iterable[EXC_WITH_NOTES | Exception]) -> typing.Self:
        for item in exc_list:
            if not isinstance(item, tuple):
                item = (item, )
            self.add(item[0], *item[1:])
        return self

    def group_exception(self, msg: str) -> Exception | None:
        """
        Return group exception with provided message if there at least one exception was collected.
        :param msg: exception message
        """
        return ExceptionGroup(msg, self.exc_list) if self.exc_list else None

    def single_or_group_exception(self, msg: str) -> Exception | None:
        """
        Return exception if only one was collected (skip message),
        group exception with provided message if more than one exception were collected.
        :param msg: exception message
        """
        if len(self.exc_list) == 1:
            return self.exc_list[0]
        return self.group_exception(msg) if self.exc_list else None
