import contextlib
import dataclasses
import typing
import logging

logger = logging.getLogger(__name__)

EXC_WITH_NOTES = tuple[Exception | None, str, ...] | tuple[Exception | None, str] | tuple[Exception | None]


_clean_traceback = False

def set_deep_exception_traceback(is_enabled: bool) -> bool:
    """
    Enable or disable deep traceback for exception inside library
    :return: current value
    """
    global _clean_traceback
    result = _clean_traceback
    _clean_traceback = is_enabled
    return result


def add_exception_notes(exc: Exception | None, *notes: str) -> Exception | None:
    if exc is not None:
        for item in notes:
            exc.add_note(item)
    return exc


@dataclasses.dataclass
class ExceptionCollector:

    exc_list: list[Exception] = dataclasses.field(default_factory=list)

    @contextlib.contextmanager
    def __call__(self, *notes: str) -> Exception | None:
        try:
            yield
        except (ValueError, TypeError) as exc:
            self.add(exc, *notes)
        except ExceptionGroup as exc:
            if not exc.message and not getattr(exc, "__notes__", None):
                self.extend((i, *notes) for i in exc.exceptions)
            else:
                self.add(exc, *notes)

    def add(self, exc: Exception | None, *notes: str) -> typing.Self:
        exc = add_exception_notes(exc, *notes)
        if exc is not None:
            if _clean_traceback:
                exc = exc.with_traceback(None)
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


