# Events with Flask

Verify incoming events and fetch a newly paired reader using synchronous callbacks.

From the repository root:

```sh
export SUMUP_API_KEY="your-api-key"
export SUMUP_EVENT_SECRET="your-event-signing-secret"
uv run --with-editable . examples/events-flask/main.py
```

Forward signed event deliveries to `POST http://localhost:8080/events`.
The signing secret must match the sender; it is separate from your API key.

The handler receives the raw body and complete signature header. It returns `204`
after processing, `400` for invalid deliveries, and `500` for callback failures.
Make callback side effects idempotent because deliveries can be retried.
Flask limits request bodies to 1 MiB in this example.
