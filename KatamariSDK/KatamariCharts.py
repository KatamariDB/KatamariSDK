import matplotlib.pyplot as plt
import json
from io import BytesIO
from typing import *
class KatamariCharts:
    """Handles chart rendering using Chart.js and Matplotlib."""

    def __init__(self):
        self.components = []  # Holds chart components to be embedded in the page

    # Chart.js rendering
    def render_chartjs(self, chart_data: Dict[str, Any], chart_type: str = "bar"):
        """
        Render a Chart.js chart using provided data and type.
        :param chart_data: Dictionary containing data and labels for Chart.js.
        :param chart_type: Type of chart ('bar', 'line', 'pie', etc.).
        """
        chart_data_json = json.dumps(chart_data)
        chart_id = f"chart-{len(self.components)}"
        chart_html = f"""
        <canvas id="{chart_id}" width="400" height="400"></canvas>
        <script>
            var ctx = document.getElementById('{chart_id}').getContext('2d');
            var chart = new Chart(ctx, {{
                type: '{chart_type}',
                data: {chart_data_json},
            }});
        </script>
        """
        self.components.append(chart_html)

    # Matplotlib rendering
    def render_matplotlib(self, plot_func: Callable):
        """
        Render a Matplotlib chart as a base64-encoded image.
        :param plot_func: Callable function that generates a Matplotlib chart.
        """
        buf = BytesIO()
        plot_func()  # Call the plot function to generate the chart
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        chart_html = f'<img src="data:image/png;base64,{image_base64}" class="img-fluid" /><br>'
        self.components.append(chart_html)

    def get_components(self):
        """Return all rendered chart components."""
        return self.components

# Example usage of KatamariCharts within KatamariUI
class KatamariUI:
    """Dynamic UI framework with support for theming, notifications, pagination, and charts."""

    def __init__(self, title="KatamariUI App", header="Welcome to KatamariUI"):
        self.title = title
        self.header = header
        self.components = []  # Holds all UI components
        self.chart_manager = KatamariCharts()  # Instantiate KatamariCharts

    async def chartjs(self, chart_data: Dict[str, Any], chart_type: str = "bar"):
        """Use KatamariCharts to render a Chart.js chart."""
        self.chart_manager.render_chartjs(chart_data, chart_type)

    async def matplotlib_chart(self, plot_func: Callable):
        """Use KatamariCharts to render a Matplotlib chart."""
        self.chart_manager.render_matplotlib(plot_func)

    async def generate_template(self):
        """Generate the full HTML template."""
        chart_content = "\n".join(self.chart_manager.get_components())
        html_template = f"""
        <html>
        <head>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            {chart_content}
        </body>
        </html>
        """
        return html_template

