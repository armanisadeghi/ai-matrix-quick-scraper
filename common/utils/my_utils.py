import json
import os
import re
import inspect
from decimal import Decimal
import datetime
import asyncio
import pickle
from django.db.models import Model, QuerySet, ManyToManyField
from uuid import UUID

from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(os.getenv("BASE_DIR"))


"""
This is a multi-purpose utility module that contains various functions and classes
1. JSONExplorer: A class to explore and search JSON data.
2. pretty_print_data: A function to pretty print data in a JSON-compatible format.
3. convert_to_json_compatible: A function to convert various data types into JSON-compatible formats.
4. mimic_save_sync and mimic_save_async: Functions to save data synchronously and synchronously in both pickle and JSON formats.
5. mimic_retrieve_sync and mimic_retrieve_async: Functions to retrieve data synchronously and asynchronously to mimic script behavior.
"""

config_file = '../../utils/aiprog/aiprog_config.json'
config_path = os.path.join(BASE_DIR, config_file)



class AppConfig:
    _cache = None


    @classmethod
    def _load_config(cls):
        # Using the full path to open and load the configuration file
        if cls._cache is None:
            with open(config_path, 'r') as file:
                cls._cache = json.load(file)


    @classmethod
    def get_config_value(self, key_path, default=None):
        """
        Retrieves a configuration value based on a key path.

        Args:
                key_path (str): A dot-separated string representing the path to
                                                the configuration item.
                default (any): The default value to return if the key is not found.

        Returns:
                The value from the configuration if the key exists, otherwise
                returns the default value.
        """
        keys = key_path.split('.')
        data = self.data
        for key in keys:
            if key in data:
                data = data[key]
            else:
                return default
        return data


    @classmethod
    def get_multiple_config_values(cls, key_paths):
        """
        Retrieves multiple configuration values based on a list of key paths.

        Args:
                key_paths (list of str): A list of dot-separated strings representing
                                                                 the paths to the configuration items.

        Returns:
                dict: A dictionary where each key is the key path and the value is
                            the corresponding configuration value. If a key is not found,
                            its value will be None.
        """
        cls._load_config()

        values = {}
        for key_path in key_paths:
            keys = key_path.split('.')
            try:
                value = cls._cache
                for key in keys:
                    value = value[key]
                values[key_path] = value
            except KeyError:
                values[key_path] = None

        return values



def validate_config_structure():
    required_keys = ['key1', 'key2', 'nested.key3']

    for key in required_keys:
        try:
            AppConfig.get_config_value(key)
        except KeyError:
            raise ValueError(f"Missing required config key: {key}")

    # Add any additional structural checks as needed
    print("Configuration is valid.")


"""
value = AppConfig.get_config_value('oai_default_values')
print(f"OAI Defaults: {value}")

keys = ['oai_default_values.temperature', 'oai_default_values.top_p']
values = AppConfig.get_multiple_config_values(keys)
kay_parts = keys[0].split('.')
print(values)

for key, value in values.items():
    print(f"{key}: {value}")

"""


# =========== Series of functions to search for things in json files ===========


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

def saved_pretty_print_data(arg, indent=4):
    try:
        frame = inspect.currentframe()
        context = inspect.getouterframes(frame)
        name = None
        for var_name, var_val in context[1].frame.f_locals.items():
            if var_val is arg:
                name = var_name
                break

        converted_data, old_type, new_type = convert_to_json_compatible(arg)
        type_message = f" [{old_type} converted to {new_type}]" if old_type != new_type else ""
        print(f"\nPretty {name}:{type_message}\n{json.dumps(converted_data, indent=indent)}")
    except Exception as e:
        try:
            print(f"Error occurred: {e}. Attempting to print argument:\n{arg}")
        except Exception as e_inner:
            print(f"Error printing argument: {e_inner}. Something went seriously wrong.")
    finally:
        if 'frame' in locals():
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
    elif isinstance(data, Model):
        # Serialize Django model instance
        return {field.name: convert_to_json_compatible(getattr(data, field.name))[0] for field in data._meta.fields}, old_type, "dict"
    elif isinstance(data, QuerySet):
        # Convert the queryset into a list of dictionaries
        return [convert_to_json_compatible(obj)[0] for obj in data], old_type, "list[dict]"
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
    elif isinstance(data, QuerySet):
        converted_qs = list(data.values())
        return converted_qs, old_type, "list[dict]"
    else:
        try:
            return str(data), old_type, "str"
        except Exception:
            return "This data type is:", old_type, "which is not compatible with pretty print."


def print_file_link(path):
    if isinstance(path, str):
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        #if not os.path.exists(path):
            # raise FileNotFoundError(f"The path {path} does not exist.")
        url_compatible_path = path.replace("\\", "/")
    else:
        if not os.path.exists(str(path)):
            raise FileNotFoundError(f"The path {path} does not exist.")
        url_compatible_path = str(path).replace("\\", "/")

    print("file:///{}".format(url_compatible_path))


'''
# mimic module code here =====================================================
mimic_dir = "D:\\OneDrive\\dev\\PycharmProjects\\aidream\\a_starter\\utils\\mimic\\mimic_data"
os.makedirs(mimic_dir, exist_ok=True)
'''

def mimic_append_dt(identifier):
    """Appends the current date and time to the given identifier."""
    return f"{identifier}_{datetime.now().strftime('%y%m%d_%H%M%S')}"

'''
# mimic module code here =====================================================
mimic_dir = "D:\\OneDrive\\dev\\PycharmProjects\\aidream\\a_starter\\utils\\mimic\\mimic_data"
os.makedirs(mimic_dir, exist_ok=True)
'''


def mimic_get_var_name():
    """Tries to get the variable name of the caller's argument."""
    try:
        frame = inspect.currentframe()
        outer_frames = inspect.getouterframes(frame)
        call_frame = outer_frames[2].frame
        arg_info = inspect.getargvalues(call_frame)
        if arg_info.args:
            first_arg_name = arg_info.args[0]
            first_arg_value = arg_info.locals[first_arg_name]
            for var_name, var_value in call_frame.f_globals.items():
                if first_arg_value is var_value:
                    return var_name
            for var_name, var_value in call_frame.f_locals.items():
                if first_arg_value is var_value:
                    return var_name
    except Exception as e:
        print(f"Error determining variable name: {e}")
    return None

def mimic_save_sync(data, identifier=None):
    """Saves data synchronously in both pickle and JSON formats."""
    if not identifier:
        identifier = mimic_get_var_name() or f"mimic_no_name_{datetime.now().strftime('%y%m%d_%H%M%S')}"
    id_with_dt = mimic_append_dt(identifier)

    # Save as pickle
    pkl_filename = os.path.join(mimic_dir, f"{id_with_dt}.pkl")
    with open(pkl_filename, 'wb') as file:
        pickle.dump(data, file)
    print(f"Data saved to {pkl_filename}")

    # Convert to JSON-compatible format and save as JSON
    json_data = convert_to_json_compatible(data)
    json_filename = os.path.join(mimic_dir, f"{id_with_dt}.json")
    with open(json_filename, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)
    print(f"Data saved to {json_filename}")

async def mimic_save_async(data, identifier=None):
    """Saves data asynchronously by calling the synchronous save function in an executor."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, mimic_save_sync, data, identifier)

def mimic_retrieve_sync(identifier):
    """Retrieves data synchronously using the full identifier, including the datetime."""
    filename = os.path.join(mimic_dir, f"{identifier}.pkl")
    try:
        with open(filename, 'rb') as file:
            return pickle.load(file)
    except FileNotFoundError:
        print(f"No saved data found for identifier '{identifier}'.")

async def mimic_retrieve_async(identifier):
    """Retrieves data asynchronously by calling the synchronous retrieve function in an executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, mimic_retrieve_sync, identifier)


"""
# Example usage
data = "hi", datetime.datetime.now(), Decimal('10.5')

json_data = my_utils.pretty_print_data(data)
print(json.dumps(json_data, indent=4))


            {
          'time'         : datetime.datetime.now(),
          'value'        : Decimal('10.5'),
          'custom_object': "hi"
            }


# Usage within another module and function:

# Imports
import os
from utils.aiprog.json_explorer import JSONExplorer
from aidream.settings import BASE_DIR

# Within the function:
json_file = 'utils/aiprog/oai_system/oai_results/oai_json/1700932907.json'
json_path = os.path.join(BASE_DIR, json_file)
explorer = JSONExplorer(json_path)
explorer.pretty_print_json()
"""

"""
explorer = JSONExplorer(config_path)
print(f"\njson_path: {config_path}")
explorer.pretty_print_json()

json_file = 'utils/aiprog/aiprog_config.json'
json_path = os.path.join(BASE_DIR, json_file)
explorer = JSONExplorer(json_path)
print(f"\njson_path: {json_path}")


# Update a value in the JSON data
explorer.update_value('oai_default_values.temperature', 0.5)
updated_temperature = explorer.get_config_value('oai_default_values.temperature')
print(f"\nUpdated temperature: {updated_temperature}")

# Pretty print the entire JSON data
explorer.pretty_print_json()


# Pretty print the entire JSON data
explorer.pretty_print_json()
"""

"""

# List top-level keys
print(f"\n\nexplorer.list_keys(): {explorer.list_keys()}")

# Recursively traverse and print all keys
explorer.recursive_traversal()

# Find keys that contain a specific substring
partial_matches = explorer.find_by_partial_key('token')
print(f"\npartial_matches: {partial_matches}")

# Find keys that match a regular expression
regex_matches = explorer.find_by_regex(r'token')
print(f"\nregex_matches: {regex_matches}")

# Get value for a nested key
nested_value = explorer.get_nested_value('default_model')
print(f"\nNested Value for 'default_model': {nested_value}")

    # Usage
    print_all_keys(data)
"""

