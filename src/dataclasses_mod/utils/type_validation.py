import logging
import types
import typing

from .exceptions import ExceptionCollector, add_exception_notes
from .repr import value_repr, type_str

logger = logging.getLogger(__name__)


def _validate_list(value, args: tuple) -> Exception | None:
    if not isinstance(value, list):
        return TypeError(f"expect list, got {type(value).__name__ if value is not None else None}")
    assert len(args) == 1, "Expect only one element in list specification"
    collector = ExceptionCollector()
    collector.extend((validate_type(item, args[0]), f"index {idx}") for idx, item in enumerate(value))
    return collector.group_exception(f"expect list of {type_str(args[0])}")


def _validate_set(value, args) -> Exception | None:
    if not isinstance(value, set):
        return TypeError(f"expect set, got {type(value).__name__ if value is not None else None}")
    assert len(args) == 1, "Expect only one element in set specification"
    return ExceptionCollector().extend((validate_type(item, args[0]), ) for item in value) \
        .group_exception(f"expect {type_str(args[0])}")


def _validate_tuple(value, args) -> Exception | None:
    if not isinstance(value, tuple):
        return TypeError(f"expect tuple, got {type(value).__name__ if value is not None else None}")
    if args == ():
        if len(value) > 0:
            return ValueError(f"expect empty tuple, got {len(value)} elements")
        return None
    if args[-1] == Ellipsis:
        assert len(args) == 2, "Expect one type in tuple specification with ellipsis"
        return ExceptionCollector().extend(
            (validate_type(item, args[0]),  f"index {idx}") for idx, item in enumerate(value)
        ).group_exception(f"expect tuple of {type_str(args[0])}")
    if len(args) != len(value):
        return ValueError(f"expect {len(args)} elements in tuple, got {len(value)} elements")
    return ExceptionCollector().extend(
        (validate_type(item, args[idx]), f"index {idx}") for idx, item in enumerate(value)
    ).group_exception(f"expect tuple[{', '.join(type_str(i) for i in args)}]")


def validate_type(value, type_descr, _with_notes: bool = True) -> Exception | None:
    logger.debug("Validate type %s", type_descr)
    notes = (f"value {value_repr(value)}", ) if _with_notes else ()
    if type_descr is None:
        if value is not None:
            return add_exception_notes(TypeError(f"expect None"), *notes)
        return None

    if type_descr is Ellipsis or type_descr is typing.Any:
        return None

    origin = typing.get_origin(type_descr)
    if origin is types.UnionType:
        args = typing.get_args(type_descr)
        assert args, "expect at least one argument for union"
        exc_list = [validate_type(value, i, _with_notes=False) for i in args]
        if any(i is None for i in exc_list):
            return None
        return add_exception_notes(ExceptionGroup(f"expect {type_descr}", exc_list), *notes)
    if origin is not None:
        if origin is list:
            return _validate_list(value, typing.get_args(type_descr))
        if origin is set:
            return _validate_set(value, typing.get_args(type_descr))
        if origin is tuple:
            return _validate_tuple(value, typing.get_args(type_descr))
        raise AssertionError(f"generic {type_str(type_descr)} not supported")
    assert isinstance(type_descr, type), f"Unexpected type {type_descr}"
    if not isinstance(value, type_descr):
        return add_exception_notes(
            TypeError(f"expect {type_descr.__name__}, got {type(value).__name__ if value is not None else None}"),
            *notes,
        )
    return None
