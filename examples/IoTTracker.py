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
logger = logging.getLogger("IoTTracker")

app = FastAPI()

# Initialize KatamariUI and KatamariDB with MVCC
ui_instance = KatamariUI(title="Katamari - IoT Tracker", header="Real-Time IoT Sensor Data")
iot_db = KatamariMVCC()

# Store the latest IoT sensor data globally to access within WebSocket
latest_iot_data = []

async def pull_iot_data(event=None, context=None):
    """Lambda function to fetch and store real-time IoT data using KatamariMVCC."""
    global latest_iot_data
    url = "https://api.thingspeak.com/channels/public.json"
    logger.info(f"Fetching data from ThingSpeak... Remaining time: {context.get_remaining_time_in_millis()}ms")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Begin a new transaction
        tx_id = iot_db.begin_transaction()

        new_iot_data = []
        for channel in data["channels"]:
            sensor_info = {
                "Channel ID": channel.get("id"),
                "Name": channel.get("name", "N/A"),
                "Description": channel.get("description", "N/A"),
                "Latitude": channel.get("latitude", "N/A"),
                "Longitude": channel.get("longitude", "N/A"),
                "Elevation": channel.get("elevation", "N/A"),
                "Created At": channel.get("created_at", "N/A"),
                "Last Entry ID": channel.get("last_entry_id", "N/A"),
                "URL": channel.get("url", "N/A"),
                "Github URL": channel.get("github_url", "N/A"),
                "Ranking": channel.get("ranking", "N/A"),
                "Tags": ", ".join(tag.get("name", "") for tag in channel.get("tags", []))
            }

            # Update or insert the sensor data with version control
            existing_record = iot_db.get(channel["id"], tx_id=tx_id)
            if existing_record:
                if existing_record != sensor_info:
                    iot_db.put(channel["id"], sensor_info, tx_id=tx_id)
                    sensor_info["Version"] = len(iot_db.store[channel["id"]])
            else:
                iot_db.put(channel["id"], sensor_info, tx_id=tx_id)
                sensor_info["Version"] = len(iot_db.store[channel["id"]])

            new_iot_data.append(sensor_info)

        # Commit the transaction
        iot_db.commit(tx_id)
        latest_iot_data = new_iot_data
        logger.info(f"Fetched and stored {len(latest_iot_data)} IoT sensor states from ThingSpeak at {datetime.now()}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch IoT data: {e}")
    except Exception as e:
        if tx_id in iot_db.transactions:
            iot_db.rollback(tx_id)
        logger.error(f"Transaction failed: {e}")

# Define the Lambda function
lambda_functions = [
    KatamariLambdaFunction(
        name='PullIoTData',
        handler=pull_iot_data,
        schedule='6s',
        environment={'SOURCE': 'thingspeak_api'},
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

# Tab to display IoT data
async def iot_tracker_tab(ui: KatamariUI):
    """Tab for displaying live IoT data based on Lambda job data."""
    await ui.add_header("Real-Time IoT Sensor Data", level=2)
    await ui.table(latest_iot_data)

# Root route to load the default page with IoT tracker
@app.get("/", response_class=HTMLResponse)
async def get():
    ui_instance.configure_navbar([
        {"label": "IoT Tracker", "link": "/"}
    ])
    await iot_tracker_tab(ui_instance)
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
            const sensors = JSON.parse(event.data);
            let table = document.querySelector("table");
            table.innerHTML = "<thead>" + table.querySelector("thead").innerHTML + "</thead><tbody></tbody>";
            let tbody = table.querySelector("tbody");

            sensors.forEach(sensor => {
                let isUpdated = previousData[sensor["Channel ID"]] && previousData[sensor["Channel ID"]].Version !== sensor.Version;
                previousData[sensor["Channel ID"]] = sensor;

                let row = tbody.insertRow();
                Object.values(sensor).forEach(value => {
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

# WebSocket endpoint to send refreshed IoT data
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(latest_iot_data))
            await asyncio.sleep(6)
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

