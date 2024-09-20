import dataclasses
import typing
from abc import abstractmethod, ABC

import pytest

from dataclasses_mod import abc


@dataclasses.dataclass
class A(abc.ABC):

    @property
    @abstractmethod
    def a(self) -> int:
        ...


def test_base_with_abs_method():
    # A is abstract
    with pytest.raises(TypeError, match=r"^Can't instantiate abstract class .* method '?a'?$"):
        A()
    # but a is available
    assert A.a


class Base(ABC):
    Derived: type
    DerivedDataClass: type

    @abstractmethod
    def test_derived(self):
        ...

    @abstractmethod
    def _test_dataclass(self, cls):
        ...

    def test_derived_dataclass(self):
        self._test_dataclass(self.DerivedDataClass)

        class SecondDerived(self.DerivedDataClass):
            pass

        @dataclasses.dataclass
        class SecondDerivedDataClass(self.DerivedDataClass):
            pass

        self._test_dataclass(SecondDerived)
        self._test_dataclass(SecondDerivedDataClass)


class TestOnlyAnnotation(Base):
    class Derived(A):
        a: int

    @dataclasses.dataclass
    class DerivedDataClass(A):
        a: int

    def test_derived(self):
        # still abstract, can't inherit A.a
        with pytest.raises(TypeError, match=r"^Can't instantiate abstract class .* method '?a'?$"):
            self.Derived()
        assert self.Derived.a != A.a
        assert isinstance(self.Derived.a, dataclasses.Field)

    def _test_dataclass(self, cls):
        # not abstract, attribute is not available as no default value, one argument is requires for init
        with pytest.raises(AttributeError):
            cls.a
        with pytest.raises(TypeError, match=r"missing 1 required positional argument: '?a'?$"):
            cls()
        assert cls(1).a == 1


class TestAnnotationAndField(Base):
    class Derived(A):
        a: int = dataclasses.field()

    @dataclasses.dataclass
    class DerivedDataClass(A):
        a: int = dataclasses.field()

    def test_derived(self):
        # still abstract, A.a is override as field
        with pytest.raises(TypeError, match=r"^Can't instantiate abstract class .* method '?a'?$"):
            self.Derived()
        assert self.Derived.a != A.a
        assert isinstance(self.Derived.a, dataclasses.Field)

    def _test_dataclass(self, cls):
        # not abstract, attribute is not available as no default value, one argument is requires for init
        with pytest.raises(AttributeError):
            cls.a
        with pytest.raises(TypeError, match=r"missing 1 required positional argument: '?a'?$"):
            cls()
        assert cls(1).a == 1


class TestClassVarAnnotation(Base):
    class Derived(A):
        a: typing.ClassVar[int]

    @dataclasses.dataclass
    class DerivedDataClass(A):
        a: typing.ClassVar[int]

    def test_derived(self):
        self._test_dataclass(self.Derived)

    def _test_dataclass(self, cls):
        # still abstract, attribute a no affected, A.a is available
        assert cls.a == A.a
        with pytest.raises(TypeError, match=r"^Can't instantiate abstract class .* method '?a'?$"):
            cls()


class TestAnnotationWithDefaultValue(Base):
    class Derived(A):
        a: int = 10

    @dataclasses.dataclass
    class DerivedDataClass(A):
        a: int = 11

    def test_derived(self):
        # not abstract, a is only class var
        assert self.Derived.a == 10
        assert self.Derived().a == 10
        with pytest.raises(TypeError, match=r"takes 1 positional argument but 2 were given$"):
            self.Derived(1)

    def _test_dataclass(self, cls):
        # not abstract, attribute has default value
        assert cls.a == 11
        assert cls().a == 11
        assert cls(2).a == 2


class TestAnnotationWithDefaultValueInField(Base):
    class Derived(A):
        a: int = dataclasses.field(default=12)

    @dataclasses.dataclass
    class DerivedDataClass(A):
        a: int = dataclasses.field(default=13)

    def test_derived(self):
        # not abstract, a is only class var and it's field
        assert isinstance(self.Derived.a, dataclasses.Field) and self.Derived.a.default == 12
        assert isinstance(self.Derived().a, dataclasses.Field) and self.Derived().a.default == 12
        with pytest.raises(TypeError, match=r"takes 1 positional argument but 2 were given$"):
            self.Derived(1)

    def _test_dataclass(self, cls):
        # not abstract, attribute has default value
        assert cls.a == 13
        assert cls().a == 13
        assert cls(3).a == 3


class TestClassVarAnnotationWithDefault(Base):
    class Derived(A):
        a: typing.ClassVar[int] = 15

    @dataclasses.dataclass
    class DerivedDataClass(A):
        a: typing.ClassVar[int] = 15

    def test_derived(self):
        self._test_dataclass(self.Derived)

    def _test_dataclass(self, cls):
        # still abstract, attribute a no affected, A.a is available
        assert cls.a == 15
        assert cls().a == 15
        with pytest.raises(TypeError, match=r"takes 1 positional argument but 2 were given$"):
            cls(9)


class TestAnnotationWithDefaultFactoryInField(Base):
    class Derived(A):
        a: int = dataclasses.field(default_factory=int)

    @dataclasses.dataclass
    class DerivedDataClass(A):
        a: int = dataclasses.field(default_factory=int)

    def test_derived(self):
        # abstract, a is only class var and it's field
        assert isinstance(self.Derived.a, dataclasses.Field) and self.Derived.a.default_factory is int
        with pytest.raises(TypeError, match=r"^Can't instantiate abstract class .* method '?a'?$"):
            self.Derived()

    def _test_dataclass(self, cls):
        # not abstract, attribute has default factory but not available as class var
        with pytest.raises(AttributeError):
            cls.a
        assert cls().a == 0
        assert cls(3).a == 3


class TestImplementation(Base):
    class Derived(A):
        @property
        def a(self) -> int:
            return 0

    @dataclasses.dataclass
    class DerivedDataClass(A):
        @property
        def a(self) -> int:
            return 1

    def test_derived(self):
        # not abstract any more, standard class
        assert self.Derived.a != A.a
        assert self.Derived().a == 0

    def _test_dataclass(self, cls):
        # not abstract any more, standard dataclass class without fields
        assert cls.a != A.a
        assert cls().a == 1
        with pytest.raises(TypeError, match=r"takes 1 positional argument but 2 were given$"):
            cls(0)


def test_abs_field_without_annotation():
    with pytest.raises(TypeError, match=r"'a' is a field but has no type annotation"):

        @dataclasses.dataclass
        class AbsField(abc.ABC):
            a = abc.abstractfield()


class AbsField(abc.ABC):
    a: int = abc.abstractfield()


@dataclasses.dataclass
class AbsFieldDataClass(AbsField):
    a: int = abc.abstractfield()


def test_abs_field():
    AbsField()
    assert isinstance(AbsField.a, dataclasses.Field)


def test_abs_field_in_dataclass():
    with pytest.raises(TypeError, match=r"Can't instantiate abstract class .* with abstract field '?a'?"):
        AbsFieldDataClass()
    with pytest.raises(AttributeError):
        AbsFieldDataClass.a


def test_abs_field_in_derived():

    class Derived(AbsFieldDataClass):
        pass

    with pytest.raises(TypeError, match=r"Can't instantiate abstract class .* with abstract field '?a'?"):
        Derived()
    with pytest.raises(AttributeError):
        Derived.a


def test_abs_field_override_in_derived():

    class Derived(AbsFieldDataClass):
        a = 111

    assert Derived.a == 111
    assert Derived().a == 111


def test_abs_field_in_derived_dataclass():

    @dataclasses.dataclass
    class Derived(AbsFieldDataClass):
        pass

    with pytest.raises(TypeError, match=r"Can't instantiate abstract class .* with abstract field '?a'?"):
        Derived()
    with pytest.raises(AttributeError):
        Derived.a


def test_abs_field_override_in_derived_dataclass():

    @dataclasses.dataclass
    class Derived(AbsFieldDataClass):
        a: int

    assert Derived(123).a == 123
    with pytest.raises(AttributeError):
        Derived.a


def test_abs_field_override_with_default_in_derived_dataclass():

    @dataclasses.dataclass
    class Derived(AbsFieldDataClass):
        a: int = 321

    assert Derived(123).a == 123
    assert Derived().a == 321
    assert Derived.a == 321