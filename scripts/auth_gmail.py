import base64
import json
import os
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

AUTH_ENDPOINT = base64.b64decode(
    "aHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL3YyL2F1dGg="
).decode("utf-8")
TOKEN_ENDPOINT = base64.b64decode(
    "aHR0cHM6Ly9vYXV0aDIuZ29vZ2xlYXBpcy5jb20vdG9rZW4="
).decode("utf-8")
SCOPE = base64.b64decode(
    "aHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vYXV0aC9nbWFpbC5tb2RpZnk="
).decode("utf-8")

CLIENT_ID = os.environ["GOOGLE_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8080"
auth_code: str | None = None


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Success! Return to VS Code now.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed.")

    def log_message(self, format, *args):
        pass


def main():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(params)}"
    print("Opening browser automatically...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8080), OAuthCallbackHandler)
    while auth_code is None:
        server.handle_request()

    token_data = urllib.parse.urlencode(
        {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")

    req = urllib.request.Request(TOKEN_ENDPOINT, data=token_data, method="POST")
    with urllib.request.urlopen(req) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))

    refresh_token = tokens["refresh_token"]
    env_text = ENV_PATH.read_text(encoding="utf-8")
    updated = [
        f'GOOGLE_REFRESH_TOKEN="{refresh_token}"' if line.startswith("GOOGLE_REFRESH_TOKEN=") else line
        for line in env_text.splitlines()
    ]
    ENV_PATH.write_text("\n".join(updated) + "\n", encoding="utf-8")
    print("SUCCESS! Saved GOOGLE_REFRESH_TOKEN into .env!")


if __name__ == "__main__":
    main()
