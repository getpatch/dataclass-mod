import abc
import dataclasses
import logging
import re as re_module
import typing

from .utils.attrs import get_deep_attr
from .utils.exceptions import add_exception_notes, ExceptionCollector
from .utils.repr import value_repr, log_value_repr, type_str
from .utils.type_validation import validate_type

logger = logging.getLogger(__name__)


VALIDATORS_ATTRS = "_data_class_proc_validators"



class Validator(abc.ABC):

    def update_validator_list(self, validator_list: list["Validator"]) -> list["Validator"]:
        return validator_list + [self]

    @abc.abstractmethod
    def check_value(self, value, instance) -> Exception | None:
        ...


@dataclasses.dataclass
class SimpleValidator(Validator):
    __slots__ = ("operator", "message", "skip_none")
    operator: typing.Callable[[...], bool]
    message: str
    skip_none: bool

    def __str__(self):
        return f"validate {self.message}"

    def __repr__(self):
        return f"<validator:{self.message}>"

    def check_value(self, value, instance):
        if value is None and self.skip_none:
            return None
        if self.operator(value):
            return None
        return add_exception_notes(ValueError(f"Expect {self.message}"), f"value {value_repr(value)}")


@dataclasses.dataclass
class DependValidator(Validator):
    __slots__ = ("path", "operator", "message", "skip_none")
    path: str | dataclasses.Field
    operator: typing.Callable[[..., ...], bool]
    message: str
    skip_none: bool

    def __str__(self):
        return f"validate {self.message} with {self.path}"

    def __repr__(self):
        return f"<validator:{self.message}:{self.path}>"

    def check_value(self, value, instance):
        if value is None and self.skip_none:
            return None

        path = self.path.name if isinstance(self.path, dataclasses.Field) else self.path
        check_value = get_deep_attr(instance, path)
        if self.operator(value, check_value):
            return None
        return add_exception_notes(
            ValueError(f"Expect {self.message} with field {path}"),
            f"value {value_repr(value)}", f"expected value {value_repr(check_value)}"
        )


class FieldWithValidator(dataclasses.Field):
    __slots__ = ("validator", )

    validator: Validator

    def __init__(self, validator: Validator):
        metadata = {VALIDATORS_ATTRS: [validator]}
        # noinspection PyTypeChecker
        super().__init__(
            default=dataclasses.MISSING, default_factory=dataclasses.MISSING,
            init=True, repr=True, hash=None, compare=True, metadata=metadata, kw_only=dataclasses.MISSING
        )
        self.validator = validator

    def __rrshift__(self, other) -> dataclasses.Field:

        if not isinstance(other, dataclasses.Field):
            # we try to append validator to value that is default value of field
            assert self.default is dataclasses.MISSING, "Validator is used as a field with a default value"
            self.default = other
            return self

        assert not isinstance(other, FieldWithValidator), "Standard rshift must be applied"
        assert self.metadata == {VALIDATORS_ATTRS: [self.validator]}, "Validator metadata was affected"
        metadata = {
            **other.metadata,
            VALIDATORS_ATTRS: self.validator.update_validator_list(other.metadata.get(VALIDATORS_ATTRS, []))
        }

        return dataclasses.Field(
            default=other.default, default_factory=other.default_factory,
            init=other.init, repr=other.repr, hash=other.repr, compare=other.compare,
            metadata=metadata, kw_only=other.kw_only
        )

    def __rshift__(self, other: dataclasses.Field) -> dataclasses.Field:
        if not isinstance(other, FieldWithValidator):
            raise NotImplemented

        other = typing.cast(FieldWithValidator, other)
        assert self.metadata == {VALIDATORS_ATTRS: [self.validator]}, "Validator metadata was affected"
        assert other.metadata == {VALIDATORS_ATTRS: [other.validator]}, "Validator metadata was affected"

        metadata = {
            VALIDATORS_ATTRS: self.validator.update_validator_list([other.validator])
        }

        return dataclasses.Field(
            default=other.default, default_factory=other.default_factory,
            init=other.init, repr=other.repr, hash=other.repr, compare=other.compare,
            metadata=metadata, kw_only=other.kw_only
        )


class ValidatorMixin:
    """
    Mixin that allows to run validation on dataclasses
    """

    @classmethod
    def dump_validators(cls):
        result = []
        for field in dataclasses.fields(cls):  # noqa
            validator_list = field.metadata.get(VALIDATORS_ATTRS, [])
            if not validator_list:
                continue
            v_repr = [f"validate type {type_str(field.type)}"] + [str(i) for i in validator_list]
            result.append(f"\t{field.name}: " + ", ".join(v_repr))
        return f"validators for {type_str(cls)}:\n" + "\n".join(result)


    def validate(self):
        """
        Allow to run custom validation on dataclasses.
        """
        pass

    @typing.final
    def full_validate(self):
        """Run full validation of dataclasses"""

        logger.info("Validate %s", log_value_repr(self, logging.INFO, logger))
        assert dataclasses.is_dataclass(self), f"{value_repr(self)} if not a dataclass"

        exc_collector = ExceptionCollector()

        for item in dataclasses.fields(self):   # noqa
            exc_collector.add(add_exception_notes(self._validate_field(item)), f"field {item.name}")

        with exc_collector():
            logger.debug("Run custom validator of %s", log_value_repr(self, logging.DEBUG, logger))
            self.validate()

        logger.debug("Validation of %s finished with %s exceptions",
                     log_value_repr(self, logging.INFO, logger), len(exc_collector.exc_list))

        exc = exc_collector.single_or_group_exception("Validation errors")
        if exc is not None:
            raise exc

    @typing.final
    def _validate_field(self, field: dataclasses.Field) -> Exception | None:
        field_value = getattr(self, field.name)
        logger.debug("Validate field %s", field.name)

        validator_metadata = typing.cast(list[Validator], field.metadata.get(VALIDATORS_ATTRS, []))

        exc_collector = ExceptionCollector()

        logger.debug("Check type of field %s", field.name)
        exc_collector.add(validate_type(field_value, field.type))

        if exc_collector.exc_list:
            logger.debug("Type validation failed, return error")
            return exc_collector.single_or_group_exception("Field type errors")

        logger.debug("Run field validators for %s", field.name)
        for validator in validator_metadata:
            logger.debug("Validate %s with %s", field.name, validator)
            exc_collector.add(validator.check_value(field_value, self))

        if isinstance(field_value, ValidatorMixin):
            logger.debug("Field %s has a value that has validator", field.name)
            with exc_collector():
                field_value.full_validate()

        if isinstance(field_value, typing.Mapping):
            logger.debug("Field %s has a dict", field.name)
            for key, item in field_value.items():
                if not isinstance(item, ValidatorMixin):
                    continue
                with exc_collector(f"key {key}"):
                    logger.debug("Value of key %s of field %s has a validator", key, field.name)
                    item.full_validate()
        elif isinstance(field_value, typing.Collection):
            for idx, item in enumerate(field_value):
                if not isinstance(item, ValidatorMixin):
                    continue
                with exc_collector(f"index {idx}"):
                    logger.debug("Value with index %s of field %s has a validator", idx, field.name)
                    item.full_validate()

        logger.debug("Validation of %s finished with %s exceptions", field.name, len(exc_collector.exc_list))
        return exc_collector.single_or_group_exception("Field validation errors")


def eq(field: dataclasses.Field | str) -> FieldWithValidator:
    """
    Check if field to be equal to another field

    :param field: another field from same data class of path related to current instance
    """
    return FieldWithValidator(DependValidator(field, lambda a, b: a == b, "equal", True))


def min(value) -> FieldWithValidator:  # noqa
    """
    Check if value is not less than minimum
    """
    return FieldWithValidator(SimpleValidator(lambda v: v >= value, f"min value {value}", True))


def max(value) -> FieldWithValidator:  # noqa
    """
    Check if value is not greater than maximum
    """
    return FieldWithValidator(SimpleValidator(lambda v: v <= value, f"max value {value}", True))


def range(min_value, max_value) -> FieldWithValidator:  # noqa
    """
    Check if value in in the range
    """
    return FieldWithValidator(SimpleValidator(lambda v: min_value <= v <= max_value,
                                              f"value in [{min_value}, {max_value}]", True))


def min_length(value) -> FieldWithValidator:
    """
    Check if sequence length is not less than minimum length
    """
    return FieldWithValidator(SimpleValidator(lambda v: len(v) >= value, f"min length {value}", True))


def max_length(value) -> FieldWithValidator:
    """
    Check if sequence length is not greater than maximum length
    """
    return FieldWithValidator(SimpleValidator(lambda v: len(v) <= value, f"max length {value}", True))


def length(value) -> FieldWithValidator:
    """
    Check if sequence length is provided

    Note: use tuple instead of list to check length
    """
    return FieldWithValidator(SimpleValidator(lambda v: len(v) == value, f"length {value}", True))


def re(reg_exp: typing.Pattern | str) -> FieldWithValidator:
    """
    Check if string value is matched to regular expression
    """
    if isinstance(reg_exp, str):
        if not reg_exp.startswith("^"):
            reg_exp = "^" + reg_exp
        if not reg_exp.endswith("$"):
            reg_exp = reg_exp + "$"
        reg_exp = re_module.compile(reg_exp)
    pattern = reg_exp.pattern.lstrip("^").rstrip("$")
    return FieldWithValidator(SimpleValidator(lambda v: reg_exp.match(v) is not None,
                                              f"regular expression `{pattern}`", True))


def values(*expected_values) -> FieldWithValidator:
    """
    Check if value is in the provided list
    """
    return FieldWithValidator(SimpleValidator(lambda v: v in expected_values, f"values {expected_values}", True))
