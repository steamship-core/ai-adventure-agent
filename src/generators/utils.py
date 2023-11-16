def safe_format(text: str, params: dict) -> str:
    """Safely formats a user-provided string by replacing {key} with `value` for all (key,value) pairs in `params`."""
    ret = text
    for (key, value) in params.items():
        if value is not None:
            ret = ret.replace("{" + key + "}", str(value))

    return ret
