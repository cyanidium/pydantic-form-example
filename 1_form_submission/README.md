# Form Submission

## The problem

JSON Editor is sending form data in a different format than Pydantic expects. Look closely at the output from
the [previous section](../0_the_problem/README.md):

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": [
        "body",
        "name"
      ],
      "msg": "Field required",
      "input": {
        "job": "Developer",
        "root[name]": "Foo Bar",
        "root[age]": "21",
        "root[job]": "Sales"
      }
    },
    {
      "type": "missing",
      "loc": [
        "body",
        "age"
      ],
      "msg": "Field required",
      "input": {
        "job": "Developer",
        "root[name]": "Foo Bar",
        "root[age]": "21",
        "root[job]": "Sales"
      }
    }
  ]
}
```

Note that the data we're sending is all wrapped with `root[]`, and because `job` isn't in the data Pydantic has filled
it with the default value.

## Converting JSON Editor fields to Pydantic

In our [model](./model.py) we add a model validator that extracts the correct key from JSON Editor's data:

```python
class Person(pydantic.BaseModel):
    ...

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
```

> Note that JSON Editor has a `form_name_root` setting that can change the name from "root" to something else

## Try it out

Make sure you're running the `app.py` from the current directory (you may need to stop any other FastAPI services):

```shell
uv run ./app.py
```

Let's try the "New" form now. Enter some data and click "Create".

```console
INFO:     127.0.0.1:45950 - "POST / HTTP/1.1" 200 OK
```

Success!

## Next steps

This solution works for simple models, but doesn't handle any cases of nested data. We'll look into that next.
