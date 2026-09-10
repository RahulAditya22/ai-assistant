import pytest

from app import MAX_INPUT_LENGTH, PROMPT_LIBRARY, create_app


class FakeMessage:
    content = "Mocked AI response"


class FakeChoice:
    message = FakeMessage()


class FakeResponse:
    choices = [FakeChoice()]


class FakeCompletions:
    def create(self, **kwargs):
        return FakeResponse()


class FakeClient:
    class chat:
        completions = FakeCompletions()


@pytest.fixture()
def app(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr("app.OpenAI", lambda api_key: FakeClient())
    application = create_app()
    application.config.update(TESTING=True)
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"AI Assistant" in response.data


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


@pytest.mark.parametrize("function, prompt_id", [
    (function, prompt["id"])
    for function, prompts in PROMPT_LIBRARY.items()
    for prompt in prompts
])
def test_each_prompt_variant(client, function, prompt_id):
    response = client.post("/api/run", json={
        "function": function,
        "prompt_id": prompt_id,
        "input": "Representative test input",
    })
    assert response.status_code == 200
    body = response.get_json()
    assert body["result"] == "Mocked AI response"
    assert body["function"] == function
    assert body["prompt_id"] == prompt_id


@pytest.mark.parametrize("payload", [
    {},
    {"function": "bad", "prompt_id": "x", "input": "text"},
    {"function": "answer", "prompt_id": "bad", "input": "text"},
    {"function": "answer", "prompt_id": "concise", "input": "   "},
    {"function": "answer", "prompt_id": "concise", "input": 123},
])
def test_invalid_run_requests(client, payload):
    response = client.post("/api/run", json=payload)
    assert response.status_code in {400, 413}
    assert "error" in response.get_json()


def test_malformed_json(client):
    response = client.post("/api/run", data="{bad json", content_type="application/json")
    assert response.status_code == 400
    assert response.get_json()["error"]


def test_large_input_rejected(client):
    payload = {
        "function": "answer",
        "prompt_id": "concise",
        "input": "x" * (MAX_INPUT_LENGTH + 1),
    }
    response = client.post("/api/run", json=payload)
    assert response.status_code == 413


def test_missing_key_is_clean(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    application = create_app()
    application.config.update(TESTING=True)
    response = application.test_client().post("/api/run", json={
        "function": "answer",
        "prompt_id": "concise",
        "input": "Hello",
    })
    assert response.status_code == 503
    assert response.get_json()["error"] == "AI service is not configured yet. Add OPENAI_API_KEY to the server environment."


def test_feedback_valid(client):
    response = client.post("/api/feedback", json={
        "function": "answer",
        "prompt_used": "Concise factual answer",
        "input": "Hello",
        "output": "World",
        "helpful": True,
    })
    assert response.status_code == 202
    assert response.get_json()["status"] == "accepted"


@pytest.mark.parametrize("payload", [
    {},
    {"function": "answer", "input": "x", "output": "y"},
    {"function": "bad", "input": "x", "output": "y", "helpful": True},
    {"function": "answer", "input": "x", "output": "y", "helpful": "yes"},
])
def test_invalid_feedback(client, payload):
    response = client.post("/api/feedback", json=payload)
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_feedback_stats_is_deterministic(client):
    response = client.get("/api/feedback/stats")
    assert response.status_code == 200
    assert response.get_json() == {
        "total": 0,
        "helpful": 0,
        "not_helpful": 0,
        "persistence": "stateless",
    }


def test_api_404_is_json(client):
    response = client.get("/api/not-found")
    assert response.status_code == 404
    assert response.get_json()["error"] == "Endpoint not found."
