"""Minimal model for this example"""

import pydantic


class Person(pydantic.BaseModel):
    """Example of a person model with simple fields."""

    name: str
    age: pydantic.NonNegativeInt
    job: str = "Developer"

    @pydantic.model_validator(mode="before")
    @classmethod
    def json_editor_parse(cls, data):
        if isinstance(data, dict):
            out = {}
            for k, v in data.items():
                if k.startswith("root[") and k.endswith("]"):
                    k = k.removeprefix("root[").removesuffix("]")
                out[k] = v
            return out
        return data
