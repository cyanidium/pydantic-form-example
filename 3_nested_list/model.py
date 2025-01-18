"""Minimal model for this example"""

import pydantic


def indexed_dicts_to_lists(d):
    if not isinstance(d, dict):
        # Leaf node
        return d
    if d and all(sub_k.isdigit() for sub_k in d.keys()):
        # Top level list
        return [indexed_dicts_to_lists(sub_v) for sub_v in d.values()]
    # Otherwise, we've got to iterate through a nested dictionary/list combination
    result = {}
    for k, v in d.items():
        if isinstance(v, dict) and all(sub_k.isdigit() for sub_k in v.keys()):
            # Nested list
            result[k] = [indexed_dicts_to_lists(sub_v) for sub_v in v.values()]
        elif isinstance(v, dict):
            # Nested dictionary
            result[k] = indexed_dicts_to_lists(v)
        elif isinstance(v, list):
            # Nested default list
            result[k] = [indexed_dicts_to_lists(sub_v) for sub_v in v]
        else:
            # Leaf node
            result[k] = v
    return result


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
    hobbies: list[str] = pydantic.Field(default_factory=list)

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
                        if isinstance(parent, list):
                            # Handle field with default list already created
                            if not sub_k.isdigit():
                                raise ValueError("List index must be a number")
                            if sub_ks and sub_ks[0].isdigit():
                                sub_type = list
                            else:
                                sub_type = NestedDict
                            while len(parent) <= int(sub_k):
                                parent.append(sub_type())
                            parent = parent[int(sub_k)]
                        else:
                            parent = parent[sub_k]
                    if isinstance(parent, list):
                        # Handle field with default list already created
                        if not leaf.isdigit():
                            raise ValueError("List index must be a number")
                        while len(parent) <= int(leaf):
                            parent.append(type(v)())
                        parent[int(leaf)] = v
                    else:
                        parent[leaf] = v
                else:
                    out[k] = v
            done = indexed_dicts_to_lists(out)
            return done
        return data
