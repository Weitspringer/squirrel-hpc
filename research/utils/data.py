"""Utils for data management."""

import json
from pathlib import Path


def save_dict_as_json(data: dict, name: str, folder_path: Path):
    """Save a dictionary as a json file."""
    file_name = f"{name}.json"
    result_file = folder_path / file_name
    folder_path.mkdir(exist_ok=True)
    file_content = json.dumps(data, indent=4, sort_keys=False)
    with open(result_file, "w", encoding="utf-8") as my_file:
        my_file.write(file_content)
