from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List, Dict, Callable, Any
import json

class KatamariUI:
    """Enhanced UI framework with support for theming, notifications, pagination, authentication, webhooks, and WebSocket-driven real-time updates."""

    def __init__(self, title="KatamariUI App", header="Welcome to KatamariUI"):
        self.title = title
        self.header = header
        self.components = []  # Holds HTML components for the page
        self.state = {}  # Manages the state of form fields
        self.clients = []  # WebSocket clients
        self.navbar_items = []  # Stores navigation items for the navbar
        self.sidebar_items = []  # Stores sidebar items
        self.custom_css = ""  # Holds custom CSS
        self.theme = "light"  # Default theme (can be 'light' or 'dark')
        self.notifications = []  # Stores notifications to be sent to clients
        self.webhooks = {}  # Stores registered webhooks for handling

    # WebSocket Management
    async def connect_client(self, websocket: WebSocket):
        await websocket.accept()
        self.clients.append(websocket)

    async def disconnect_client(self, websocket: WebSocket):
        self.clients.remove(websocket)

    async def send_update(self, message: str):
        """Send real-time updates to WebSocket clients."""
        for client in self.clients:
            await client.send_text(message)

    async def notify_all_clients(self):
        """Send all notifications to WebSocket clients."""
        for client in self.clients:
            for notification in self.notifications:
                await client.send_text(notification)

    # Webhook Management
    def add_webhook(self, route: str, handler: Callable):
        """Register a new webhook route with a handler."""
        self.webhooks[route] = handler

    async def handle_webhook(self, route: str, request: Request):
        """Invoke the appropriate webhook handler for a given route."""
        if route in self.webhooks:
            handler = self.webhooks[route]
            data = await request.json()
            return await handler(data)
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Components API
    async def text(self, label: str):
        """Add a text component."""
        self.components.append(f"<p>{label}</p>")

    async def add_header(self, label: str, level: int = 1):
        """Add a header component."""
        self.components.append(f"<h{level}>{label}</h{level}>")

    async def input(self, label: str, input_name: str, value: str = ""):
        """Add a text input component."""
        current_value = self.state.get(input_name, value)
        self.components.append(f"""
            <label for="{input_name}">{label}</label>
            <input type="text" id="{input_name}" name="{input_name}" value="{current_value}" class="form-control mb-3"><br>
        """)

    async def textarea(self, label: str, input_name: str, value: str = ""):
        """Add a textarea component."""
        current_value = self.state.get(input_name, value)
        self.components.append(f"""
            <label for="{input_name}">{label}</label>
            <textarea name="{input_name}" class="form-control mb-3">{current_value}</textarea><br>
        """)

    async def button(self, label: str, button_name: str, value: str = ""):
        """Add a button component."""
        self.components.append(f"""
            <button type="submit" name="{button_name}" value="{value}" class="btn btn-primary">{label}</button>
        """)

    async def dropdown(self, label: str, input_name: str, options: List[str], selected: str = ""):
        """Add a dropdown component."""
        self.components.append(f"""
            <label for="{input_name}">{label}</label>
            <select name="{input_name}" id="{input_name}" class="form-select">
        """)
        for option in options:
            selected_attr = "selected" if option == selected else ""
            self.components.append(f"""
                <option value="{option}" {selected_attr}>{option}</option>
            """)
        self.components.append("</select><br>")

    async def file_upload(self, label: str, input_name: str):
        """Add a file upload component."""
        self.components.append(f"""
            <label for="{input_name}">{label}</label>
            <input type="file" name="{input_name}" class="form-control mb-3"><br>
        """)

    async def chart(self, chart_data: Dict[str, Any], chart_type: str = "bar"):
        """Render a Chart.js chart with dynamic data."""
        chart_data_json = json.dumps(chart_data)
        chart_id = f"chart-{len(self.components)}"
        chart_html = f"""
        <canvas id="{chart_id}" width="400" height="400"></canvas>
        <script>
            var ctx = document.getElementById('{chart_id}').getContext('2d');
            var chart = new Chart(ctx, {{
                type: '{chart_type}',
                data: {chart_data_json},
                options: {{
                    plugins: {{
                        legend: {{ labels: {{ color: 'white' if self.theme == 'dark' else 'black' }} }}
                    }},
                    scales: {{
                        x: {{ ticks: {{ color: 'white' if self.theme == 'dark' else 'black' }} }},
                        y: {{ ticks: {{ color: 'white' if self.theme == 'dark' else 'black' }} }}
                    }}
                }}
            }});
        </script>
        """
        self.components.append(chart_html)

    async def raw_html(self, html_content: str):
        """Add raw HTML directly to the page."""
        self.components.append(html_content)

    async def table(self, table_data: List[Dict[str, Any]]):
        """Render a table."""
        self.components.append("<table class='table table-bordered'>")
        if len(table_data) > 0:
            headers = table_data[0].keys()
            self.components.append("<thead><tr>")
            for header in headers:
                self.components.append(f"<th>{header}</th>")
            self.components.append("</tr></thead>")
        self.components.append("<tbody>")
        for row in table_data:
            self.components.append("<tr>")
            for value in row.values():
                self.components.append(f"<td>{value}</td>")
            self.components.append("</tr>")
        self.components.append("</tbody></table>")

    def set_theme(self, theme: str):
        """Set the UI theme (light or dark)."""
        self.theme = theme
        if theme == "dark":
            self.custom_css += """
            body {
                background-color: #121212;
                color: #ffffff;
            }
            .form-control, .form-select {
                background-color: #2c2c2c;
                color: #ffffff;
            }
            """
        elif theme == "light":
            self.custom_css += """
            body {
                background-color: #f8f9fa;
                color: #000000;
            }
            """

    def add_notification(self, message: str):
        """Add a notification to the queue to be sent to all clients."""
        self.notifications.append(message)

    async def send_notifications(self):
        """Send notifications to all connected clients via WebSockets."""
        await self.notify_all_clients()

    def configure_navbar(self, items: List[Dict[str, str]]):
        """Configure the navbar with a list of items."""
        self.navbar_items = items

    def configure_sidebar(self, items: List[Dict[str, str]]):
        """Configure the sidebar with a list of items."""
        self.sidebar_items = items

    def set_custom_css(self, css: str):
        """Apply custom CSS to the page."""
        self.custom_css = css

    def generate_navbar(self):
        navbar_html = '<nav class="navbar navbar-expand-lg navbar-light bg-light"><div class="container-fluid"><ul class="navbar-nav me-auto mb-2 mb-lg-0">'
        for item in self.navbar_items:
            navbar_html += f'<li class="nav-item"><a class="nav-link" href="{item["link"]}">{item["label"]}</a></li>'
        navbar_html += '</ul></div></nav>'
        return navbar_html

    def generate_sidebar(self):
        sidebar_html = '<div class="d-flex flex-column p-3 bg-light" style="width: 280px;"><ul class="nav nav-pills flex-column mb-auto">'
        for item in self.sidebar_items:
            sidebar_html += f'<li class="nav-item"><a class="nav-link" href="{item["link"]}">{item["label"]}</a></li>'
        sidebar_html += '</ul></div>'
        return sidebar_html

    async def generate_template(self, data=None, show_sidebar=True):
        """Dynamically generate the full HTML template, including navbar, sidebar, and content."""
        html_content = "\n".join(self.components)
        navbar = self.generate_navbar()
        sidebar = self.generate_sidebar() if show_sidebar else ""

        full_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{self.title}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0-alpha1/dist/css/bootstrap.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                {self.custom_css}
            </style>
        </head>
        <body class="{self.theme}">
            {navbar}
            <div class="container-fluid">
                <div class="row">
                    <div class="col-3">
                        {sidebar}
                    </div>
                    <div class="col">
                        <h1>{self.header}</h1>
                        <form method="post" enctype="multipart/form-data">
                            {html_content}
                        </form>
                        {"<p class='mt-3'>" + data + "</p>" if data else ""}
                    </div>
                </div>
            </div>
            <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        </body>
        </html>
        """
        return full_template

    async def update_state(self, form_data: dict):
        """Update the state with form data."""
        self.state.update(form_data)


# FastAPI setup for routing and rendering
def katamari_ui_app(
        ui_func: Callable,
        navbar_items: List[Dict[str, str]],
        sidebar_items: List[Dict[str, str]],
        custom_css: str = "",
        show_sidebar: bool = True,
        theme: str = "light",
        requires_auth: bool = False,
        credentials_validator: Callable = None
    ):
    """Create the KatamariUI FastAPI app with navbar, sidebar, pagination, webhooks, websockets, and authentication."""
    app = FastAPI()
    security = HTTPBasic()

    ui_instance = KatamariUI()
    ui_instance.configure_navbar(navbar_items)
    ui_instance.configure_sidebar(sidebar_items)
    ui_instance.set_custom_css(custom_css)
    ui_instance.set_theme(theme)

    async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
        if requires_auth and credentials_validator:
            return await credentials_validator(credentials)
        return None

    @app.get("/", response_class=Response)
    async def render_get(request: Request, page: int = 1, user: str = Depends(get_current_user)):
        ui_instance.components = []  # Reset components for each render
        await ui_func(ui_instance)  # Build the UI dynamically
        return Response(content=await ui_instance.generate_template(show_sidebar=show_sidebar), media_type="text/html")

    @app.post("/", response_class=Response)
    async def handle_form_post(request: Request, user: str = Depends(get_current_user)):
        form_data = await request.form()
        await ui_instance.update_state(form_data)
        ui_instance.components = []  # Reset components for each render
        await ui_func(ui_instance)  # Build the UI dynamically after submission
        return Response(content=await ui_instance.generate_template(data=str(form_data), show_sidebar=show_sidebar), media_type="text/html")

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """Handle WebSocket connections for real-time updates."""
        await ui_instance.connect_client(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await ui_instance.send_update(f"Message received: {data}")
        except WebSocketDisconnect:
            await ui_instance.disconnect_client(websocket)

    @app.post("/webhook/{route}")
    async def handle_webhook_route(route: str, request: Request):
        """Handle incoming webhook requests."""
        return await ui_instance.handle_webhook(route, request)

    return app
