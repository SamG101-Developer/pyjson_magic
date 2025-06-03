# PyJson Magic

The `pyjson_magic` package provides a way to achieve serialization and deserialization of Python objects to and from
JSON format using the `json` module, using magic methods. The `__json__` method is used to serialize the object, and
deserialization is done automatically by attribute. If every attribute needs to be serialized, then the `auto_json`
decorator can be used to automatically generate the `__json__` method:

```python
import json
from dataclasses import dataclass, field

from pyjson_magic import pyjson_magic


@pyjson_magic.auto_json
@dataclass(eq=True)
class B:
    x: int = field(default=42)
    y: str = field(default="hello")


@pyjson_magic.auto_json
@dataclass(eq=True)
class A:
    a: int = field(default=1)
    b: str = field(default="test")
    c: B = field(default_factory=B)


# Initialize the pyjson_magic module to ensure it is ready for testing.
pyjson_magic.init()
old_a = A()
new_a = json.loads(json.dumps(old_a))
assert old_a == new_a, "The serialized and deserialized objects should be equal"

# Or with files:
old_a = A()
with open("test_custom_obj.json", "w") as f:
    json.dump(old_a, f)

with open("test_custom_obj.json", "r") as f:
    new_a = json.load(f)

assert old_a == new_a, "The serialized and deserialized objects should be equal"
```