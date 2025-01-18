"""FastAPI app for running example"""

from pathlib import Path
from typing import Annotated

import fastapi
import uvicorn
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

import html
from model import Person, Address

# Global state, this would be in a database for real world usage
models = []


def get_app():
    app = fastapi.FastAPI()

    @app.get("/")
    async def people() -> HTMLResponse:
        """List all existing people and provide a form for creating a new person."""
        return HTMLResponse(
            html.html_home("".join(html.html_person(m, i) for i, m in enumerate(models))),
        )

    @app.post("/")
    async def create_person(model: Annotated[Person, fastapi.Form()]) -> HTMLResponse:
        """Receive a new person request and store it."""
        models.append(model)
        return await people()

    @app.get("/{index}")
    async def person(index: int) -> HTMLResponse:
        """Show an edit form for an existing person."""
        try:
            model = models[index]
        except IndexError:
            return HTMLResponse(status_code=404, content="Not Found")
        return HTMLResponse(html.html_edit(model, index))

    @app.post("/{index}")
    async def update_person(index: int, model: Annotated[Person, fastapi.Form()]) -> HTMLResponse:
        """Receive an updated person request and update the existing entry."""
        try:
            models[index] = model
        except IndexError:
            return HTMLResponse(status_code=404, content="Not Found")
        return HTMLResponse(html.html_edit(model, index))

    # Mount static files if we've created the static directory
    static = Path(__file__).parent.parent / "static"
    if static.is_dir():
        app.mount("/static", StaticFiles(directory=static), name="static")

    return app


def main():
    # Create dummy data
    models.append(
        Person(
            name="John Doe",
            age=30,
            job="UX",
            address=Address(
                house_number=123,
                street="Main St",
                city="New York",
            ),
        )
    )
    models.append(
        Person(
            name="Jane Smith",
            age=25,
            job="Designer",
            address=Address(
                house_number=4,
                street="5th Ave",
                city="San Francisco",
            ),
        )
    )
    # Start the FastAPI app
    uvicorn.run(get_app(), log_level="info", use_colors=True)


if __name__ == "__main__":
    main()
