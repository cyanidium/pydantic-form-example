import unittest
from multiprocessing import Process
from pathlib import Path

import httpx
import uvicorn
from djlint.lint import linter
from djlint.settings import Config
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright, expect

import app
import html
import model


class TestModel(unittest.TestCase):
    def test_person_model(self):
        person = model.Person(name="John Doe", age=30, job="Developer")
        self.assertEqual(person.name, "John Doe")
        self.assertEqual(person.age, 30)
        self.assertEqual(person.job, "Developer")
        data = person.model_dump_json()
        self.assertEqual(person, model.Person.model_validate_json(data))


class TestHTML(unittest.TestCase):
    def setUp(self) -> None:
        self.config = Config()

    def test_home(self):
        html_str = html.html_home("")
        errors = linter(config=self.config, html=html_str, filename="home.html", filepath="home.html")
        self.assertEqual(len(errors["home.html"]), 0)

    def test_edit(self):
        html_str = html.html_edit(model.Person(name="John Doe", age=30, job="Developer"), 0)
        errors = linter(config=self.config, html=html_str, filename="edit.html", filepath="edit.html")
        self.assertEqual(len(errors["edit.html"]), 0)


class TestApp(unittest.TestCase):
    def setUp(self) -> None:
        self.app = app.get_app()
        self.client = TestClient(self.app)
        app.models = []

    def test_home_page_empty(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("People", response.text)
        self.assertIn("New", response.text)

    def test_home_page_dummy(self):
        app.models = [
            model.Person(name="John Doe", age=30, job="Developer"),
            model.Person(name="Jane Smith", age=25, job="UX Designer"),
        ]
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("People", response.text)
        self.assertIn("John Doe", response.text)
        self.assertIn("Jane Smith", response.text)
        self.assertIn("New", response.text)

    def test_create_endpoint(self):
        response = self.client.post("/", data={"name": "John Doe", "age": 30, "job": "Developer"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("John Doe", response.text)
        self.assertEqual(len(app.models), 1)
        response = self.client.post("/", data={"name": "Jane Smith", "age": 25, "job": "UX Designer"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Jane Smith", response.text)
        self.assertEqual(len(app.models), 2)

    def test_get_page(self):
        app.models = [
            model.Person(name="John Doe", age=30, job="Developer"),
            model.Person(name="Jane Smith", age=25, job="UX Designer"),
        ]
        response = self.client.get("/0")
        self.assertEqual(response.status_code, 200)
        self.assertIn("John Doe", response.text)
        response = self.client.get("/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Jane Smith", response.text)
        response = self.client.get("/2")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Not Found", response.text)

    def test_edit_page(self):
        app.models = [
            model.Person(name="John Doe", age=30, job="Developer"),
            model.Person(name="Jane Smith", age=25, job="UX Designer"),
        ]
        response = self.client.post("/0", data={"name": "John Smith", "age": 31, "job": "Programmer"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("John Smith", response.text)
        response = self.client.post("/1", data={"name": "Jane Doe", "age": 26, "job": "UI Designer"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Jane Doe", response.text)
        self.assertEqual(
            app.models,
            [
                model.Person(name="John Smith", age=31, job="Programmer"),
                model.Person(name="Jane Doe", age=26, job="UI Designer"),
            ],
        )


class TestInteraction(unittest.TestCase):
    @staticmethod
    def run_server():
        uvicorn.run(app.get_app(), log_level="info")

    def setUp(self) -> None:
        (Path(__file__).parent / "results").mkdir(exist_ok=True)
        self.proc = Process(target=self.run_server, args=(), daemon=True)
        self.proc.start()
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch()
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.set_viewport_size({"width": 500, "height": 500})

    def tearDown(self) -> None:
        self.browser.close()
        self.playwright.stop()
        self.proc.kill()

    def load_dummy_data(self):
        """Add some data for working with"""
        with httpx.Client(base_url="http://127.0.0.1:8000") as client:
            response = client.post(
                url="/",
                data={"name": "John Doe", "age": 30, "job": "Developer"},
            )
            self.assertEqual(response.status_code, 200)
            response = client.post(
                url="/",
                data={"name": "Jane Smith", "age": 25, "job": "UX Designer"},
            )
            self.assertEqual(response.status_code, 200)

    def test_home_page(self):
        self.page.goto("http://127.0.0.1:8000/")
        self.page.screenshot(full_page=True, path=Path(__file__).parent / "results" / "home_empty.png")
        expect(self.page.get_by_role("textbox", name="Name")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Age")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Job")).to_be_visible()
        expect(self.page.get_by_role("button", name="Create")).to_be_visible()
        self.load_dummy_data()
        self.page.reload()
        expect(self.page.get_by_role("link", name="John Doe")).to_be_visible()
        expect(self.page.get_by_role("link", name="Jane Smith")).to_be_visible()
        self.page.screenshot(full_page=True, path=Path(__file__).parent / "results" / "home_dummy.png")

    def test_get_page(self):
        self.load_dummy_data()
        self.page.goto("http://127.0.0.1:8000/0")
        expect(self.page.get_by_role("textbox", name="Name")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Name")).to_have_value("John Doe")
        expect(self.page.get_by_role("textbox", name="Age")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Age")).to_have_value("30")
        expect(self.page.get_by_role("textbox", name="Job")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Job")).to_have_value("Developer")
        expect(self.page.get_by_role("button", name="Update")).to_be_visible()
        self.page.screenshot(full_page=True, path=Path(__file__).parent / "results" / "get_0.png")
        self.page.goto("http://127.0.0.1:8000/1")
        expect(self.page.get_by_role("textbox", name="Name")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Name")).to_have_value("Jane Smith")
        expect(self.page.get_by_role("textbox", name="Age")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Age")).to_have_value("25")
        expect(self.page.get_by_role("textbox", name="Job")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Job")).to_have_value("UX Designer")
        expect(self.page.get_by_role("button", name="Update")).to_be_visible()
        self.page.screenshot(full_page=True, path=Path(__file__).parent / "results" / "get_1.png")

    def test_new_fails(self):
        self.page.goto("http://127.0.0.1:8000/")
        self.page.get_by_role("textbox", name="Name").fill("Foo Bar")
        self.page.get_by_role("textbox", name="Age").fill("21")
        self.page.get_by_role("textbox", name="Job").fill("Sales")
        self.page.get_by_role("button", name="Create").click()
        self.assertIn('"type":"missing"', self.page.content())
        self.assertIn("root[name]", self.page.content())
        self.assertIn("root[age]", self.page.content())
        self.assertIn("root[job]", self.page.content())
        self.page.screenshot(full_page=True, path=Path(__file__).parent / "results" / "new_fails.png")
        self.page.goto("http://127.0.0.1:8000/")
        expect(self.page.get_by_role("link", name="Foo Bar")).not_to_be_visible()

    def test_edit_fails(self):
        self.load_dummy_data()
        self.page.goto("http://127.0.0.1:8000/0")
        expect(self.page.get_by_role("textbox", name="Name")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Name")).to_have_value("John Doe")
        self.page.get_by_role("textbox", name="Name").fill("Foo Bar")
        expect(self.page.get_by_role("textbox", name="Age")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Age")).to_have_value("30")
        self.page.get_by_role("textbox", name="Age").fill("21")
        expect(self.page.get_by_role("textbox", name="Job")).to_be_visible()
        expect(self.page.get_by_role("textbox", name="Job")).to_have_value("Developer")
        self.page.get_by_role("textbox", name="Job").fill("Sales")
        expect(self.page.get_by_role("button", name="Update")).to_be_visible()
        self.page.get_by_role("button", name="Update").click()
        self.assertIn('"type":"missing"', self.page.content())
        self.assertIn("root[name]", self.page.content())
        self.assertIn("root[age]", self.page.content())
        self.assertIn("root[job]", self.page.content())
        self.page.screenshot(full_page=True, path=Path(__file__).parent / "results" / "edit_fails.png")
        self.page.goto("http://127.0.0.1:8000/")
        expect(self.page.get_by_role("link", name="Foo Bar")).not_to_be_visible()


if __name__ == "__main__":
    unittest.main()
