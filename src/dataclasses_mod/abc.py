"""
Extension of abc that allows to define abstract properties that can be override by field in dataclasses.
"""
import dataclasses
import inspect
import typing
from abc import ABC as _ABC, ABCMeta, abstractmethod, update_abstractmethods, abstractproperty, \
    abstractclassmethod, abstractstaticmethod

__all__ = (
    "ABC", "ABCMeta", "abstractmethod", "abstractfield", "update_abstractmethods",
    "abstractproperty", "abstractclassmethod", "abstractstaticmethod",

)


class AbsField(dataclasses.Field):
    """Abstract field that must be override in subclasses.."""

    def __str__(self):
        return "Abs" + super().__str__()

    def __repr__(self):
        return "Abs" + super().__repr__()


class MissingField(dataclasses.Field):
    """
    Workaround to define field instead of abstract method.
    """
    related_cls: type

    def __str__(self):
        return "Missing" + super().__str__()

    def __repr__(self):
        return "Missing" + super().__repr__()

    def __get__(self, instance: object, owner: type):
        if instance is None:
            return self
        AttributeError(f"'{type(instance).__qualname__}' object has no attribute '{self.name}'")

    @property
    def __isabstractmethod__(self):
        return self.type is None

    @property
    def default(self):
        if self.name is not None and isinstance(self.related_cls.__dict__[self.name], _Descriptor):
            return dataclasses.MISSING
        return _Descriptor(self.name)

    @default.setter
    def default(self, value):
        ...



def abstractfield():
    """
    An indicating abstract field.

    Usage:

        from dataclasses import dataclass
        from dataclasses_mod import abc

        @dataclass
        class A(abc.ABC):
            a: int = abc.abstractfield()

        @dataclass
        class D:
            a: int

    :return:
    """
    return AbsField(
        default=_Descriptor(""), #abstractmethod(lambda _: ...),
        default_factory=dataclasses.MISSING,
        init=False,
        repr=False,
        hash=None,
        compare=False,
        metadata=None,
        kw_only=dataclasses.MISSING
    )


@dataclasses.dataclass(slots=True)
class _Descriptor:
    """
    Reject access to field until it is assigned to attribute
    """
    attr_name: str

    def __get__(self, instance: object, owner: type):
        if instance is None:
            raise AttributeError(f"type object '{owner.__qualname__}' has no attribute '{self.attr_name}'")
        AttributeError(f"'{type(instance).__qualname__}' object has no attribute '{self.attr_name}'")

    def __set_name__(self, owner, name):
        self.attr_name = name

    def __hash__(self):
        return 0



class ABC(_ABC):
    """
    Helper class that provides a way to create an ABC with dataclasses support using
    inheritance.
    """

    def __new__(cls, *args, **kwargs):
        if dataclasses.is_dataclass(cls):
            abstract_fields = [
                i.name for i in dataclasses.fields(cls)
                if isinstance(i, AbsField) and (
                        i.name not in cls.__dict__ or isinstance(cls.__dict__[i.name], (AbsField, _Descriptor))
                )
            ]
            if len(abstract_fields) == 1:
                raise TypeError(f"Can't instantiate abstract class {cls.__qualname__} "
                                f"with abstract field {abstract_fields[0]}")
            if len(abstract_fields) > 1:
                fields = ", ".join(repr(i) for i in abstract_fields)
                raise TypeError(f"Can't instantiate abstract class {cls.__qualname__} "
                                f"with abstract fields {fields}")
        return super().__new__(cls)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        abstracts = set()
        # Check the existing abstract methods of the parents, keep only the ones
        # that are not implemented.
        for scls in cls.__bases__:
            for name in getattr(scls, '__abstractmethods__', ()):
                value = getattr(cls, name, None)
                value = getattr(scls, name, None)
                if getattr(value, "__isabstractmethod__", False):
                    abstracts.add(name)

        if not abstracts:
            return
        annotation = {k: v for k, v in inspect.get_annotations(cls).items() if k in abstracts}
        for field, a_type in annotation.items():
            # update class attribute using annotation
            if (dataclasses._is_classvar(a_type, typing) or (
                isinstance(a_type, str)
                and dataclasses._is_type(a_type, cls, typing, typing.ClassVar,dataclasses._is_classvar)
            )):
                continue

            if field not in cls.__dict__:
                f = MissingField(
                    default=dataclasses.MISSING,
                    default_factory=dataclasses.MISSING,
                    init=True,
                    repr=False,
                    hash=None,
                    compare=False,
                    metadata=None,
                    kw_only=dataclasses.MISSING
                )
                f.related_cls = cls
                setattr(cls, field, f)
                continue
            field_value = cls.__dict__[field]
            if isinstance(field_value, dataclasses.Field):
                if field_value.default is dataclasses.MISSING:
                    f = MissingField(
                        default=dataclasses.MISSING,
                        default_factory=field_value.default_factory,
                        init=field_value.init,
                        repr=field_value.repr,
                        hash=field_value.hash,
                        compare=field_value.compare,
                        metadata=field_value.metadata,
                        kw_only=field_value.kw_only,
                    )
                    f.related_cls = cls
                    setattr(cls, field, f)
                    continue
        # class is prepared to process by dataclass decorator
