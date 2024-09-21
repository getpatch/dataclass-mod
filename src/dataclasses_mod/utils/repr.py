import typing
import logging

logger = logging.getLogger(__name__)

_repr_function = repr


def value_repr(value) -> str:
    try:
        return _repr_function(value)
    except Exception as ex:
        logger.exception("Can not repr object: %s", ex)
        return "<can't repr>"


def log_value_repr(value, level, log: logging.Logger) -> str:
    if log.isEnabledFor(level):
        return value_repr(value)
    return "-"


def set_value_repr(repr_function: typing.Callable[[...], str] = None):
    """
    Use provided function to repr values in exception and logs.
    Can be used to sanitise sensitive data.

    :param repr_function: custom repr function
    """
    global _repr_function
    _repr_function = repr_function if repr_function is not None else repr


def type_str(type_descr) -> str:
    """
    Get string representation of given type or type hints.

    :param type_descr: type description as class or type hints
    :return: str
    """
    if type_descr is None or type_descr is type(None):
        return "None"
    if isinstance(type_descr, type):
        return type_descr.__name__
    return str(type_descr)
