import enum
import logging
import typing

from dataclasses_mod.utils.attrs import get_deep_attr
from dataclasses_mod.utils.repr import value_repr, log_value_repr

logger = logging.getLogger(__name__)

T = typing.TypeVar('T')

E_0 = typing.TypeVar('E_0')
E_1 = typing.TypeVar('E_1')
E_2 = typing.TypeVar('E_2')

T_0 = typing.TypeVar('T_0')
T_1 = typing.TypeVar('T_1')
T_2 = typing.TypeVar('T_2')

S_ELEMENT_0 = dict[str, str | tuple[str, ...] | E_0 | dict[str, ...]]
S_ELEMENT_1 = dict[str, str | tuple[str, ...] | E_1]
S_ELEMENT_2 = dict[str, str | tuple[str, ...] | E_2]
S_ELEMENT = S_ELEMENT_0[S_ELEMENT_1[S_ELEMENT_2[str]]]

S_TUPLE = tuple[T_0, ...] | T_0

SCHEMA = S_TUPLE[S_ELEMENT]

S_S_ELEMENT_0 = str | tuple[str, ...] | list[str] | dict[str, ...]
S_S_ELEMENT_1 = str | tuple[str, ...] | list[str] | E_1
S_S_ELEMENT_2 = str | tuple[str, ...] | list[str] | E_1

S_S_ELEMENT = S_S_ELEMENT_2[S_S_ELEMENT_1[S_S_ELEMENT_0]]

S_SCHEMA = S_TUPLE[S_S_ELEMENT]


def _j_keys(a: str, b: str) -> str:
    if not a:
        return b
    if not b:
        return a
    if a.endswith("."):
        return a + b
    return a + "." + b


def _element_schema_compile(field_schema: SCHEMA) -> list[tuple[str, str]]:
    result = []
    for key, value in field_schema.items():
        if isinstance(value, str):
            result.append((key, value))
        elif isinstance(value, dict):
            for sub_key, cmp_key in _element_schema_compile(value):
                result.append((_j_keys(key, sub_key), cmp_key))
        elif isinstance(value, tuple):
            assert all(isinstance(v, str) for v in value), "Expect a tuple of string"
            result += [(key, v) for v in value]
        else:
            typing.assert_never(type(value))
    return result


def _schema_compile(schema: SCHEMA) -> list[tuple[str, str]]:
    if not isinstance(schema, tuple):
        schema = (schema,)
    result = typing.cast(list[tuple[str, str]], [])
    for item in schema:
        result += _element_schema_compile(item)
    return result


def _element_s_schema_compile(field_schema: str | dict) -> list[str]:
    if isinstance(field_schema, str):
        return [field_schema]

    if isinstance(field_schema, dict):
        result = []
        for key, val in field_schema.items():
            result += [_j_keys(key, i) for i in _element_s_schema_compile(val)]
        return result

    assert isinstance(field_schema, (list, tuple)), "Unexpected type of fields"
    assert all(isinstance(i, str) for i in field_schema), ""
    return [str(i) for i in field_schema]


def _s_schema_compile(schema: S_SCHEMA) -> list[str]:
    if isinstance(schema, str):
        return [schema]
    if isinstance(schema, (tuple, list)) and all(isinstance(i, str) for i in schema):
        return list(schema)
    if isinstance(schema, dict):
        result = []
        for key, value in schema.items():
            result.extend(_j_keys(key, i) for i in _element_s_schema_compile(value))
        return result
    assert isinstance(schema, (list, tuple)), "Invalid schema type"
    return sum((_s_schema_compile(i) for i in schema), [])



class CheckFieldsMixin:

    def check_same_fields(self, other: typing.Any, fields: S_SCHEMA):
        """
        Compare provided fields of self object against attributes of other object.

        :param other: object to compare
        :param fields: field schema
        :return: None
        :raise ValueError: when field schema is not satisfied with other
        """
        logger.info("Check same fields against %s", log_value_repr(other, logging.INFO, logger))
        compiled_schema = _s_schema_compile(fields)

        diff = {}
        for item in compiled_schema:
            logger.debug("Compare %s", item)
            self_value = get_deep_attr(self, item)
            other_value = get_deep_attr(other, item)
            if self_value != other_value:
                logger.debug("Found different at %s", item)
                diff[item] = (self_value, other_value)

        logger.debug("Found %s diffs", len(diff))
        if not diff:
            return
        k_length = max(len(i) for i in diff)
        lines = []
        for k, (s_value, o_value) in sorted(diff.items(), key=lambda v: v[0]):
            lines.append(f"      {k.rjust(k_length)}: {value_repr(s_value)} -> {value_repr(o_value)}")
        table = "\n".join(lines)
        raise ValueError(f"Found unexpected difference {self} -> {other}:\n{table}")

    def check_another_fields(self, other: typing.Any, field_schema: SCHEMA):
        """
        Compare fields of self object against attributes of other object using provided schema.

        :param other: object to compare
        :param field_schema: field schema
        :return: None
        :raise ValueError: when field schema is not satisfied with other
        """
        logger.info("Check another fields against %s", log_value_repr(other, logging.INFO, logger))
        diff = []

        compiled_schema = _schema_compile(field_schema)
        for self_attr, other_attr in compiled_schema:
            logger.debug("Compare %s to %s", self_attr, other_attr)
            self_value = get_deep_attr(self, self_attr)
            self_cmp_value = self_value.value if isinstance(self_value, enum.Enum) else self_value
            other_value = get_deep_attr(other, other_attr)
            other_cmp_value = other_value.value if isinstance(other_value, enum.Enum) else other_value
            if self_cmp_value != other_cmp_value:
                logger.debug("Found diff of %s to %s", self_attr, other_attr)
                diff.append((self_attr, other_attr, self_value, other_value))
        logger.debug("Found %s diffs", len(diff))
        if not diff:
            return

        k_length = max(max(len(i[0]) + len(i[1]) + 4 for i in diff), 5)
        lines = []
        for key, o_key, s_value, o_value in sorted(diff, key=lambda v: (v[0], v[1])):
            k = f"{key} -> {o_key}"
            lines.append(f"    {k.rjust(k_length)}: {value_repr(s_value)} -> {value_repr(o_value)}")
        table = "\n".join(lines)
        raise ValueError(f"Found unexpected difference {self} -> {other}:\n{table}")