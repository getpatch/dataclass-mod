import typing
from logging import getLogger

from .repr import value_repr

logger = getLogger(__name__)
logger.disabled = True


def get_deep_attr(value, path: str):
    if path == "." or not path:
        return value
    prefix = []
    for attr in (path.split(".") if "." in path else [path]):
        assert attr, f"Empty element in path {path}"
        prefix.append(attr)
        if isinstance(value, typing.Mapping):
            value = value[attr]
            continue
        if isinstance(value, typing.Sequence):
            try:
                attr = int(attr)
            except ValueError:
                raise AssertionError(f"Expect int as index, got {value!r} in path {path}")
            try:
                value = value[attr]
            except IndexError:
                raise AssertionError(f"Out of index of path {'.'.join(prefix)}")
            continue
        if not hasattr(value, attr):
            raise AssertionError(f"Expect attribute {attr} of path {path} but not found in {value_repr(value)}")
        value = getattr(value, attr)
    return value
