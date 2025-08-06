import uasyncio

HTML_PATH = "f01/motor_controls.html"
MAX_CLIENTS = 2

class WebServer:
    """
    Simple async web server for Raspberry Pi Pico W.
    Serves a control page and handles /set? requests for motor control.
    """
    def __init__(self) -> None:
        self.server = None
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
        Handles an incoming HTTP client connection. Allows up to MAX_CLIENTS at a time.
        """
        if self._client_count >= MAX_CLIENTS:
            response = (
                f"HTTP/1.1 503 Service Unavailable\r\nContent-Type: text/plain\r\n\r\nOnly {MAX_CLIENTS} controllers can be connected at the same time!."
            )
            await writer.awrite(response)
            await writer.aclose()
            return
        self._client_count += 1
        try:
            request_line = await reader.readline()
            if not request_line:
                await writer.aclose()
                return
            request = request_line.decode().strip()
            # Read and discard headers quickly
            while True:
                header = await reader.readline()
                if not header or header == b"\r\n":
                    break
            # Fast path for /set? requests
            if request.startswith("GET /set?"):
                # Remove rate limiting: always process the latest value
                query = request[9:].split(" ")[0]
                params = self.parse_query_params(query)
                stop = params.get("stop")
                left = params.get("left")
                right = params.get("right")
                if stop == "1":
                    self.last_left = 0
                    self.last_right = 0
                else:
                    if left is not None:
                        try:
                            self.last_left = int(left)
                        except Exception:
                            pass
                    if right is not None:
                        try:
                            self.last_right = int(right)
                        except Exception:
                            pass
                response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nOK"
                await writer.awrite(response)
                await writer.aclose()
                return
            # Serve HTML page
            html = self.web_page()
            response = (
                "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
            )
            await writer.awrite(response)
        except Exception as e:
            print(f"Error handling request: {e}")
        finally:
            await writer.aclose()
            self._client_count -= 1

    async def run(self) -> None:
        """
        Starts the async web server and waits for connections.
        """
        self.server = await uasyncio.start_server(self.handle_client, self.address, self.port)
        print(f"F0.1 control server listening on http://{self.address}:{self.port}")
        await self.server.wait_closed()
