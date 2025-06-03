"""
Importing this file and then calling pyjson_magic.initialize() will allow all classes to become json serializable. The
"__json__" method must be defined over a class, which allows for custom serialization of the class. For loading into the
class, each key from teh incoming dictionary must exist as a class attribute, and the value is then loaded itself, to
allow for recursive loading of classes. This is useful for classes that contain other classes. To simplify
serialization, the "@auto_json" decorator can be used, where all attributes will be serialized as-is, without any custom
logic. This is useful for classes that do not require custom serialization but still need to be JSON serializable.
"""
from json import JSONDecoder, JSONEncoder
import json
from typing import Any

__INITIALIZED = False


class CalledTwiceException(Exception):
    """
    Exception raised when the pyjson_magic module is initialized more than once. This is to prevent multiple
    initializations, which could lead to unexpected behavior.
    """


def auto_json(cls: type) -> type:
    """
    A decorator that automatically adds a __json__ method to the class, which serializes all attributes of the class as-is.
    This is useful for classes that do not require custom serialization logic but still need to be JSON serializable.
    """

    def __json__(self) -> dict:
        """
        Serialize the object to a dictionary, including all attributes that do not start with "__".
        """
        return {k: v for k, v in self.__dict__.items() if not k.startswith("__")}

    cls.__json__ = __json__
    return cls


def __override_json_encoder(self, obj: object) -> dict:
    """
    Override the default JSONEncoder to use the custom serialization method defined in the class. This will replace the
    "default" method of the JSONEncoder class, which is used to serialize objects to JSON.
    """

    # Add type information to the object, so that it can be used in the deserialization process.
    fully_qualified_type = f"{obj.__class__.__module__}.{obj.__class__.__name__}"
    type_info = {"__type__": fully_qualified_type}

    # If the object has a __json__ method, call it to get the serialized representation.
    if hasattr(obj, "__json__"):
        return type_info | obj.__json__()

    # If the object does not have a __json__ method, raise a TypeError to indicate that it cannot be serialized.
    else:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable.")


def __override_json_decoder(self, dct: Any) -> object:
    """
    Override the default JSONDecoder to use the custom deserialization method defined in the class. This will replace
    the "decode" method of the JSONDecoder class, which is used to deserialize JSON objects into Python objects. This is
    a bit messy as the "decode" method should not be overridden, but there is no other intermediary method to handle
    default decoding failures.
    """

    def _internal(dct: Any) -> object:
        # Ensure the json is a dictionary and contains the type information.
        if isinstance(dct, dict) and "__type__" in dct:
            type_name = dct.pop("__type__")

            # Dynamically import the class based on the type name.
            try:
                module_name, class_name = type_name.rsplit(".", 1)
                module = __import__(module_name, fromlist=[class_name])
                cls = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                raise TypeError(f"Could not find class {type_name} for deserialization: {e}")

            # Create the class but bypass the __init__ method to avoid issues with missing attributes.
            instance = cls.__new__(cls)

            # Add all the attributes from the dictionary to the instance.
            for key, value in dct.items():
                # If the value is a dictionary, recursively deserialize it.
                value = _internal(value)
                setattr(instance, key, value)

            # Return the instance.
            return instance

        return dct

    dct = self.original_decode(dct)
    return _internal(dct)


def init() -> None:
    """
    Initialize the pyjson_magic module to make all classes in this module JSON serializable, as long as they contain
    __json__. This function should be called at the start of the application to ensure that all classes can be
    serialized and deserialized correctly.
    """

    global __INITIALIZED

    # Check if the module has already been initialized.
    if __INITIALIZED:
        raise CalledTwiceException("pyjson_magic has already been initialized. It can only be initialized once.")

    # Patch the JSONEncoder and JSONDecoder classes to use the custom serialization and deserialization methods.
    JSONEncoder.default = __override_json_encoder

    # Patch the JSONDecoder to use the custom deserialization method.
    JSONDecoder.original_decode = JSONDecoder.decode
    JSONDecoder.decode = __override_json_decoder

    # Set the initialized flag to True to prevent re-initialization.
    __INITIALIZED = True
