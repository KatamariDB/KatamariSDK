Certainly! Below is the full documentation for **KatamariMQServer** and **KatamariMQClient** in **Markdown** format. This includes all classes and functions documented for clarity.

---

# KatamariMQServer and KatamariMQClient Documentation

## Overview

The **KatamariMQServer** and **KatamariMQClient** are part of the **KatamariMQ** system designed to manage distributed processing of jobs, such as pipeline tasks, Lambda function execution, and sharded data across worker nodes. 

- **KatamariMQServer**: This class acts as the central controller that manages job distribution, worker registration, workload tracking, data sharding, and pipeline sharing.
- **KatamariMQClient** (WorkerNode): The client that connects to the MQ server, receives jobs (including Lambda functions, shards, and pipeline tasks), and processes them. The client also manages sending periodic heartbeats back to the server to update workload information.

---

## KatamariMQServer

### `class KatamariMQServer(KatamariMVCC)`
The **KatamariMQServer** class manages the core message queue operations for distributed job processing. It distributes jobs to workers, shards data for parallel processing, and tracks job states using **KatamariMVCC**. It also uses **KatamariDBM** for storing job details and data shards.

### **Constructor**
```python
def __init__(self, db_filename='katamari_mq.db')
```
- Initializes the server with a **KatamariDBM** instance to handle database operations.
- Inherits from **KatamariMVCC** to manage job state consistency.
- Parameters:
  - `db_filename`: The name of the database file for **KatamariDBM** (default: `'katamari_mq.db'`).
- Attributes:
  - `workers`: A dictionary mapping worker IDs to their current state, including workload and last heartbeat.
  - `jobs_queue`: A queue for managing pending jobs to be dispatched.
  - `worker_data_shards`: Tracks data shards assigned to each worker.

---

### **Function: `register_worker()`**
```python
async def register_worker(self, websocket, worker_id: str)
```
- Registers a new worker and stores its state (including workload) in the **KatamariDBM**.
- Parameters:
  - `websocket`: The WebSocket connection associated with the worker.
  - `worker_id`: The unique identifier of the worker.
- Stores:
  - `worker_id`, `workload`, `registered_at` in **KatamariDBM**.

---

### **Function: `update_heartbeat()`**
```python
async def update_heartbeat(self, worker_id: str, workload: int)
```
- Updates the heartbeat information of a worker, including workload and timestamp.
- Parameters:
  - `worker_id`: The unique ID of the worker sending the heartbeat.
  - `workload`: The current workload of the worker.
- Updates the worker's state in **KatamariDBM** and logs the heartbeat event.

---

### **Function: `shard_data()`**
```python
async def shard_data(self, data: list, num_shards: int) -> list
```
- Splits large datasets into smaller shards for distribution among workers.
- Parameters:
  - `data`: A list of data that needs to be sharded.
  - `num_shards`: The number of shards to divide the data into.
- Returns:
  - A list of sharded data.

---

### **Function: `assign_shards()`**
```python
async def assign_shards(self, job_data: dict)
```
- Distributes data shards to workers based on their current workload.
- Parameters:
  - `job_data`: A dictionary containing job-related data, including the list of data to be sharded.
- Stores the data shards in **KatamariDBM** and dispatches them to the least loaded workers.

---

### **Function: `send_job_to_worker()`**
```python
async def send_job_to_worker(self, worker_id: str, job_data: dict)
```
- Sends a job or data shard to a specific worker.
- Parameters:
  - `worker_id`: The unique ID of the worker to which the job will be sent.
  - `job_data`: A dictionary containing job details to be processed.

---

### **Function: `dispatch_pipeline()`**
```python
async def dispatch_pipeline(self, pipeline_data: dict)
```
- Dispatches a pipeline job to workers. The pipeline consists of multiple tasks, which will be processed in parallel by different workers.
- Parameters:
  - `pipeline_data`: A dictionary containing the pipeline ID and associated jobs to be processed.
- Shards the pipeline tasks and sends them to the workers.

---

### **Function: `dispatch_lambda()`**
```python
async def dispatch_lambda(self, lambda_data: dict)
```
- Dispatches a Lambda function to workers for execution.
- Parameters:
  - `lambda_data`: A dictionary containing Lambda function details, such as function name, environment variables, and resource limits (memory, timeout).

---

### **Function: `receive_messages()`**
```python
async def receive_messages(self, websocket, worker_id: str)
```
- Listens for messages from a worker, including heartbeats and job completion notifications.
- Parameters:
  - `websocket`: The WebSocket connection from which messages will be received.
  - `worker_id`: The unique ID of the worker sending the messages.

---

### **Function: `handle_worker()`**
```python
async def handle_worker(self, websocket, path)
```
- Handles new worker connections. Registers the worker and starts receiving messages from them.
- Parameters:
  - `websocket`: The WebSocket connection used to communicate with the worker.
  - `path`: The WebSocket path.

---

### **Function: `start()`**
```python
async def start(self)
```
- Starts the WebSocket server that listens for worker connections on the specified host and port.
- Initiates the server to handle incoming worker connections.

---

## KatamariMQClient (WorkerNode)

### `class WorkerNode(KatamariMVCC)`
The **WorkerNode** class represents a worker that connects to the **KatamariMQServer**, receives jobs (including Lambda functions, shards, and pipeline tasks), and processes them. The worker node also sends periodic heartbeats to the server to update its workload status.

### **Constructor**
```python
def __init__(self, node_id: str, server_uri: str)
```
- Initializes the worker node with a **KatamariDBM** instance for local storage and **KatamariMVCC** for job state management.
- Parameters:
  - `node_id`: The unique identifier of the worker node.
  - `server_uri`: The WebSocket URI of the **KatamariMQServer**.
- Attributes:
  - `workload`: Tracks the current workload of the worker.
  - `db`: A **KatamariDBM** instance that stores local data for the worker.

---

### **Function: `process_pipeline_job()`**
```python
async def process_pipeline_job(self, job_data: dict)
```
- Processes a pipeline job using **KatamariPipelines**' **JobModel**. Tracks the job state using **KatamariMVCC**.
- Parameters:
  - `job_data`: A dictionary containing details about the pipeline job.

---

### **Function: `process_lambda_function()`**
```python
async def process_lambda_function(self, function_data: dict)
```
- Processes a **KatamariLambda** function. It executes the function and manages its state.
- Parameters:
  - `function_data`: A dictionary containing Lambda function details, such as function name, environment, timeout, and memory.

---

### **Function: `lambda_handler()`**
```python
async def lambda_handler(self, event=None, context=None)
```
- A handler function to simulate Lambda execution.
- Parameters:
  - `event`: Optional event data passed to the Lambda function.
  - `context`: Optional context data passed to the Lambda function.

---

### **Function: `process_job()`**
```python
async def process_job(self, job)
```
- Processes a job received from the **KatamariMQServer** based on the job type (pipeline, Lambda, shard).
- Parameters:
  - `job`: A dictionary containing job details.

---

### **Function: `start()`**
```python
async def start(self)
```
- Starts the worker node and connects to the **KatamariMQServer** via WebSocket. Initiates job processing and sends periodic heartbeats.
- Sends initial registration information to the server (worker ID and workload).

---

### **Function: `send_heartbeat()`**
```python
async def send_heartbeat(self, websocket)
```
- Periodically sends heartbeats to the **KatamariMQServer** to update the worker's current workload.
- Parameters:
  - `websocket`: The WebSocket connection used to send the heartbeat.

---

### **Function: `receive_jobs()`**
```python
async def receive_jobs(self, websocket)
```
- Listens for jobs from the **KatamariMQServer** and processes them based on the job type.
- Parameters:
  - `websocket`: The WebSocket connection from which jobs will be received.

---

### **Example Usage (Server & Client)**

#### Running the **KatamariMQServer**
```python
async def main():
    server = KatamariMQServer(db_filename='katamari_mq.db')
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())
```

#### Running the **WorkerNode**
```python
async def main():
    worker = WorkerNode(node

_id="worker_1", server_uri="ws://localhost:8765")
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
```

---
