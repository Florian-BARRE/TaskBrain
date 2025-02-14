# ====== Standard Library Imports ======
from multiprocessing import Manager
from typing import Any
import pickle

# ====== Third-Party Imports ======
from loggerplusplus import Logger


# ====== Class Part ======
class DictProxyAccessor:
    """
    Class to access a DictProxy object as if it were a normal object.
    Avoid dict["key"] notation by using dict.key notation

    Attributes:
        _dict_proxy (Manager.dict): The dictionary proxy object being wrapped.
        _name (str): The name of the object.
        _dict_proxy['_updated_attributes'] (Set[str]): A set of attributes that have been updated.
    """
    # Tuple of all types that are considered serialized directly.
    _serializable_types: tuple[type] = (
        Logger,  # Logger from loggerplusplus library is serialized since V0.1.2
        int,
        float,
        str,
        list,
        set,
        dict,
        tuple,
        type(None),
    )

    def __init__(self, name: str = "Undefined name") -> None:
        """
        Initialize the DictProxyAccessor by creating a DictProxy object.

        Args:
            name (str): The name of the object. Defaults to "Undefined name".
        """
        self._dict_proxy: Manager.dict = Manager().dict()
        self._name: str = name

        # Store the set of attributes that have been updated (subprocess side) in a
        # Manager.dict to allow access from the main process.
        self._dict_proxy["_updated_attributes"]: set[str] = set()

    def __getattr__(self, item: str) -> Any:
        """
        Get an attribute or a key from the DictProxy object.

        Args:
            item (str): The name of the attribute or key to access.

        Returns:
            Any: The value of the attribute or key.

        Raises:
            AttributeError: If the attribute or key does not exist.
        """
        if item in ["_dict_proxy", "_name"]:
            return object.__getattribute__(self, item)

        try:
            attr: Any = object.__getattribute__(self, item)
            if callable(attr):
                return attr
        except AttributeError:
            pass  # If the attribute does not exist, continue to check in _dict_proxy

        # Attempt to access an item in _dict_proxy if it is not a method
        try:
            return self._dict_proxy[item]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{item}'. "
                f"Available attributes: {self._dict_proxy.keys()}"
            )

    def __setattr__(self, key: str, value: Any, ghost_add: bool = False) -> None:
        """
        Set an attribute or a key in the DictProxy object.

        Args:
            key (str): The name of the attribute or key.
            value (Any): The value to set.
            ghost_add (bool, optional): If True, the attribute will be added to the DictProxy object
                but not to the updated attributes set. Defaults to False.
        """
        if key in ["_dict_proxy", "_name"]:
            object.__setattr__(self, key, value)
        else:
            self._dict_proxy[key] = value
            if key not in self._dict_proxy["_updated_attributes"]:
                if not ghost_add:
                    self.add_attributes_to_synchronize(key)

    def add_attributes_to_synchronize(self, *args: str) -> None:
        """
        Add attributes to the updated attributes set.

        Args:
            *args (str): The names of the attributes to add.
        """
        for key in args:
            self._dict_proxy["_updated_attributes"] |= {
                key}  # Add the key to the set via union ('add' method does not work)

    def get_updated_attributes(self) -> set[str]:
        """
        Get the set of attributes that have been updated.

        Returns:
            Set[str]: The set of updated attribute names.
        """
        return self._dict_proxy["_updated_attributes"]

    def remove_updated_attribute(self, key: str) -> None:
        """
        Remove an attribute from the updated attributes set.

        Args:
            key (str): The name of the attribute to remove.
        """
        if key in self._dict_proxy["_updated_attributes"]:
            # self._dict_proxy["_updated_attributes"].discard(key)  # Remove the key from the set via discard
            self._dict_proxy["_updated_attributes"] -= {
                key}  # Remove the key from the set via difference ('remove' method does not work)

    def get_dict(self) -> dict:
        """
        Return the underlying DictProxy object as a regular dictionary.

        Returns:
            dict: The dictionary representation of the DictProxy object.
        """
        # Exclude the "_updated_attributes" key from the returned dictionary (it is a protected key)
        return {k: v for k, v in self._dict_proxy.items() if k != "_updated_attributes"}

    def __str__(self) -> str:
        """
        Return the string representation of the object.

        Returns:
            str: The name of the object.
        """
        return self._name

    def __repr__(self) -> str:
        """
        Return the official string representation of the object.

        Returns:
            str: The name of the object.
        """
        return self.__str__()

    @classmethod
    def add_serializable_type(cls, new_type: type, test_instance: Any = None) -> bool:
        """
        Add a new type to the set of serializable types.

        Args:
            new_type (type): The type to add.
            test_instance (Any, optional): An instance of the type to test serialization.
                                           If provided, it will be serialized to verify compatibility.

        Returns:
            bool: True if the type was successfully added, False otherwise.
        """
        tmp_logger = Logger(identifier="DictProxyAccessor", follow_logger_manager_rules=True)
        if test_instance is not None:
            try:
                pickle.dumps(test_instance)  # Test if the instance can be serialized
                tmp_logger.info(f"Type {new_type} is serializable")
            except (pickle.PickleError, TypeError) as e:
                tmp_logger.error(f"The provided instance of {new_type} is not serializable - {e}")
                return False
        else:
            tmp_logger.warning(f"No test instance provided, the type ({new_type}) will be added without verification")

        cls._serializable_types += (new_type,)
        tmp_logger.info(f"Type {new_type} is added to the list of serializable types")
        return True

    @staticmethod
    def is_serialized(obj: Any) -> bool:
        """
        Check if an object is of a type that is considered serialized directly.

        Args:
            obj (Any): The object to check.

        Returns:
            bool: True if the object is serialized, False otherwise.
        """
        if isinstance(obj, DictProxyAccessor._serializable_types):
            return True

        # Special case for an object with a __name__ attribute equal to "CONFIG".
        try:
            return obj.__name__ == "CONFIG"
        except AttributeError:  # If the object doesn't have the __name__ attribute.
            return False
