import typing

from dataclasses_mod.utils.type_validation import validate_type
from ..common import serialize_exception, Base

DATA = {
    "None": None,
    "int": 12,
    "str": "foo",
    "list_empty": [],
    "list_none": [None, None],
    "list_str": ["", "foo"],
    "list_str_or_none": ["foo", None],
    "list_int": [12, 13, 16],
    "list_none_or_int": [None, 12, ],
    "list_int_or_str": [12, "foo", 16],
    "tuple_empty": (),
    "tuple_none": (None, ),
    "tuple_none_none": (None, None),
    "tuple_int": (1, ),
    "tuple_int_int_int": (1, 12, 13),
    "tuple_str": ("foo", ),
    "tuple_str_str_str": ("foo", "bar", ""),
    "tuple_int_str": (1, "foo"),
    "set_empty": set(),
    "set_int": {1, 2},
    "set_none": {None,},
    "set_str": {"foo", "bar"},
    "set_str_or_none": {"foo", None},
    "set_int_or_str": {"foo", "bar", 1},
    "list_list_int": [[1, 2], [1]],
    "list_list_int_or_str": [[1, 2], ["str"], [1], [1, "str"]],
    "tuple_list_int_set_str_or_int": ([1, 2], {1, "foo"}),
}


def _test(cases: dict, type_desc, data_regression):
    result = {}
    for key, val in cases.items():
        result[key] = serialize_exception(validate_type(val, type_desc))
    data_regression.check(result)


class TestCase(Base):

    def _test(self, type_desc, cases: dict = None):
        cases = cases or DATA
        result = {}
        for key, val in cases.items():
            result[key] = serialize_exception(validate_type(val, type_desc))
        self.data_regression.check(result)

    def test_null(self):
        self._test(None)

    def test_ellipsis(self):
        self._test(...)

    def test_typing_any(self):
        self._test(typing.Any)

    def test_int(self):
        self._test(int)

    def test_str(self):
        self._test(str)

    def test_list(self):
        self._test(list)

    def test_tuple(self):
        self._test(tuple)

    def test_int_or_str(self):
        self._test(int | str)

    def test_list_of_int(self):
        self._test(list[int])

    def test_list_of_str(self):
        self._test(list[str])

    def test_list_of_str_or_int(self):
        self._test(list[str | int])

    def test_list_list(self):
        self._test(list[list])

    def test_list_list_int(self):
        self._test(list[list[int]])

    def test_list_list_int_or_str(self):
        self._test(list[list[int | str]])

    def test_set_of_int(self):
        self._test(set[int])

    def test_set_of_str(self):
        self._test(set[str])

    def test_set_of_str_or_int(self):
        self._test(set[str | int])

    def test_tuple_empty(self):
        self._test(tuple[()])

    def test_tuple_int(self):
        self._test(tuple[int])

    def test_tuple_int_int(self):
        self._test(tuple[int, int])

    def test_tuple_int_int_int(self):
        self._test(tuple[int, int, int])

    def test_tuple_int_ellipsis(self):
        self._test(tuple[int, ...])

    def test_tuple_int_str(self):
        self._test(tuple[int, str])

    def test_tuple_int_or_str(self):
        self._test(tuple[int | str])

    def test_tuple_int_or_str_str(self):
        self._test(tuple[int | str, str])

    def test_tuple_int_or_str_int_int(self):
        self._test(tuple[int | str, int, int])

    def test_tuple_int_or_str_int_or_str(self):
        self._test(tuple[int | str, int | str])

    def test_tuple_list_set(self):
        self._test(tuple[list, set])

    def test_tuple_list_int_set(self):
        self._test(tuple[list[int], set])

    def test_tuple_list_int_set_int(self):
        self._test(tuple[list[int], set[int]])

    def test_tuple_list_int_set_int_or_str(self):
        self._test(tuple[list[int], set[int | str]])
