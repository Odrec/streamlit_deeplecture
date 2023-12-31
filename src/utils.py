import json


def open_json_data_file(path_json_data_file) -> dict:
    """
        Open the JSON file and load its contents into a dictionary.

        Parameters:
        - path_text_data_file (Path): Path to the JSON file.

        Returns:
        - dict: Dictionary containing text data.
    """
    with open(path_json_data_file, 'r', encoding='utf-8') as json_file:
        text_data = json.load(json_file)
    return text_data


def save_json_data_file(path_json_data_file, json_content):
    """
    Save the provided JSON content to a file.

    Parameters:
    - path_json_data_file (Path): Path to the JSON file to be saved.
    - json_content (dict): JSON content to be saved to the file.

    Returns:
    - None
    """
    with open(path_json_data_file, 'w') as json_file:
        json.dump(json_content, json_file, indent=4)
