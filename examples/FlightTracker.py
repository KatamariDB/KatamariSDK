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
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenSkyTracker")

app = FastAPI()

# Initialize KatamariUI and KatamariDB with MVCC
ui_instance = KatamariUI(title="Katamari - Flight Tracker", header="OpenSky Live Flight Tracker")
flight_db = KatamariMVCC()

# Store the latest flight data globally to access within WebSocket
latest_flight_data = []

async def pull_opensky_data(event=None, context=None):
    """Lambda function to fetch and store real-time flight data using KatamariMVCC."""
    global latest_flight_data
    url = "https://opensky-network.org/api/states/all"
    logger.info(f"Fetching data from OpenSky API... Remaining time: {context.get_remaining_time_in_millis()}ms")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # Begin a new transaction
        tx_id = flight_db.begin_transaction()

        new_flight_data = []
        for flight in data["states"]:
            flight_info = {
                "ICAO24": flight[0],
                "Callsign": flight[1].strip(),
                "Country": flight[2],
                "Last Contact": flight[3],
                "Longitude": flight[5],
                "Latitude": flight[6],
                "Altitude (m)": flight[7],
                "On Ground": flight[8],
                "Velocity (m/s)": flight[9],
                "Heading (deg)": flight[10],
                "Vertical Rate (m/s)": flight[11],
                "Baro Altitude (m)": flight[13],
                "Squawk": flight[14],
                "Position Source": flight[16]
            }

            # Update or insert the flight record with version control using put and transaction ID
            existing_record = flight_db.get(flight[0], tx_id=tx_id)
            if existing_record:
                # Update existing record if data has changed
                if existing_record != flight_info:
                    flight_db.put(flight[0], flight_info, tx_id=tx_id)
                    flight_info["Version"] = len(flight_db.store[flight[0]])  # Track version for each key
            else:
                # Insert new record
                flight_db.put(flight[0], flight_info, tx_id=tx_id)
                flight_info["Version"] = len(flight_db.store[flight[0]])  # Track version for each key

            new_flight_data.append(flight_info)
        
        # Commit the transaction to finalize the changes
        flight_db.commit(tx_id)
        latest_flight_data = new_flight_data
        logger.info(f"Fetched and stored {len(latest_flight_data)} flight states from OpenSky API at {datetime.now()}.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch OpenSky data: {e}")
    except Exception as e:
        # Roll back transaction if there is any failure during put operations
        if tx_id in flight_db.transactions:
            flight_db.rollback(tx_id)
        logger.error(f"Transaction failed: {e}")

# Define the Lambda function using KatamariLambdaFunction
lambda_functions = [
    KatamariLambdaFunction(
        name='PullOpenSkyData',
        handler=pull_opensky_data,
        schedule='6s',  # Runs every 1 minute
        environment={'SOURCE': 'opensky_api'},
        timeout_seconds=240,
        memory_limit=256,
        concurrency_limit=2
    )
]

# Set up the Lambda Manager
lambda_manager = KatamariLambdaManager(lambda_functions)

# Run Lambda Manager in the background to keep data updated
@app.on_event("startup")
async def start_lambda_manager():
    asyncio.create_task(lambda_manager.schedule_functions())

# Tab to display flight data
async def flight_tracker_tab(ui: KatamariUI):
    """Tab for displaying live flight data based on Lambda job data."""
    await ui.add_header("Real-Time Flight Data", level=2)
    await ui.table(latest_flight_data)

# Root route to load the default page with flight tracker
@app.get("/", response_class=HTMLResponse)
async def get():
    # Configure navbar
    ui_instance.configure_navbar([
        {"label": "Flight Tracker", "link": "/"}
    ])

    # Render flight tracker tab
    await flight_tracker_tab(ui_instance)

    # Generate and return HTML content
    html_content = await ui_instance.generate_template()

    # Add responsive styles and WebSocket JavaScript for highlighting updates
    html_content += """
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }
        table {
            width: 100%;
            max-width: 100%;
            border-collapse: collapse;
            margin: 0 auto;
            overflow-x: auto;
            display: block;
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
        @media (max-width: 768px) {
            th, td {
                font-size: 0.9em;
            }
        }
        tbody tr.highlight {
            background-color: #FFFF99;
            transition: background-color 2s ease;
        }
    </style>
    <script>
        let socket = new WebSocket("ws://localhost:8000/ws");
        let previousData = {};  // Store previous flight data for comparison

        socket.onmessage = function(event) {
            const flights = JSON.parse(event.data);
            let table = document.querySelector("table");

            // Clear current table rows, keeping the headers
            table.innerHTML = "<thead>" + table.querySelector("thead").innerHTML + "</thead><tbody></tbody>";
            let tbody = table.querySelector("tbody");

            // Sort updated flights to the top and highlight them by version
            flights.forEach(flight => {
                let isUpdated = previousData[flight.ICAO24] && previousData[flight.ICAO24].Version !== flight.Version;
                previousData[flight.ICAO24] = flight;  // Update previous data

                let row = tbody.insertRow();
                Object.values(flight).forEach(value => {
                    let cell = row.insertCell();
                    cell.textContent = value !== null ? value : "N/A";
                });

                // Highlight the row if it was updated
                if (isUpdated) {
                    row.classList.add("highlight");
                    setTimeout(() => { row.classList.remove("highlight"); }, 2000);  // Remove highlight after 2 seconds
                    tbody.prepend(row);  // Move updated rows to the top
                }
            });
        };
    </script>
    """
    return HTMLResponse(content=html_content)

# WebSocket endpoint to send refreshed flight data every minute
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(latest_flight_data))
            await asyncio.sleep(6)  # Refresh every 60 seconds
    except WebSocketDisconnect:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

