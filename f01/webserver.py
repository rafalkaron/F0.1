import uasyncio

HTML_PATH: str = "f01/motor_controls.html"
MAX_CLIENTS: int = 2

# Pre-encoded static responses for performance
RESPONSE_200_OK: str = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
RESPONSE_503: str = f"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nOnly {MAX_CLIENTS} controllers can be connected at the same time!."
RESPONSE_500: str = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nInternal Server Error"


class WebServer:
    """
    Simple async web server for Raspberry Pi Pico W.
    Serves a control page and handles /set? requests for motor control.
    """

    def __init__(self) -> None:
        self.server: object = None
        self.address: str = "0.0.0.0"
        self.port: int = 80
        self.last_left: int = 0
        self.last_right: int = 0
        self._html_cache: str = ""
        self._client_count: int = 0  # Track connected clients
        self._load_html()

    def _load_html(self) -> None:
        """
        Loads the HTML page from disk into cache.
        """
        try:
            with open(HTML_PATH, "r") as f:
                self._html_cache = f.read()
        except Exception as e:
            print(f"Error reading {HTML_PATH}: {e}")
            self._html_cache = """
<html><body><h1>Error loading page</h1></body></html>"""

    def web_page(self) -> str:
        """
        Returns the cached HTML page.
        """
        return self._html_cache

    def parse_query_params(self, query: str) -> dict[str, str]:
        """
        Parses a URL query string into a dictionary.
        """
        params: dict[str, str] = {}
        for pair in query.split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k] = v
        return params

    async def handle_client(self, reader: object, writer: object) -> None:
        """
        Handles an incoming HTTP client connection. Allows up to MAX_CLIENTS at the same time.
        No special stop logic: left=0 and right=0 means stop.
        """
        incremented: bool = False
        try:
            if self._client_count >= MAX_CLIENTS:
                await writer.awrite(RESPONSE_503)
                return
            self._client_count += 1
            incremented = True
            request_line = await reader.readline()
            if not request_line:
                return
            request: str = request_line.decode().strip()
            # Only read headers if not a /set? request
            is_set = request.startswith("GET /set?")
            if not is_set:
                while True:
                    header = await reader.readline()
                    if not header or header == b"\r\n":
                        break
            if is_set:
                query: str = request[9:].split(" ")[0]
                params: dict[str, str] = self.parse_query_params(query)
                left: str | None = params.get("left")
                right: str | None = params.get("right")
                if left is not None:
                    try:
                        self.last_left = int(left)
                    except Exception as e:
                        print(f"Invalid left value: {left} ({e})")
                if right is not None:
                    try:
                        self.last_right = int(right)
                    except Exception as e:
                        print(f"Invalid right value: {right} ({e})")
                await writer.awrite(RESPONSE_200_OK)
                return
            # Serve HTML page
            html: str = self.web_page()
            response: str = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
            await writer.awrite(response)
        except Exception as e:
            print(f"Error handling request: {e}")
            try:
                await writer.awrite(RESPONSE_500)
            except Exception as e2:
                print(f"Error sending 500 response: {e2}")
        finally:
            await writer.aclose()
            if incremented:
                self._client_count -= 1

    async def run(self) -> None:
        """
        Starts the async web server and waits for connections.
        """
        self.server = await uasyncio.start_server(
            self.handle_client, self.address, self.port
        )
        print(f"F0.1 control server listening on http://{self.address}:{self.port}")
        await self.server.wait_closed()
