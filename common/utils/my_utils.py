import json
import os
import re
import inspect
from decimal import Decimal
import datetime
from uuid import UUID

"""
This is a multi-purpose utility module that contains various functions and classes
1. JSONExplorer: A class to explore and search JSON data.
2. pretty_print_data: A function to pretty print data in a JSON-compatible format.
3. convert_to_json_compatible: A function to convert various data types into JSON-compatible formats.
4. mimic_save_sync and mimic_save_async: Functions to save data synchronously and synchronously in both pickle and JSON formats.
5. mimic_retrieve_sync and mimic_retrieve_async: Functions to retrieve data synchronously and asynchronously to mimic script behavior.
"""


class JSONExplorer:
    """
    A class to explore and search JSON data.
    """

    def __init__(self, file_path):
        """
        Initializes the JSONExplorer with data from a JSON file.
        """
        with open(file_path, 'r') as file:
            self.data = json.load(file)
        self.file_path = file_path  # Store the file path for saving changes later

    def get_config_value(self, key_path, default=None):
        """
        Retrieves a configuration value based on a key path.
        """
        keys = key_path.split('.')
        data = self.data
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return default
        return data

    def list_keys(self, data=None):
        """
        Lists all keys in the JSON data at the current level.
        """
        if data is None:
            data = self.data
        if isinstance(data, dict):
            return list(data.keys())
        return []

    def recursive_traversal(self, data=None, parent_key=''):
        """
        Recursively traverses the JSON data and prints all keys.
        """
        if data is None:
            data = self.data

        if isinstance(data, dict):
            for key, value in data.items():
                current_key = f"{parent_key}.{key}" if parent_key else key
                print(current_key)
                self.recursive_traversal(value, current_key)
        elif isinstance(data, list):
            for item in data:
                self.recursive_traversal(item, parent_key)

    def find_by_partial_key(self, partial_key, data=None):
        """
        Finds keys that include the partial key name.
        """
        if data is None:
            data = self.data

        found = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if partial_key in key:
                    found[key] = value
                found.update(self.find_by_partial_key(partial_key, value))
        elif isinstance(data, list):
            for item in data:
                found.update(self.find_by_partial_key(partial_key, item))
        return found

    def find_by_regex(self, pattern, data=None):
        """
        Finds keys that match a regular expression pattern.
        """
        if data is None:
            data = self.data

        found = {}
        regex = re.compile(pattern)
        if isinstance(data, dict):
            for key, value in data.items():
                if regex.search(key):
                    found[key] = value
                found.update(self.find_by_regex(pattern, value))
        elif isinstance(data, list):
            for item in data:
                found.update(self.find_by_regex(pattern, item))
        return found

    def get_nested_value(self, nested_key, data=None):
        """
        Retrieves the value for a nested key if it exists anywhere in the JSON data.
        """
        if data is None:
            data = self.data

        if isinstance(data, dict):
            for key, value in data.items():
                if key == nested_key:
                    return value
                elif isinstance(value, (dict, list)):
                    result = self.get_nested_value(nested_key, value)
                    if result is not None:
                        return result
        elif isinstance(data, list):
            for item in data:
                result = self.get_nested_value(nested_key, item)
                if result is not None:
                    return result
        return None

    def update_value(self, key_path, new_value):
        """
        Updates the value for a given key path in the JSON data.
        """
        keys = key_path.split('.')
        data = self.data
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = new_value
        self.save_changes()

    def save_changes(self):
        """
        Saves the current state of the JSON data back to the file.
        """
        with open(self.file_path, 'w') as file:
            json.dump(self.data, file, indent=4)

    def pretty_print_json(self, indent=4):
        """
        Prints the JSON data in a formatted, human-readable way.
        """
        print(f"\nPretty Print:\n{json.dumps(self.data, indent=indent)}\n")


def pretty_print_data(arg, indent=4):
    frame = inspect.currentframe()
    try:
        context = inspect.getouterframes(frame)
        name = None
        for var_name, var_val in context[1].frame.f_locals.items():
            if var_val is arg:
                name = var_name
                break

        if isinstance(arg, str) and not arg.strip().startswith(('{', '[')):
            print(f"\n{name} (string):\n{arg}")
            return

        converted_data, old_type, new_type = convert_to_json_compatible(arg)
        type_message = f" [{old_type} converted to {new_type}]" if old_type != new_type else ""
        json_string = json.dumps(converted_data, indent=indent)

        compact_json_string = re.sub(r'"\\"([^"]*)\\""', r'"\1"', json_string)
        compact_json_string = re.sub(r'\[\n\s+((?:\d+,?\s*)+)\n\s+\]', lambda m: '[' + m.group(1).replace('\n', '').replace(' ', '') + ']', compact_json_string)

        print(f"\nPretty {name}:{type_message}\n{compact_json_string}")
    finally:
        del frame


def convert_to_json_compatible(data):
    """
    Recursively converts various data types into JSON-compatible formats.
    Returns a tuple of the converted data, the original data type, and the converted data type.
    """
    old_type = type(data).__name__
    new_type = old_type

    if isinstance(data, (str, int, float, bool, type(None), UUID)):
        return str(data), old_type, new_type  # Convert UUID to str
    elif isinstance(data, (list, tuple)):
        converted_list = [convert_to_json_compatible(item)[0] for item in data]
        new_type = "list" if isinstance(data, list) else "tuple"
        return converted_list, old_type, new_type
    elif isinstance(data, dict):
        converted_dict = {key: convert_to_json_compatible(value)[0] for key, value in data.items()}
        return converted_dict, old_type, "dict"
    elif isinstance(data, datetime.datetime):
        return data.isoformat(), old_type, "str"
    elif isinstance(data, Decimal):
        return float(data), old_type, "float"
    elif hasattr(data, 'dict'):
        # For objects with a 'dict' method, use it to serialize
        return {key: convert_to_json_compatible(value)[0] for key, value in data.dict().items()}, old_type, "dict"
    else:
        try:
            return str(data), old_type, "str"
        except Exception:
            return "This data type is:", old_type, "which is not compatible with pretty print."


def convert_to_json_compatible_perfect(data):
    """
    Recursively converts various data types into JSON-compatible formats.
    Returns a tuple of the converted data, the original data type, and the converted data type.
    """
    old_type = type(data).__name__
    new_type = old_type

    if isinstance(data, (str, int, float, bool, type(None))):
        return data, old_type, new_type
    elif isinstance(data, (list, tuple)):
        converted_list = [convert_to_json_compatible(item)[0] for item in data]
        new_type = "list" if isinstance(data, list) else "tuple"
        return converted_list, old_type, new_type
    elif isinstance(data, dict):
        converted_dict = {key: convert_to_json_compatible(value)[0] for key, value in data.items()}
        return converted_dict, old_type, "dict"
    elif isinstance(data, datetime.datetime):
        return data.isoformat(), old_type, "str"
    elif isinstance(data, Decimal):
        return float(data), old_type, "float"
    elif hasattr(data, 'dict'):
        converted_obj = {key: convert_to_json_compatible(value)[0] for key, value in data.__dict__.items()}
        return converted_obj, old_type, "dict"
    else:
        try:
            return str(data), old_type, "str"
        except Exception:
            return "This data type is:", old_type, "which is not compatible with pretty print."


def print_file_link(path):
    if isinstance(path, str):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        url_compatible_path = path.replace("\\", "/")
    else:
        if not os.path.exists(str(path)):
            raise FileNotFoundError(f"The path {path} does not exist.")
        url_compatible_path = str(path).replace("\\", "/")

    print("file:///{}".format(url_compatible_path))
