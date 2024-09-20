# Dataclasses MOD

This library provides a extensions for [dataclasses](https://docs.python.org/3/library/dataclasses.html).

## Abstract dataclasses

The module `dataclasses_mod.abc` allows to define abstract classes that compatible with dataclasses.

Using the standard `dataclass` decorator from the `dataclasses` module 
to implement abstract properties of abstract class derived from `abc.ABC` will result in a TypeError.

Example:

```python
from dataclasses import dataclass
from abc import ABC, abstractmethod

# An abstract base class with an abstract property
class A(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

@dataclass
class B(A):
    name: str

# TypeError: Can't instantiate abstract class B without an implementation for abstract method 'name'
b = B(name='A')
```

This module solves it easily by replace import `ABC` from `abc` to `dataclasses_mod.abc`.

```python
from dataclasses import dataclass
from dataclasses_mod.abc import ABC, abstractmethod

class A(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

@dataclass
class B(A):
    name: str

# Class B is not abstract any more
b = B(name='A')
```

However, there are tradeoffs that introduce side effects:

* An annotation does not allow to inherit abstract attribute (instead of it stub field is used)
  even without `dataclass` decorator:

```python
from dataclasses_mod.abc import ABC, abstractmethod

class A(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

class B(A):
    name: str

# B.name is dataclass.Field
assert B.name != A.name
```

* An abstract attribute will be removed from dataclass if there is no default value.

```python
from dataclasses import dataclass
from dataclasses_mod.abc import ABC, abstractmethod

class A(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

@dataclass
class B(A):
    name: str

# Result in a
B.name
```

However, it uses decorator that added to class during creation of dataclass that can be unexpected 
in case of direct access to class `__dict__`.

Finally, module `dataclasses_mod.abc` add abstract fields that required implementation in subclass. 
Abstract fields does not have a default value/factory, can be part of `__init__`, etc.

```python
from dataclasses import dataclass
from dataclasses_mod.abc import ABC, abstractfield


@dataclass
class A(ABC):
  a: int = abstractfield()
  b: str = abstractfield()

# TypeError: Can't instantiate abstract class A with abstract fields 'a', 'b'
A()
# type object 'A' has no attribute 'a'
A.a
```

Abstract field is not available as class variable of dataclasses that is implemented using decorators.
In general class (without `dataclass` decorator) abstract fields are general class variables.

```python
import dataclasses
from dataclasses_mod.abc import ABC, abstractfield


class A(ABC):
  a: int = abstractfield()


# A.a is abstract field
isinstance(A.a, dataclasses.Field)
```