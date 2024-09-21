import dataclasses

import pytest

from dataclasses_mod import validators as v
from dataclasses_mod.validators import ValidatorMixin
from .common import Base, serialize_exception


@dataclasses.dataclass
class SimpleTypes(ValidatorMixin):
    a: int
    b: str


class TestSimpleTypeValidation(Base):

    def test_valid(self):
        SimpleTypes(1, "a").full_validate()

    @pytest.mark.parametrize("args", (
        (1, 1),
        (1, None),
        ("a", "a"),
        (None, "a"),
    ))
    def test_simple_types_fail(self, args):
        with pytest.raises(TypeError) as exc_info:
            SimpleTypes(*args).full_validate()
        self.data_regression.check(serialize_exception(exc_info.value))


@dataclasses.dataclass
class UnionTypes(ValidatorMixin):
    a: int | str | bool
    b: str | None


class TestUnionTypeValidation(Base):

    @pytest.mark.parametrize("args", (
            (1, "a"),
            ("a", "a"),
            (1, None),
            ("a", None),
            (True, None),
    ))
    def test_valid(self, args):
        UnionTypes(*args).full_validate()

    @pytest.mark.parametrize("args", (
            (None, 1),
            (None, None),
            (1, 1),
    ))
    def test_union_types_fail(self, args: tuple):
        with pytest.raises(ExceptionGroup) as exc_info:
            UnionTypes(*args).full_validate()
        self.data_regression.check(serialize_exception(exc_info.value))


@dataclasses.dataclass
class GenericTypes(ValidatorMixin):
    a: list[int]
    b: set[int | str | None]
    c: tuple[int]
    d: tuple[str, str | int]
    e: tuple[bool, ...] | None


class TestGenericTypeValidation(Base):

    @pytest.mark.parametrize("args", (
            ([1], {1, "a", None}, (1, ), ("a", "b"), (True, True, True, False)),
            ([1], {1, "a", None}, (1,), ("a", "b"), (True,)),
            ([1], {1, "a", None}, (1,), ("a", "b"), ()),
            ([1], {1, "a", None}, (1,), ("a", "b"), None),

            ([1, 2, 3], {1, "a", None}, (1,), ("a", "b"), None),
            ([], {1, "a", None}, (1,), ("a", "b"), None),
            ([1], set(), (1,), ("a", "b"), None),
            ([1], {1, "a", None}, (1,), ("a", 12), None),
    ))
    def test_valid(self, args):
        GenericTypes(*args).full_validate()

    @pytest.mark.parametrize("args", (
            (["a"], {1, "a", None}, (1,), ("a", "b"), (True, )),
            ([1], {b"b"}, (1,), ("a", "b"), (True,)),
            ([1], {1, "a", None}, ("a",), ("a", "b"), (True,)),
            ([1], {1, "a", None}, (1, 2), ("a", "b"), (True,)),
            ([1], {1, "a", None}, (1,), (1, "b"), (True,)),
            ([1], {1, "a", None}, (1,), ("a", "b"), ("a",)),

            ([], set(), (1,), ("a", 1), []),
            ("a", set(), (1,), ("a", 1), ()),
            ([], {}, (1,), ("a", 1), ()),
            ([], set(), None, ("a", 1), ()),
            ([], set(), (1,), b"", ()),
    ))
    def test_generic_types_fail(self, args):
        with pytest.raises(Exception) as exc_info:
            GenericTypes(*args).full_validate()
        self.data_regression.check(serialize_exception(exc_info.value))


@dataclasses.dataclass
class Constrains(ValidatorMixin):
    a: list[int] = dataclasses.field() >> v.min_length(1)
    b: str = v.max_length(2)
    c: int = 10 >> v.min(10) >> v.max(20)
    d: str | None = "" >> v.re("a.?a(c)?") >> v.eq(b)


class TestConstrainsValidation(Base):

    @pytest.mark.parametrize("args", (
            ([1], "aa", 15, "aa"),
    ))
    def test_valid(self, args):
        Constrains(*args).full_validate()

    @pytest.mark.parametrize("args", (
            ([], "aa", 15, "aa"),
            ([1], "aac", 15, "aac"),
            ([1], "aa", 5, "aa"),
            ([1], "aa", 25, "aa"),
            ([1], "ab", 15, "ab"),
            ([1], "ab", 15, "aa"),
    ))
    def test_constrains_fail(self, args):
        with pytest.raises(Exception) as exc_info:
            Constrains(*args).full_validate()
        self.data_regression.check(serialize_exception(exc_info.value))
