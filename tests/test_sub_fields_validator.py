import pytest

from dataclasses_mod.sub_fields_validator import CheckFieldsMixin


class Base(CheckFieldsMixin):
    class Sub:
        a = 1
        b = 2
        c = 3

        def __repr__(self):
            return type(self).__qualname__

    a = 10
    b = 11

    s = Sub()

    def __repr__(self):
        return type(self).__qualname__


class Cmp:
    class Sub:
        a = 1
        b = 3
        c = 4

        def __repr__(self):
            return type(self).__qualname__

    a = 10
    b = 12

    s = Sub()

    def __repr__(self):
        return type(self).__qualname__


base = Base()
cmp = Cmp()

def test_check_same_fields_success():
    base.check_same_fields(cmp, "a")
    base.check_same_fields(cmp, "s.a")
    base.check_same_fields(cmp, ("a", "s.a"))
    base.check_same_fields(cmp, ["s.a", "a"])
    base.check_same_fields(cmp, (
        ("a", ),
        {"s": "a"},
    ))
    base.check_same_fields(cmp, (
        "a",
        {"s": ["a", ]},
    ))

@pytest.mark.parametrize("schema", (
    "b",
    "s.b",
    "s.c",
    ("b", "s.c"),
    ("b", "s.b", {"s": "c"}),
    ("b", {"s": ["c", "b"]})
))
def test_check_same_fields_fail(schema, file_regression):
    with pytest.raises(ValueError) as exc_info:
        base.check_same_fields(cmp, schema)
    file_regression.check(str(exc_info.value))



def test_check_another_fields_success():
    base.check_another_fields(cmp, {
        "a": "a",
        "s.a" : "s.a",
    })
    base.check_another_fields(cmp, ({"a": "a"}, {"s.a": "s.a"}))
    base.check_another_fields(cmp, {"": {
        "a": "a",
        "s.a": "s.a",
    }})
    base.check_another_fields(cmp, ({"a": {"": "a"}, "s": {"a": "s.a"}}))


@pytest.mark.parametrize("schema", (
    {"b": "b"},
    {"a": "b"},
    {"s.b": "s.b"},
    {"s.a": "s.b"},
    {"a": "a", "s.b": "s.b"},
    {"a": ("a", "b"), "s": {"a": "a", "c": "s.c"}},
))
def test_check_another_fields_fail(schema, file_regression):
    with pytest.raises(ValueError) as exc_info:
        base.check_another_fields(cmp, schema)
    file_regression.check(str(exc_info.value))