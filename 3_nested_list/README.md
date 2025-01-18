# Nested List

## The problem

We want to add a list to our model for people to have hobbies, but Pydantic complains that indices must be integers
instead of strings, what's going on?

> Note that we updated a few lines in the [HTML functions](./html.py) to add hobbies support as well

```python
class Person(pydantic.BaseModel):
    ...
    hobbies: list[str] = pydantic.Field(default_factory=list)
```

```console
INFO:     127.0.0.1:39578 - "POST / HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
Traceback (most recent call last):
...
TypeError: list indices must be integers or slices, not str
```

This happens because our `json_editor_parse` model validator function is getting a list as the `parent` variable and
trying to access `parent['0']`, which is not valid. We need to convert the string to an integer. We want to solve this
in a generic way that can handle arbitrarily nested lists because we might want to add a list to the Address model in
the future.

## Converting nested JSON Editor list fields to Pydantic

In our [model](./model.py) we add a new helper function:

```python
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
```

And we need to update our `json_editor_parse` model validator function to handle the lists and call the new function:

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
```

## Try it out

Make sure you're running the `app.py` from the current directory (you may need to stop any other FastAPI services):

```shell
uv run ./app.py
```

Let's try the "New" form now. Enter some data, including by clicking "Add item" under "Hobbies", and click "Create".

```console
INFO:     127.0.0.1:45950 - "POST / HTTP/1.1" 200 OK
```

Success!

## Next steps

This solution works for arbitrarily nested dicts and lists. What if we want to work with a
[union](https://docs.pydantic.dev/latest/concepts/unions/) type, though?
