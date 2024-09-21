import pytest

from dataclasses_mod import set_value_repr


def serialize_exception(exc: Exception | None):
    if exc is None:
        return None

    result = {
        "type": type(exc).__name__,
        "message": str(exc),
        "notes": getattr(exc, "__notes__", None),
    }
    if isinstance(exc, ExceptionGroup):
        res = sorted(list(serialize_exception(i).items()) for i in exc.exceptions)

        result.update({f"sub-exceptions-{idx}": dict(i) for idx, i in enumerate(res)})
    return result


def stable_repr(value):
    """
    Sort key/values in unordered collections like set, dict, etc.
    """
    if isinstance(value, set):
        reprs = sorted(repr(i) for i in value)
        return "{" + ", ".join(reprs) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(stable_repr(i) for i in value) + "]"
    if isinstance(value, tuple):
        if len(value) == 0:
            return "()"
        if len(value) == 1:
            return "(" + stable_repr(value[0]) + ",)"
        return "(" + ", ".join(stable_repr(i) for i in value) + ")"
    return repr(value)


class Base:
    data_regression: ...

    @pytest.fixture(autouse=True)
    def set_up_repr(self, data_regression):
        try:
            self.data_regression = data_regression
            set_value_repr(stable_repr)
            yield
        finally:
            set_value_repr()
