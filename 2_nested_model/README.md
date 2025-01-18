# Nested Model

## The problem

We want to create a nested model for an address field:

```python
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
```

> Note that we updated a few lines in the [HTML functions](./html.py) to add address support as well

However, our previous `json_editor_parse` model validator function only partially fixes the key names:

```text
root[address][house_number]  becomes  address][house_number
root[address][street]        becomes  address][street
root[address][city]          becomes  address][city
```

So Pydantic can't process the nested model correctly.

## Converting nested JSON Editor fields to Pydantic

In our [model](./model.py) we add a new helper class:

```python
class NestedDict(dict):
    """Dictionary which automatically creates nested dictionaries when accessing missing keys."""

    def __missing__(self, key):
        value = self[key] = NestedDict()
        return value
```

And we need to update our `json_editor_parse` model validator function to create a nested data structure:

```python
class Person(pydantic.BaseModel):
    ...

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
```

## Try it out

Make sure you're running the `app.py` from the current directory (you may need to stop any other FastAPI services):

```shell
uv run ./app.py
```

Let's try the "New" form now. Enter some data, including by setting "address" to "Address" instead of "null", and
click "Create".

```console
INFO:     127.0.0.1:45950 - "POST / HTTP/1.1" 200 OK
```

Success!

## Next steps

This solution works for nested dicts, but will fail if you have a list in your model because indices must be integers,
not strings. We'll look into that next.
