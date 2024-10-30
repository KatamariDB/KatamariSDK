Here's the updated documentation, integrating **KatamariCharts** with **KatamariUI** in the example. This showcases how **KatamariCharts** can be used within the **KatamariUI** framework to render charts on a dynamic UI page.

---

# KatamariCharts and KatamariUI Integration Documentation

**KatamariCharts** is a chart rendering utility for both **Chart.js** and **Matplotlib** charts. It integrates seamlessly with **KatamariUI**, a dynamic UI framework for creating real-time, interactive web applications with support for charts, theming, and components.

## Features

- **Chart.js**: Interactive, JavaScript-based charts (e.g., bar, line, pie).
- **Matplotlib**: Python-based charts rendered as base64-encoded images for static embedding.
- **Integration with KatamariUI**: Easily embed charts in dynamic user interfaces.

---

## Installation

Make sure to install **Matplotlib**:

```bash
pip install matplotlib
```

No installation is required for **Chart.js** as it's loaded via a CDN in the HTML template.

---

## Classes and Functions

### 1. **KatamariCharts**

The **KatamariCharts** class is responsible for rendering charts using **Chart.js** or **Matplotlib** and storing them as HTML components for embedding into a webpage.

#### **Class Definition**

```python
class KatamariCharts:
    """
    Handles chart rendering using Chart.js and Matplotlib.
    """
    def __init__(self):
        self.components = []  # Holds chart components to be embedded in the page
```

#### **Methods**

- **`render_chartjs(chart_data: Dict[str, Any], chart_type: str = "bar")`**: Renders a Chart.js chart using the provided data and type.

    ```python
    def render_chartjs(self, chart_data: Dict[str, Any], chart_type: str = "bar"):
        """
        Render a Chart.js chart using provided data and type.
        
        Args:
            chart_data (dict): Data and labels for Chart.js.
            chart_type (str): Type of chart (bar, line, pie, etc.).
        """
    ```

- **`render_matplotlib(plot_func: Callable)`**: Renders a Matplotlib chart as a base64-encoded image.

    ```python
    def render_matplotlib(self, plot_func: Callable):
        """
        Render a Matplotlib chart as a base64-encoded image.
        
        Args:
            plot_func (Callable): Function that generates a Matplotlib chart.
        """
    ```

- **`get_components()`**: Returns all rendered chart components.

    ```python
    def get_components(self):
        """
        Return all rendered chart components as HTML.
        
        Returns:
            list: List of HTML components for charts.
        """
    ```

---

### 2. **KatamariUI**

**KatamariUI** is a dynamic UI framework that allows embedding charts, rendering components, and managing state. It integrates with **KatamariCharts** to render interactive **Chart.js** charts and static **Matplotlib** charts.

#### **Class Definition**

```python
class KatamariUI:
    """
    Dynamic UI framework with support for theming, notifications, pagination, and charts.
    """
    def __init__(self, title="KatamariUI App", header="Welcome to KatamariUI"):
        self.title = title
        self.header = header
        self.components = []  # Holds all UI components
        self.chart_manager = KatamariCharts()  # Integrate KatamariCharts
```

#### **Methods**

- **`chartjs(chart_data: Dict[str, Any], chart_type: str = "bar")`**: Uses **KatamariCharts** to render a **Chart.js** chart.

    ```python
    async def chartjs(self, chart_data: Dict[str, Any], chart_type: str = "bar"):
        """
        Use KatamariCharts to render a Chart.js chart.
        
        Args:
            chart_data (dict): Data for Chart.js chart.
            chart_type (str): Type of chart (bar, line, pie, etc.).
        """
    ```

- **`matplotlib_chart(plot_func: Callable)`**: Uses **KatamariCharts** to render a **Matplotlib** chart.

    ```python
    async def matplotlib_chart(self, plot_func: Callable):
        """
        Use KatamariCharts to render a Matplotlib chart.
        
        Args:
            plot_func (Callable): Function to generate a Matplotlib chart.
        """
    ```

- **`generate_template()`**: Generates the HTML page template including charts and other components.

    ```python
    async def generate_template(self):
        """
        Generate the full HTML template, including charts and other components.
        
        Returns:
            str: The complete HTML template.
        """
    ```

---

## Example Usage: KatamariCharts with KatamariUI

Here's how you can use **KatamariCharts** within **KatamariUI** to render both **Chart.js** and **Matplotlib** charts on a dynamic page.

```python
import asyncio
from KatamariUI import KatamariUI

# Define the main function that builds the UI
async def ui_builder(ui: KatamariUI):
    # Chart.js example
    chart_data = {
        "labels": ["January", "February", "March"],
        "datasets": [{
            "label": "Revenue",
            "data": [1200, 1500, 1800],
            "backgroundColor": ["#FF6384", "#36A2EB", "#FFCE56"]
        }]
    }
    await ui.chartjs(chart_data, chart_type="bar")

    # Matplotlib example
    def plot_example():
        import matplotlib.pyplot as plt
        plt.plot([1, 2, 3], [1, 4, 9], label='Sample Plot')
        plt.legend()

    await ui.matplotlib_chart(plot_example)

# Initialize KatamariUI and generate the template
async def main():
    ui = KatamariUI(title="Dashboard", header="Welcome to Katamari Dashboard")
    await ui_builder(ui)
    html_template = await ui.generate_template()

    # Output the generated HTML (for demonstration purposes)
    print(html_template)

# Run the asynchronous UI generation
asyncio.run(main())
```

#### Output HTML Template Example

This script generates an HTML page with both **Chart.js** and **Matplotlib** charts embedded:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <canvas id="chart-0" width="400" height="400"></canvas>
    <script>
        var ctx = document.getElementById('chart-0').getContext('2d');
        var chart = new Chart(ctx, {
            type: 'bar',
            data: {"labels":["January","February","March"],"datasets":[{"label":"Revenue","data":[1200,1500,1800],"backgroundColor":["#FF6384","#36A2EB","#FFCE56"]}]}
        });
    </script>

    <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABo..." class="img-fluid" /><br>
</body>
</html>
```

---

## How It Works

1. **Chart.js**: The **chartjs()** method in **KatamariUI** uses **KatamariCharts** to generate the required HTML and JavaScript for rendering a Chart.js chart. The chart is embedded in the UI as a `<canvas>` element with the required chart data and options.

2. **Matplotlib**: The **matplotlib_chart()** method in **KatamariUI** calls a Matplotlib plot function, which generates the chart. The chart is then converted into a base64-encoded PNG image and embedded in the HTML as an `<img>` tag.

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.

---

This README provides detailed instructions on using **KatamariCharts** within the **KatamariUI** framework for rendering both dynamic and static charts in a web application.
