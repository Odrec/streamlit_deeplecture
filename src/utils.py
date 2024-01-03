import json
import gzip


def open_json_data_gzipped(gzipped_file_path) -> dict:
    """
        Open the gzipped JSON file and load its contents into a dictionary.

        Parameters:
        - gzipped_file_path (Path): Path to the gzipped JSON file.

        Returns:
        - data_dict: Dictionary containing data.
    """
    with gzip.open(gzipped_file_path, "rt", encoding="utf-8") as gzipped_file:
        data_dict = json.load(gzipped_file)
    return data_dict


def save_json_data_gzipped(gzipped_file_path, json_content):
    """
    Save the provided JSON content to a gzipped file.

    Parameters:
    - gzipped_file_path (Path): Path to the gzipped JSON file to be saved.
    - json_content (dict): JSON content to be saved to the file.

    Returns:
    - None
    """
    with gzip.open(gzipped_file_path, "wt", encoding="utf-8") as gzipped_file:
        json.dump(json_content, gzipped_file)


def open_json_data_file(path_json_data_file) -> dict:
    """
        Open the JSON file and load its contents into a dictionary.

        Parameters:
        - path_text_data_file (Path): Path to the JSON file.

        Returns:
        - dict: Dictionary containing text data.
    """
    with open(path_json_data_file, 'r', encoding='utf-8') as json_file:
        data_dict = json.load(json_file)
    return data_dict


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
