"""Minimal model for this example"""

import pydantic


class Person(pydantic.BaseModel):
    """Example of a person model with simple fields."""

    name: str
    age: pydantic.NonNegativeInt
    job: str = "Developer"
