Here is the detailed documentation for the **KatamariUI** FastAPI-based dynamic UI framework in markdown format for a GitHub README file. This documentation explains each class, function, and provides example usage.

---

# KatamariUI Documentation

**KatamariUI** is a dynamic UI framework built on top of **FastAPI** that supports real-time updates via WebSockets, webhooks, theming, pagination, authentication, and more. It allows developers to create responsive, interactive web applications with ease.

## Features

- **Dynamic UI Generation**: Add components like text, headers, buttons, forms, and tables dynamically.
- **WebSockets**: Real-time updates for all connected clients via WebSockets.
- **Webhooks**: Register and handle webhooks easily.
- **State Management**: Track and update form state across multiple submissions.
- **Theming**: Supports light and dark themes with custom CSS.
- **Notifications**: Broadcast notifications to all connected clients.
- **Pagination**: Create paginated tables for displaying large datasets.
- **Authentication**: Optional HTTP Basic authentication for secure access to routes.

---

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/yourusername/katamariui.git
cd katamariui
pip install -r requirements.txt
```

---

## Classes and Functions

### 1. **KatamariUI**

The **KatamariUI** class is the core of the framework. It manages components, state, WebSocket connections, webhooks, theming, and notifications.

#### **Class Definition**

```python
class KatamariUI:
    """
    Dynamic UI framework with support for theming, notifications, pagination, authentication, webhooks, and websockets.
    """
    def __init__(self, title="KatamariUI App", header="Welcome to KatamariUI"):
```

#### **Methods**

- **`connect_client(websocket)`**: Manages WebSocket connections.

    ```python
    async def connect_client(self, websocket: WebSocket):
        """
        Accept a WebSocket connection and add it to the list of clients.
        """
    ```

- **`disconnect_client(websocket)`**: Disconnects WebSocket clients.

    ```python
    async def disconnect_client(self, websocket: WebSocket):
        """
        Remove a WebSocket client from the list of connected clients.
        """
    ```

- **`send_update(message)`**: Sends real-time updates to WebSocket clients.

    ```python
    async def send_update(self, message: str):
        """
        Send a real-time update to all connected WebSocket clients.
        
        Args:
            message (str): The message to send to clients.
        """
    ```

- **`notify_all_clients()`**: Sends all notifications to connected WebSocket clients.

    ```python
    async def notify_all_clients(self):
        """
        Send all queued notifications to WebSocket clients.
        """
    ```

- **`add_webhook(route, handler)`**: Registers a new webhook.

    ```python
    def add_webhook(self, route: str, handler: Callable):
        """
        Register a new webhook route with its handler.
        
        Args:
            route (str): The route for the webhook.
            handler (Callable): The function that handles the webhook.
        """
    ```

- **`handle_webhook(route, request)`**: Handles incoming webhook requests.

    ```python
    async def handle_webhook(self, route: str, request: Request):
        """
        Invoke the appropriate webhook handler for the given route.
        
        Args:
            route (str): The route of the webhook.
            request (Request): The FastAPI request object.
        """
    ```

- **`text(label)`**: Adds a text component to the UI.

    ```python
    async def text(self, label: str):
        """
        Add a text component to the UI.
        
        Args:
            label (str): The text content to display.
        """
    ```

- **`input(label, input_name, value)`**: Adds an input field.

    ```python
    async def input(self, label: str, input_name: str, value: str = ""):
        """
        Add a text input field to the UI.
        
        Args:
            label (str): The label for the input field.
            input_name (str): The name for the input field.
            value (str): The default value for the input.
        """
    ```

- **`set_theme(theme)`**: Sets the UI theme (light or dark).

    ```python
    def set_theme(self, theme: str):
        """
        Set the theme of the UI (light or dark).
        
        Args:
            theme (str): The theme to apply (light or dark).
        """
    ```

- **`generate_template(data=None, show_sidebar=True)`**: Generates the full HTML template dynamically.

    ```python
    async def generate_template(self, data=None, show_sidebar=True):
        """
        Generate the full HTML template, including the navbar, sidebar, and main content.
        
        Args:
            data (str, optional): Additional data to display (e.g., form submission data).
            show_sidebar (bool): Whether to show the sidebar.
        """
    ```

#### **Example Usage**

```python
from KatamariUI import KatamariUI

ui = KatamariUI(title="My App", header="Welcome to My App")

# Add a text component
await ui.text("This is a dynamic UI component!")

# Add an input field
await ui.input("Enter your name", "name_input", value="")

# Generate the full HTML
html_content = await ui.generate_template()
print(html_content)
```

---

### 2. **katamari_ui_app**

This function creates a **FastAPI** app that integrates with **KatamariUI**. It supports dynamic UI rendering, WebSocket connections, webhooks, and form submissions.

#### **Function Definition**

```python
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
```

#### **Parameters**

- `ui_func`: The function that defines the UI components.
- `navbar_items`: A list of navigation items for the navbar.
- `sidebar_items`: A list of items for the sidebar.
- `custom_css`: Custom CSS for styling.
- `show_sidebar`: Whether to display the sidebar.
- `theme`: The theme to apply (light or dark).
- `requires_auth`: Whether the app requires authentication.
- `credentials_validator`: Function to validate user credentials (if authentication is enabled).

#### **Example Usage**

```python
from fastapi import FastAPI, HTTPBasicCredentials
from KatamariUI import katamari_ui_app

# Define a UI function
async def ui_func(ui):
    await ui.text("Welcome to the KatamariUI FastAPI App")
    await ui.input("Enter your name", "name_input")

# Navbar and Sidebar items
navbar_items = [{"label": "Home", "link": "/"}, {"label": "Contact", "link": "/contact"}]
sidebar_items = [{"label": "Dashboard", "link": "/dashboard"}, {"label": "Settings", "link": "/settings"}]

# Create the app
app = katamari_ui_app(
    ui_func=ui_func,
    navbar_items=navbar_items,
    sidebar_items=sidebar_items,
    custom_css=".custom-class { color: red; }",
    show_sidebar=True,
    theme="light"
)

# To run the FastAPI app, use the following command:
# uvicorn app:app --reload
```

---

### WebSockets and Real-Time Updates

The **KatamariUI** framework supports real-time updates via WebSockets. You can broadcast messages or notifications to all connected clients.

#### **WebSocket Endpoint Example**

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for real-time updates."""
    await ui.connect_client(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        await ui.disconnect_client(websocket)
```

---

### Authentication

**KatamariUI** supports optional HTTP Basic authentication. You can enable authentication by setting `requires_auth=True` and providing a `credentials_validator` function.

#### **Authentication Example**

```python
from fastapi import HTTPBasicCredentials

async def validate_credentials(credentials: HTTPBasicCredentials):
    if credentials.username == "admin" and credentials.password == "secret":
        return credentials.username
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Create the app with authentication enabled
app = katamari_ui_app(
    ui_func=ui_func,
    navbar_items=navbar_items,
    sidebar_items=sidebar_items,
    requires_auth=True,
    credentials_validator=validate_credentials
)
```

---

## Contributing

Contributions are welcome! Feel free to submit pull requests, open issues, or suggest new features.

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.

---

