import json
from dataclasses import dataclass, field
from unittest import TestCase

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


@dataclass(eq=True)
class C:
    c: int = field(default=1)
    d: str = field(default="test")

    def __json__(self) -> dict:
        """
        Custom JSON serialization method for class C.
        This method is used to serialize the object to a dictionary.
        """
        return {"c": self.c}


@pyjson_magic.auto_json
@dataclass(eq=True)
class D:
    types: list[type] = field(default_factory=lambda: [A, B])


class TestCustomObj(TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize the pyjson_magic module to ensure it is ready for testing.
        pyjson_magic.init()

    def test_custom_obj_auto_json(self):
        old_a = A()
        new_a = json.loads(json.dumps(old_a))
        print(old_a, "\n", new_a)
        assert old_a == new_a, "The serialized and deserialized objects should be equal"

    def test_custom_obj_auto_json_to_file(self):
        old_a = A()
        with open("test_custom_obj.json", "w") as f:
            json.dump(old_a, f)

        with open("test_custom_obj.json", "r") as f:
            new_a = json.load(f)

        print(old_a, "\n", new_a)
        assert old_a == new_a, "The serialized and deserialized objects should be equal"

    def test_custom_obj(self):
        c = C(c=1, d="hello")
        d = C(c=1, d="world")

        c_serialized = json.dumps(c)
        d_serialized = json.dumps(d)
        assert c_serialized == d_serialized

        parsed = json.loads(c_serialized)
        print(parsed, "\n", C(c=1, d=""))
        assert parsed == C(c=1, d="test")

    def test_top_level_list(self):
        a = A()
        b = B()
        top_level_list = [a, b]
        serialized = json.dumps(top_level_list)
        deserialized = json.loads(serialized)

        assert len(deserialized) == 2
        assert isinstance(deserialized[0], A) and isinstance(deserialized[1], B)
        assert deserialized[0] == a
        assert deserialized[1] == b

    def test_type_attribute(self):
        d = D()
        serialized = json.dumps(d)
        deserialized = json.loads(serialized)

        assert deserialized == d
