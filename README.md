# AI Assistant

A production-ready Flask web application for prompt-engineering experiments powered by Google Gemini. It provides four AI functions, each with three prompt variants: question answering, text summarization, creative content generation, and practical advice.

## Features

- Four core AI functions with 3 prompt variants each.
- Gemini 3.8 Flash backend using the official Google Gen AI Python SDK.
- Input validation and maximum request size protection.
- Friendly handling for missing API keys, quota/rate limits, authentication errors, timeouts, connection failures, and upstream API errors.
- Responsive browser interface with accessible labels, keyboard focus states, loading/status messages, and mobile layout.
- Feedback buttons and a deployment-safe stateless feedback endpoint. The app intentionally does not write feedback to the local filesystem because Render service filesystems are not a durable application database.
- `/health` endpoint for deployment checks.

## Project structure

```text
.
├── app.py
├── requirements.txt
├── render.yaml
├── .env.example
├── .gitignore
├── templates/
│   └── index.html
├── static/
│   ├── script.js
│   └── style.css
└── tests/
    └── test_app.py
```

## Environment variables

Set these on the server or in a local environment. Never commit `.env` or an API key.

```text
GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.8-flash
MAX_INPUT_LENGTH=12000
```

`GEMINI_API_KEY` is the only secret required by the application.

## Local setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
```

Then configure `GEMINI_API_KEY` in your environment and run:

```bash
python app.py
```

Open `http://127.0.0.1:5000`.

The application also starts without an API key; AI requests return a clear `503` configuration error instead of crashing.

## Tests

Run the full mocked regression suite with:

```bash
pytest -q
```

The tests cover startup, homepage, health, all prompt variants, validation, malformed JSON, large inputs, missing API key behavior, Gemini quota/rate-limit handling, feedback validation, feedback handling, stats, and API 404 behavior. The Gemini service is mocked; no real API credits are required.

## Deployment on Render

This repository includes `render.yaml` for a Python web service. Render uses:

```text
Build: pip install -r requirements.txt
Start: gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 90
```

Set `GEMINI_API_KEY` as a Render environment variable and keep it server-side. Set `GEMINI_MODEL` to `gemini-3.8-flash` unless you intentionally choose another compatible Gemini model.

The `/health` endpoint reports whether the Gemini key is configured and is suitable for a basic service health check.

## Production considerations

The application disables Flask debug mode in production. Upstream exception details are not returned to users. User input is bounded, malformed API requests are rejected, and frontend code avoids rendering raw JavaScript/network exceptions.

Feedback is deliberately stateless in this lightweight deployment. To retain feedback across deployments or instances, connect `/api/feedback` to a managed database such as Render Postgres rather than relying on a local JSON file.
