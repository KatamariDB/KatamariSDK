import asyncio
import json
import logging
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from KatamariUI import KatamariUI
from KatamariLambda import KatamariLambdaFunction, KatamariLambdaManager
from KatamariDB import KatamariMVCC
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AirQualityTracker")

app = FastAPI()

# Initialize KatamariUI and KatamariDB with MVCC
ui_instance = KatamariUI(title="Katamari - Air Quality Tracker", header="Real-Time Air Quality Data")
air_quality_db = KatamariMVCC()

# Store the latest air quality data globally to access within WebSocket
latest_air_quality_data = []

async def pull_air_quality_data(event=None, context=None):
    """Lambda function to fetch and store real-time air quality data using KatamariMVCC."""
    global latest_air_quality_data
    api_key = "API_KEY"  # Replace with your AirNow API key
    url = f"https://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode=20002&distance=25&API_KEY={api_key}"
    logger.info(f"Fetching data from AirNow API... Remaining time: {context.get_remaining_time_in_millis()}ms")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Begin a new transaction
        tx_id = air_quality_db.begin_transaction()

        new_air_quality_data = []
        for observation in data:
            air_quality_info = {
                "Date Observed": observation.get("DateObserved"),
                "Reporting Area": observation.get("ReportingArea"),
                "State Code": observation.get("StateCode"),
                "Latitude": observation.get("Latitude"),
                "Longitude": observation.get("Longitude"),
                "Parameter Name": observation.get("ParameterName"),
                "AQI": observation.get("AQI"),
                "Category": observation.get("Category", {}).get("Name", "N/A"),
            }

            # Update or insert the air quality record with version control
            key = f"{observation['ReportingArea']}_{observation['ParameterName']}"
            existing_record = air_quality_db.get(key, tx_id=tx_id)
            if existing_record:
                if existing_record != air_quality_info:
                    air_quality_db.put(key, air_quality_info, tx_id=tx_id)
                    air_quality_info["Version"] = len(air_quality_db.store[key])
            else:
                air_quality_db.put(key, air_quality_info, tx_id=tx_id)
                air_quality_info["Version"] = len(air_quality_db.store[key])

            new_air_quality_data.append(air_quality_info)

        # Commit the transaction
        air_quality_db.commit(tx_id)
        latest_air_quality_data = new_air_quality_data
        logger.info(f"Fetched and stored {len(latest_air_quality_data)} air quality observations from AirNow API at {datetime.now()}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch AirNow data: {e}")
    except Exception as e:
        if tx_id in air_quality_db.transactions:
            air_quality_db.rollback(tx_id)
        logger.error(f"Transaction failed: {e}")

# Define the Lambda function
lambda_functions = [
    KatamariLambdaFunction(
        name='PullAirQualityData',
        handler=pull_air_quality_data,
        schedule='2s',  # Runs every 6 seconds
        environment={'SOURCE': 'airnow_api'},
        timeout_seconds=240,
        memory_limit=256,
        concurrency_limit=2
    )
]

# Set up the Lambda Manager
lambda_manager = KatamariLambdaManager(lambda_functions)

@app.on_event("startup")
async def start_lambda_manager():
    asyncio.create_task(lambda_manager.schedule_functions())

# Tab to display air quality data
async def air_quality_tracker_tab(ui: KatamariUI):
    """Tab for displaying live air quality data based on Lambda job data."""
    await ui.add_header("Real-Time Air Quality Data", level=2)
    await ui.table(latest_air_quality_data)

# Root route to load the default page with air quality tracker
@app.get("/", response_class=HTMLResponse)
async def get():
    ui_instance.configure_navbar([
        {"label": "Air Quality Tracker", "link": "/"}
    ])
    await air_quality_tracker_tab(ui_instance)
    html_content = await ui_instance.generate_template()

    # Add responsive styles and WebSocket JavaScript for updates
    html_content += """
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        table {
            width: 100%;
            max-width: 100%;
            border-collapse: collapse;
            margin: 0 auto;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border: 1px solid #ddd;
        }
        th {
            background-color: #f4f4f4;
            font-weight: bold;
        }
        tbody tr.highlight {
            background-color: #FFFF99;
            transition: background-color 2s ease;
        }
    </style>
    <script>
        let socket = new WebSocket("ws://localhost:8000/ws");
        let previousData = {};

        socket.onmessage = function(event) {
            const observations = JSON.parse(event.data);
            let table = document.querySelector("table");
            table.innerHTML = "<thead>" + table.querySelector("thead").innerHTML + "</thead><tbody></tbody>";
            let tbody = table.querySelector("tbody");

            observations.forEach(observation => {
                let key = observation["Reporting Area"] + "_" + observation["Parameter Name"];
                let isUpdated = previousData[key] && previousData[key].Version !== observation.Version;
                previousData[key] = observation;

                let row = tbody.insertRow();
                Object.values(observation).forEach(value => {
                    let cell = row.insertCell();
                    cell.textContent = value !== null ? value : "N/A";
                });

                if (isUpdated) {
                    row.classList.add("highlight");
                    setTimeout(() => { row.classList.remove("highlight"); }, 2000);
                    tbody.prepend(row);
                }
            });
        };
    </script>
    """
    return HTMLResponse(content=html_content)

# WebSocket endpoint to send refreshed air quality data
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(latest_air_quality_data))
            await asyncio.sleep(2)  # Refresh every 6 seconds
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

