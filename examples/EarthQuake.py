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
logger = logging.getLogger("SeismicTracker")

app = FastAPI()

# Initialize KatamariUI and KatamariDB with MVCC
ui_instance = KatamariUI(title="Katamari - Earthquake Tracker", header="Real-Time Earthquake Data")
seismic_db = KatamariMVCC()

# Store the latest earthquake data globally to access within WebSocket
latest_earthquake_data = []

async def pull_seismic_data(event=None, context=None):
    """Lambda function to fetch and store real-time earthquake data using KatamariMVCC."""
    global latest_earthquake_data
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_hour.geojson"
    logger.info(f"Fetching data from USGS Earthquake API... Remaining time: {context.get_remaining_time_in_millis()}ms")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Begin a new transaction
        tx_id = seismic_db.begin_transaction()

        new_earthquake_data = []
        for feature in data["features"]:
            earthquake_info = {
                "Time": datetime.fromtimestamp(feature["properties"]["time"] / 1000).isoformat(),
                "Location": feature["properties"]["place"],
                "Magnitude": feature["properties"]["mag"],
                "Depth (km)": feature["geometry"]["coordinates"][2],
                "Latitude": feature["geometry"]["coordinates"][1],
                "Longitude": feature["geometry"]["coordinates"][0]
            }

            # Update or insert earthquake data with version control
            event_id = feature["id"]
            existing_record = seismic_db.get(event_id, tx_id=tx_id)
            if existing_record:
                if existing_record != earthquake_info:
                    seismic_db.put(event_id, earthquake_info, tx_id=tx_id)
                    earthquake_info["Version"] = len(seismic_db.store[event_id])
            else:
                seismic_db.put(event_id, earthquake_info, tx_id=tx_id)
                earthquake_info["Version"] = len(seismic_db.store[event_id])

            new_earthquake_data.append(earthquake_info)

        # Commit the transaction
        seismic_db.commit(tx_id)
        latest_earthquake_data = new_earthquake_data
        logger.info(f"Fetched and stored {len(latest_earthquake_data)} earthquake events from USGS API at {datetime.now()}.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch seismic data: {e}")
    except Exception as e:
        if tx_id in seismic_db.transactions:
            seismic_db.rollback(tx_id)
        logger.error(f"Transaction failed: {e}")

# Define the Lambda function
lambda_functions = [
    KatamariLambdaFunction(
        name='PullSeismicData',
        handler=pull_seismic_data,
        schedule='6s',  # Runs every 6 seconds
        environment={'SOURCE': 'usgs_earthquake_api'},
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

# Tab to display seismic data
async def earthquake_tracker_tab(ui: KatamariUI):
    """Tab for displaying live earthquake data based on Lambda job data."""
    await ui.add_header("Real-Time Earthquake Data", level=2)
    await ui.table(latest_earthquake_data)

# Root route to load the default page with earthquake tracker
@app.get("/", response_class=HTMLResponse)
async def get():
    ui_instance.configure_navbar([
        {"label": "Earthquake Tracker", "link": "/"}
    ])
    await earthquake_tracker_tab(ui_instance)
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
            const earthquakes = JSON.parse(event.data);
            let table = document.querySelector("table");
            table.innerHTML = "<thead>" + table.querySelector("thead").innerHTML + "</thead><tbody></tbody>";
            let tbody = table.querySelector("tbody");

            earthquakes.forEach(earthquake => {
                let key = earthquake["Time"];
                let isUpdated = previousData[key] && previousData[key].Version !== earthquake.Version;
                previousData[key] = earthquake;

                let row = tbody.insertRow();
                Object.values(earthquake).forEach(value => {
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

# WebSocket endpoint to send refreshed earthquake data
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(latest_earthquake_data))
            await asyncio.sleep(6)  # Refresh every 6 seconds
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

