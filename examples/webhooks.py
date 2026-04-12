"""Minimal HTTP server example for receiving and verifying SumUp webhooks."""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import pydantic

from sumup import Sumup
from sumup.webhooks import (
    CheckoutCreatedEvent,
    WebhookSignatureError,
    WebhookSignatureExpiredError,
    WebhookTimestampError,
)


client = Sumup(api_key=os.environ["SUMUP_API_KEY"])
webhooks = client.webhook_handler(
    secret=os.environ["SUMUP_WEBHOOK_SECRET"],
)


class WebhookRequestHandler(BaseHTTPRequestHandler):
    """Handle incoming webhook POST requests."""

    def do_POST(self) -> None:
        if self.path != "/webhooks":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length)

        try:
            event = webhooks.parse_and_verify(dict(self.headers.items()), body)
        except (WebhookSignatureError, WebhookSignatureExpiredError, WebhookTimestampError):
            self.send_error(400, "Invalid webhook signature")
            return
        except pydantic.ValidationError:
            self.send_error(400, "Invalid webhook payload")
            return

        print(
            "Webhook received:",
            {
                "id": event.id,
                "type": event.type,
                "object_id": event.object.id,
            },
        )

        if isinstance(event, CheckoutCreatedEvent):
            checkout = event.fetch_object()
            print(f"Checkout status: {checkout.status}")

        self.send_response(204)
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8080), WebhookRequestHandler)
    print("Listening on http://127.0.0.1:8080/webhooks")
    server.serve_forever()
