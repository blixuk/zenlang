import json
from dataclasses import asdict
from typing import Any


def print_data(data: Any, as_json: bool = False, title: str | None = None) -> None:
    if title:
        print(f"-- {title} --")

    if as_json:
        print(json.dumps(asdict(data), indent=4))
    else:
        print(data)
