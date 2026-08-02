"""Minimal HTTP server for verified, typed SumUp event notifications."""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import pydantic

from sumup import Sumup
from sumup.events import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    EventNotification,
    EventSignatureError,
    EventTimestampError,
    ReaderCreatedEvent,
)


client = Sumup(api_key=os.environ["SUMUP_API_KEY"])


def handle_unhandled_event(event: EventNotification, _client: Sumup) -> None:
    print(f"Received unhandled event type: {event.type}")


def handle_reader_created(event: ReaderCreatedEvent, _client: Sumup) -> None:
    reader = event.fetch_object()
    print(f"Reader paired: {reader.id} ({reader.name})")


events = client.events_handler(
    os.environ["SUMUP_EVENT_SECRET"],
    handle_unhandled_event,
)
events.on(ReaderCreatedEvent, handle_reader_created)


class EventRequestHandler(BaseHTTPRequestHandler):
    """Handle incoming event notification requests."""

    def do_POST(self) -> None:
        if self.path != "/events":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)
        signature = self.headers.get(SIGNATURE_HEADER, "")
        timestamp = self.headers.get(TIMESTAMP_HEADER, "")

        try:
            events.handle(body, signature, timestamp)
        except (EventSignatureError, EventTimestampError):
            self.send_error(400, "Invalid event signature")
            return
        except pydantic.ValidationError:
            self.send_error(400, "Invalid event payload")
            return
        except Exception as error:
            print(f"Event callback failed: {error}")
            self.send_error(500, "Event callback failed")
            return

        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8080), EventRequestHandler)
    print("Listening on http://127.0.0.1:8080/events")
    server.serve_forever()
