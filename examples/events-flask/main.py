# /// script
# requires-python = ">=3.10"
# dependencies = ["flask"]
# ///
"""Run with: uv run --with-editable . examples/events-flask/main.py"""

import os

from flask import Flask, request

from sumup import Sumup
from sumup.events import (
    SIGNATURE_HEADER,
    EventCallbackError,
    EventNotification,
    EventPayloadError,
    EventSignatureError,
    ReaderCreatedEvent,
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
client = Sumup(api_key=os.environ["SUMUP_API_KEY"])


def fallback(event: EventNotification) -> None:
    print(f"Received {event.type}")


events = client.events_handler(os.environ["SUMUP_EVENT_SECRET"], fallback)


@events.on_reader_created
def reader_created(event: ReaderCreatedEvent) -> None:
    reader = event.fetch_object()
    print(f"Reader paired: {reader.id} ({reader.name})")


@app.post("/events")
def receive_event():
    try:
        events.handle(request.get_data(), request.headers.get(SIGNATURE_HEADER))
    except (EventSignatureError, EventPayloadError):
        return "Invalid event", 400
    except EventCallbackError:
        app.logger.exception("Event processing failed")
        return "Event processing failed", 500
    return "", 204


if __name__ == "__main__":
    try:
        app.run(port=8080)
    finally:
        client._client.close()
