"""Simple HTML template

You can use anything you want to generate the HTML, this is just a simple example.
"""

import json
from pathlib import Path
from textwrap import dedent, indent

from model import Person, Address


def _template(title: str, content: str) -> str:
    return dedent(f"""\
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <title>{title}</title>
            <meta name="description" content="A simple web application for demonstrating JSON Editor and FastAPI integration">
            <meta name="keywords" content="JSON Editor, FastAPI, Python">
            <!-- Include JSON Editor -->
            <script src="{"/static/jsoneditor.min.js" if (Path(__file__).parent.parent / "static").is_dir() else "https://cdn.jsdelivr.net/npm/@json-editor/json-editor@latest/dist/jsoneditor.min.js"}"></script>
        </head>
        <body>
            {indent(content, " " * 4)}
        </body>
        </html>
        """)


def html_home(content: str) -> str:
    """Home page with list of existing models and form for creating new models."""
    return _template(
        "People",
        dedent(f"""\
            <div>
                <h2>People</h2>
                {indent(content, " " * 4)}
            </div>
            <h2>New</h2>
            <form method="post" action="/">
                <div id="new-person">
                    <!-- Inject the JSON Editor here, using the JSON Schema from the Person model -->
                    <script>
                        var editor = new JSONEditor(
                            document.getElementById('new-person'),
                            {{
                                disable_collapse: true,
                                disable_edit_json: true,
                                disable_properties: true,
                                schema: {json.dumps(Person.model_json_schema())}
                            }},
                        );
                    </script>
                </div>
                <input type="submit" value="Create"></input>
            </form>
        """),
    )


def html_address(address: Address) -> str:
    """Snippet for displaying an address."""
    return dedent(f"""\
        <p>Address: {address.house_number} {address.street}, {address.city}</p>
        """)


def html_hobbies(hobbies: list[str]) -> str:
    """Snippet for displaying a list of hobbies."""
    return dedent(f"""\
        <p>Hobbies:
            <ul>
                {indent("\n".join(f"<li>{hobby}</li>" for hobby in hobbies), " " * 12)}
            </ul>
        </p>
        """)


def html_contacts(contacts: list[Person]) -> str:
    """Snippet for displaying a list of contacts."""
    return dedent(f"""\
        <p>Contacts:
            <ul>
                {indent("\n".join(f"<li>{contact.name} [{contact.__class__.__name__}]</li>" for contact in contacts), " " * 12)}
            </ul>
        </p>
        """)


def html_person(person: Person, index: int) -> str:
    """Snippet for listing a single person."""
    return dedent(f"""\
        <div>
            <h2><a href="/{index}">{person.name}</a></h2>
            <p>Age: {person.age}</p>
            <p>Job: {person.job}</p>
            {html_address(person.address) if person.address else ""}
            {html_hobbies(person.hobbies) if person.hobbies else ""}
            {html_contacts(person.contacts) if person.contacts else ""}
        </div>
        """)


def html_edit(person: Person, index: int) -> str:
    """Page to edit an existing person, pre-filled with existing data."""
    return _template(
        person.name,
        dedent(f"""\
            <h2>Edit</h2>
            <form method="post" action="/{index}">
                <div id="edit-person">
                    <!-- Inject the JSON Editor here, using the JSON Schema from the Person model -->
                    <!-- and initial data from the Person instance -->
                    <script>
                        var editor = new JSONEditor(
                            document.getElementById('edit-person'),
                            {{
                                disable_collapse: true,
                                disable_edit_json: true,
                                disable_properties: true,
                                schema: {json.dumps(Person.model_json_schema())},
                                startval: {person.model_dump_json()}
                            }},
                        );
                    </script>
                </div>
                <input type="submit" value="Update"></input>
            </form>
            """),
    )
