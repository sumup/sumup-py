"""OAuth 2.0 Authorization Code flow with SumUp.

This example uses Authlib to handle the OAuth2 Authorization Code flow with
PKCE and then uses the resulting access token with the SumUp SDK.

Run:
    CLIENT_ID=... CLIENT_SECRET=... REDIRECT_URI=http://localhost:8080/callback \
        python examples/oauth2.py
"""

from __future__ import annotations

from sumup import Sumup

import http.server
import json
import os
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

from authlib.integrations.httpx_client import OAuth2Client

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AUTHORIZATION_ENDPOINT = "https://api.sumup.com/authorize"
TOKEN_ENDPOINT = "https://api.sumup.com/token"
SCOPES = "email profile"


def build_redirect_uri() -> str:
    return os.getenv("REDIRECT_URI", "http://localhost:8080/callback")


def build_server_address(redirect_uri: str) -> tuple[str, int]:
    parsed = urllib.parse.urlparse(redirect_uri)
    host = parsed.hostname or "localhost"
    port = parsed.port or 8080
    return host, port


def build_callback_path(redirect_uri: str) -> str:
    parsed = urllib.parse.urlparse(redirect_uri)
    return parsed.path or "/callback"


class OAuth2Server(http.server.ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[http.server.BaseHTTPRequestHandler],
        *,
        oauth_client: OAuth2Client,
        callback_path: str,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.oauth_client = oauth_client
        self.callback_path = callback_path
        self.state: str | None = None
        self.code_verifier: str | None = None
        self.done = threading.Event()


class OAuth2Handler(http.server.BaseHTTPRequestHandler):
    server: OAuth2Server

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<h1>SumUp OAuth2 Example</h1>"
                b"<p>This example uses Authlib for the OAuth2 Authorization Code flow with PKCE.</p>"
                b'<p><a href="/login">Start OAuth2 Flow</a></p>'
            )
            return

        if parsed.path == "/login":
            self.handle_login()
            return

        if parsed.path == self.server.callback_path:
            self.handle_callback()
            return

        self.send_error(404, "Not Found")

    def handle_login(self) -> None:
        authorization_url, state = self.server.oauth_client.create_authorization_url(
            AUTHORIZATION_ENDPOINT,
            scope=SCOPES,
        )
        code_verifier = getattr(self.server.oauth_client, "code_verifier", None)
        if not isinstance(code_verifier, str) or not code_verifier:
            self.respond_with_error(500, "OAuth client did not generate a PKCE code verifier")
            self.server.done.set()
            return

        self.server.state = state
        self.server.code_verifier = code_verifier

        self.send_response(302)
        self.send_header("Location", authorization_url)
        self.end_headers()

    def handle_callback(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        state = params.get("state", [""])[0]
        merchant_code = params.get("merchant_code", [""])[0]
        error = params.get("error", [""])[0]
        error_description = params.get("error_description", [""])[0]

        if error:
            self.respond_with_error(400, f"OAuth error: {error_description or error}")
            self.server.done.set()
            return

        if not self.server.state or state != self.server.state:
            self.respond_with_error(400, "Invalid OAuth state parameter")
            self.server.done.set()
            return

        if not merchant_code:
            self.respond_with_error(
                400,
                "Missing merchant_code query parameter in callback response",
            )
            self.server.done.set()
            return

        try:
            token = self.server.oauth_client.fetch_token(
                TOKEN_ENDPOINT,
                authorization_response=self.request_url(),
                code_verifier=self.server.code_verifier,
            )
            access_token = token["access_token"]
            client = Sumup(api_key=access_token)
            merchant = client.merchants.get(merchant_code)
        except Exception as exc:  # noqa: BLE001
            self.respond_with_error(500, f"OAuth callback failed: {exc}")
            self.server.done.set()
            return

        merchant_payload = merchant.model_dump() if hasattr(merchant, "model_dump") else merchant

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            json.dumps(
                {
                    "merchant_code": merchant_code,
                    "merchant": merchant_payload,
                },
                indent=2,
                default=str,
            ).encode("utf-8")
        )

        print(f"Merchant code: {merchant_code}")
        print(json.dumps(merchant_payload, indent=2, default=str))
        self.server.done.set()

    def request_url(self) -> str:
        host = self.headers.get("Host", "localhost:8080")
        return f"http://{host}{self.path}"

    def respond_with_error(self, status: int, message: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(message.encode("utf-8"))

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def main() -> None:
    client_id = os.environ.get("CLIENT_ID")
    client_secret = os.environ.get("CLIENT_SECRET")
    redirect_uri = build_redirect_uri()

    if not client_id or not client_secret:
        raise SystemExit("Please set CLIENT_ID and CLIENT_SECRET environment variables.")

    oauth_client = OAuth2Client(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        code_challenge_method="S256",
    )

    server_address = build_server_address(redirect_uri)
    callback_path = build_callback_path(redirect_uri)

    server = OAuth2Server(
        server_address,
        OAuth2Handler,
        oauth_client=oauth_client,
        callback_path=callback_path,
    )

    print(f"Server is running at http://{server_address[0]}:{server_address[1]}")
    print("Open /login to start the OAuth2 flow.")

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    login_url = f"http://{server_address[0]}:{server_address[1]}/login"
    webbrowser.open(login_url)

    try:
        server.done.wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        oauth_client.close()


if __name__ == "__main__":
    main()
