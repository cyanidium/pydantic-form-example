# Nested Union

## The problem

This might not fit with the rest of the problems, but I needed to handle cases where a nested object could be one of
many classes. To make this work the form needs to include some form of 'hint' about the type being submitted/edited.

For this example we will add a field to our Person for `contacts`, which can be one of a few different classes based off
of a common base class.

> Note that we updated a few lines in the [HTML functions](./html.py) to add contacts support as well

```python
class Person(pydantic.BaseModel):
    ...
    contacts: list = pydantic.Field(default_factory=list)
```

This doesn't work because the JSON schema doesn't know what type of object can be in the list, so it doesn't create a
valid form to create a useful object. We can help by creating models for different types of `contact`:

```python
class Contact(pydantic.BaseModel):
    """Example of a contact model with simple fields."""
    name: str


class Friend(Contact):
    """Example of a friend model with additional fields."""
    known_since: datetime.datetime


class FamilyMember(Contact):
    """Example of a family member model with additional fields."""
    relationship: str
```

But this is still insufficient because FastAPI won't know which class to use, even if we update the type annotation to
be:

```python
class Person(pydantic.BaseModel):
    ...
    contacts: list[Contact | Friend | FamilyMember] = pydantic.Field(default_factory=list)
```

Plus, what if we add a new class in the future? We don't want to have to remember to include it in every type annotation
every time.

## Generate the type hint dynamically

Let's solve the last problem first. We're going to need a couple of helper functions and their supporting imports:

```python
from typing import Annotated
from typing import Any
from typing import Union


def get_discriminator_value(v: Any) -> str | None:
    if isinstance(v, dict):
        return v.get("_type", None)
    return getattr(v, "_type", None)


class Contact(pydantic.BaseModel):
    ...
    @pydantic.computed_field
    @property
    def _type(self) -> str:
        return self.__class__.__name__

    @_type.setter
    def _type(self, v: str) -> None:
        if v != self.__class__.__name__:
            raise ValueError(f"Incorrectly loading a {v} as {self.__class__.__name__} object")
        raise ValueError("Cannot set _type attribute directly")

    @classmethod
    def get_subclasses(cls, include_self=True):
        if include_self:
            yield cls
        for subclass in cls.__subclasses__():
            yield from subclass.get_subclasses()

    @classmethod
    def get_annotated_subclass_types(cls, include_self=True):
        return (Annotated[c, pydantic.Tag(c.__name__)] for c in cls.get_subclasses(include_self=include_self))


class Person(pydantic.BaseModel):
    ...
    contacts: list[
        Annotated[
            Union[*Contact.get_annotated_subclass_types()],
            pydantic.Discriminator(get_discriminator_value),
        ]
    ] = pydantic.Field(default_factory=list)
```

We create a computed field on `Contact` called `_type` that just contains the class name and can't be changed. We can
then use this and Pydantic's [Discriminated Unions](https://docs.pydantic.dev/latest/concepts/unions/#discriminated-unions-with-callable-discriminator)
to determine which class to use. We also iterate through the subclasses of `Contact` to generate the type annotation,
which means all we need to do when adding a new contact type is to subclass from `Contact` and it will automatically
contain `_type` and be included in the `contacts` type annotation.

`get_subclasses` and `get_annotated_subclass_types` don't have to be separate functions for this example, but
`get_subclasses` on its own may be useful for other logic if you're going down this path, so we've kept them separate.

Unfortunately, this doesn't solve the HTTP form problem, but even though JSON Editor now knows enough to create a
good-looking form with all the expected fields, `_type` won't get submitted which means the discriminator won't work.

## Including `_type` in the form

We don't want users having to enter the `_type` field; they already choose the type they want from a combobox and
shouldn't have to do it again. We can fix this with a bit of JSON schema manipulation, though:

```python
from pydantic_core import core_schema as cs


class Contact(pydantic.BaseModel):
    ...
    @classmethod
    def __get_pydantic_json_schema__(
            cls, core_schema: cs.CoreSchema, handler: pydantic.GetJsonSchemaHandler
    ) -> pydantic.json_schema.JsonSchemaValue:
        json_schema = handler(core_schema)
        json_schema = handler.resolve_ref_schema(json_schema)
        json_schema["properties"]["_type"] = {
            "enum": [cls.__name__],
            "default": cls.__name__,
            "type": "string",
            "title": "Type of contact",
        }
        return json_schema
```

This adds `_type` as a property to the JSON schema, allows only one valid value, and sets that value as the default.
JSON Editor uses that information to ensure that `_type` is submitted with each form.

## Try it out

Make sure you're running the `app.py` from the current directory (you may need to stop any other FastAPI services):

```shell
uv run ./app.py
```

Let's try the "New" form now. Enter some data, including by clicking "Add item" under "Contacts", and click "Create".

```console
INFO:     127.0.0.1:45950 - "POST / HTTP/1.1" 200 OK
```

Success!

## Next steps

Unfortunately, this does result in the form containing an additional combobox with redundant information, but at least
the user doesn't have to do anything with it, and it can likely be hidden with some CSS magic.

## Results

We now have a dynamically created form for Pydantic models using FastAPI. You may have noticed that the `app.py` file is
essentially the same for each version of this (other than dummy data creation). All the magic is coming from tweaks to
how Pydantic models are configured. Give it a go and adapt it to your own needs!
