
def safe_format(text: str, params: dict) -> str:
    """Safely formats a user-provided string by replacing {key} with `value` for all (key,value) pairs in `params`."""
    ret = text
    for (key, value) in params.items():
        ret = ret.replace("{" + key + "}", value)

    return ret
