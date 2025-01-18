# The problem

We want to use modern python tools for our new website. Maybe we have an API driven product and want to create a quick
UI to interact with it. We've already got our [Pydantic](https://docs.pydantic.dev/latest/) models
and [FastAPI](https://fastapi.tiangolo.com/), how do we get simple forms for our models without having to create them
all by hand? [Django's admin interface](https://docs.djangoproject.com/en/5.1/ref/contrib/admin/) can do it, why not
FastAPI?

## Partial solution

FastAPI provides a [Swagger](https://fastapi.tiangolo.com/how-to/configure-swagger-ui/)
and [ReDoc](https://fastapi.tiangolo.com/reference/openapi/docs/) interface that have "Try it out" functionality, but
that's not a full solution with pre-filled forms for existing data.

## Better solution

Pydantic can create a [JSON schema](https://docs.pydantic.dev/latest/concepts/json_schema/) for a model,
and [JSON Editor](https://github.com/json-editor/json-editor) can turn a JSON schema into a form.

## Setup

We've created our simple [model](./model.py), enabled JSON Editor in our [HTML templates](./html.py), and created
our [FastAPI endpoints](./app.py). Now we just need to run it:

```shell
uv run ./app.py
```

```console
INFO:     Started server process [153291]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Check endpoints

Navigating to [our site](http://127.0.0.1:8000) we see our example data and a new object form, all good so far!

Let's check that the form endpoints work correctly:

```shell
curl http://127.0.0.1:8000/ -H "Content-Type: application/x-www-form-urlencoded" -d "name=Foo%20Bar&age=18"
```

Now refresh [our site](http://127.0.0.1:8000), and we see the new entry for Foo Bar, so we know the endpoints work!

## Check JSON Editor form

Let's try the "New" form now. Enter some data and click "Create".

```console
INFO:     127.0.0.1:55556 - "POST / HTTP/1.1" 422 Unprocessable Entity
```

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

😢

## More problems

So JSON Editor and FastAPI don't work well together "out of the box". Don't worry, though; in the next sections we'll
get them working correctly!
