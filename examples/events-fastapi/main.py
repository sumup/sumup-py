# /// script
# requires-python = ">=3.10"
# dependencies = ["fastapi", "uvicorn"]
# ///
"""Run with: uv run --with-editable . examples/events-fastapi/main.py"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response

from sumup import AsyncSumup
from sumup.events import (
    SIGNATURE_HEADER,
    EventCallbackError,
    EventNotification,
    EventPayloadError,
    EventSignatureError,
    ReaderCreatedEvent,
)

logger = logging.getLogger(__name__)
client = AsyncSumup(api_key=os.environ["SUMUP_API_KEY"])


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await client._client.aclose()


app = FastAPI(lifespan=lifespan)


async def fallback(event: EventNotification) -> None:
    print(f"Received {event.type}")


events = client.events_handler(os.environ["SUMUP_EVENT_SECRET"], fallback)


@events.on_reader_created
async def reader_created(event: ReaderCreatedEvent) -> None:
    reader = await event.fetch_object_async()
    print(f"Reader paired: {reader.id} ({reader.name})")


@app.post("/events")
async def receive_event(request: Request) -> Response:
    try:
        await events.handle(await request.body(), request.headers.get(SIGNATURE_HEADER))
    except (EventSignatureError, EventPayloadError):
        return Response("Invalid event", status_code=400)
    except EventCallbackError:
        logger.exception("Event processing failed")
        return Response("Event processing failed", status_code=500)
    return Response(status_code=204)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080)
