"""Minimal model for this example"""

import pydantic


class NestedDict(dict):
    """Dictionary which automatically creates nested dictionaries when accessing missing keys."""

    def __missing__(self, key):
        value = self[key] = NestedDict()
        return value


class Address(pydantic.BaseModel):
    """Example of an address model with simple fields."""

    house_number: int
    street: str
    city: str


class Person(pydantic.BaseModel):
    """Example of a person model with simple fields."""

    name: str
    age: pydantic.NonNegativeInt
    job: str = "Developer"
    address: Address | None = None

    @pydantic.model_validator(mode="before")
    @classmethod
    def json_editor_parse(cls, data):
        if isinstance(data, dict):
            out = NestedDict()
            for k, v in data.items():
                if k.startswith("root[") and k.endswith("]"):
                    parent = out
                    *sub_ks, leaf = k.removeprefix("root[").removesuffix("]").split("][")
                    while sub_ks:
                        sub_k = sub_ks.pop(0)
                        parent = parent[sub_k]
                    parent[leaf] = v
                else:
                    out[k] = v
            return out
        return data
