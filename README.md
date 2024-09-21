# Dataclasses MOD

This library provides a extensions for [dataclasses](https://docs.python.org/3/library/dataclasses.html).

## Sanitise sensitive data

Usually, the log messages and exceptions include a lot of helpful information, for example variable values. 
In some cases, the output of this information is not secure, potentially exposing sensitive data. 
You probably would like to hide passwords or personal information to mitigate these risks.
This module has an additional layer that preprocesses variables before writing down values.

By default, it uses the function repr, which is enough in many cases. 
However, you can define a custom repr function.

```python

import dataclasses_mod

class SecureStr(str):
  pass

city = "New York"
password = SecureStr("my super secret password")

def sanitised_repr(value) -> str:
  if isinstance(value, SecureStr):
    return len(value) * "?"
  return repr(value)


dataclasses_mod.set_value_repr(sanitised_repr)

```

Also, if this function raises an exception, it will be ignored, and `"<can't repr>"` will be used instead of repr.


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

## Validation

External type checkers play a crucial role in validating data classes, 
especially in the absence of built-in validation.
They provide a way to check the types of fields, although constraints cannot be added within the data classes themselves.

Runtime validation simplifies debugging and catching errors that result in preventing bugs or undefined behavior.
This validation should not be used to check user input; it is an auxiliary tool that can be disabled.

This module introduces the support of runtime type checks and adds constraints using some sort of definition layer. 
It also has convenient tools to simplify writing custom validators.
The most important aspect is that adding validation is easy, 
as it is a tool for increasing quality instead of solving tasks.

### Type validation

A dataclass does not have any runtime validation for the field types.

The list of supported types is limited:
* python types: `str`, `int`, `None`, `list`
* generics: `list[T] | tuple[T] | set[T] `
* unions and options: `int | str`
* ellipsis and any type: `...`, `typing.Any`

Type validation is enabled by default, to avoid it use `...` or `typing.Any`.

### Field validators

Dataclasses can't provide a way to describe what values are acceptable except type constraints, 
which are usually not enough. 
For example, you know in advance that a list can not be empty or an integer can not be negative.

Even if you can check assertions while using these fields, 
it is spaghetti code because a piece of knowledge about constraints is far from the class definition.
Also, you can only check these constraints while using the instance instead of creating it.
The ability to define constraints in class definitions, together with running checks of these constraints, 
helps avoid bugs.


## Logging, debugging and exceptions

This library has a lot of logging inside it. 
Even if it allows for debugging unexpected or unclear bugs, it is very annoying. 
To avoid it, you can increase the log level:
* `debug` - to debug internal process
* `info` - to check what the library tries to do
* `warning` and higher - to use without carrying about internal staff

By default, exceptions do not have tracebacks for functions inside library and custom validators.
To enable them, use `dataclasses_mod.set_deep_exception_traceback`:

```python
import dataclasses_mod

dataclasses_mod.set_deep_exception_traceback(True)
```

Usually, it is necessary only for debugging this library. 