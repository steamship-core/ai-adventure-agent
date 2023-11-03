from typing import Type, List

from pydantic import BaseModel

from schema.server_settings import ServerSettings


def get_model_schema(t: Type[BaseModel]) -> List[dict]:
    fields = []
    for name, field in t.__fields__.items():
        field_info = field.field_info
        field_dict = {
            "name": field.name,
            "nullable": field.allow_none,
            "type": field.type_.__name__,
            "description": field_info.description,
            "default": field.default,
            "category": field_info.extra.get("category")
        }
        fields.append(field_dict)
    return fields


if __name__ == "__main__":
    print(get_model_schema(ServerSettings))