import logging
from typing import List, Union

from steamship import Block, MimeTypes, SteamshipError


def safe_format(text: str, params: dict) -> str:
    """Safely formats a user-provided string by replacing {key} with `value` for all (key,value) pairs in `params`."""
    logging.info(f"Safe Format Text {text} with {params}")
    ret = text
    for (key, value) in params.items():
        if value is not None:
            ret = ret.replace("{" + key + "}", str(value))
    return ret


def block_to_config_value(block: Block) -> str:
    if block.mime_type == MimeTypes.TXT:
        generated_value = block.raw().decode("utf-8").strip("\"'\n\t ")
    else:
        generated_value = block.to_public_url()
    return generated_value


def get_keypath_value(obj: dict, keypath: List[Union[str, int]]) -> any:
    """Gets the value at the dotted keypath.

    - foo -> obj["foo"]
    - foo.3.bar -> obj["foo"][3]["bar"]
    """
    if len(keypath) == 0:
        raise SteamshipError(message="Keypath must be >0 length.")

    ptr = obj
    for key in keypath:
        # Aggressively catch error cases.
        if isinstance(key, int) and not isinstance(ptr, list):
            raise SteamshipError(
                message=f"Keypath traversal expected a list, but found {ptr}."
            )
        if isinstance(key, str) and not isinstance(ptr, dict):
            raise SteamshipError(
                message=f"Keypath traversal expected a dict, but found {ptr}."
            )
        # Traverse the path.
        ptr = ptr[key]
    return ptr


def set_keypath_value(obj: dict, keypath: List[Union[str, int]], value):  # noqa: C901
    """Gets the value at the dotted keypath.

    - foo -> obj["foo"]
    - foo.3.bar -> obj["foo"][3]["bar"]
    """
    if len(keypath) == 0:
        raise SteamshipError(message="Keypath must be >0 length.")

    ptr = obj
    final_key = keypath[-1]

    for i, key in enumerate(keypath[:-1]):
        next_key = keypath[i + 1]
        if isinstance(key, int):
            if not isinstance(ptr, list):
                raise SteamshipError(
                    message=f"Keypath traversal expected a list, but found {ptr}."
                )
            while len(ptr) < key + 1 and key >= 0:
                ptr.append({})

        if not isinstance(ptr, dict) and not isinstance(ptr, list):
            raise SteamshipError(
                message=f"Keypath traversal expected a dict, but found {ptr}."
            )

        if ptr[key] is None:
            # FLAG
            if isinstance(next_key, int):
                ptr[key] = []
            else:
                ptr[key] = {}

        ptr = ptr[key]

    if isinstance(final_key, int):
        while len(ptr) < final_key + 1 and final_key >= 0:
            ptr.append(None)

    ptr[final_key] = value
