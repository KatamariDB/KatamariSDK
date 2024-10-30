Here is the detailed documentation for **KatamariPipelines** in markdown format for a GitHub README file. It explains the purpose of each class, function, and provides example usage.

---

# KatamariPipelines Documentation

**KatamariPipelines** is a framework for managing data pipelines with event-based execution, state machines, and scheduling capabilities. Pipelines are modeled as a series of jobs that can be executed based on schedules, while ensuring state transitions and job lifecycle management.

## Features

- **Event-Driven Execution**: Triggers events for job completion or failure, allowing dynamic workflows.
- **State Management**: Both pipelines and jobs are managed with state machines to track progress.
- **Scheduling**: Jobs can be scheduled using human-readable time strings (e.g., "5m", "2h").
- **Transactional Job Execution**: Jobs are executed within transactions to ensure consistency using **KatamariMVCC**.
- **Pipeline Manager**: Provides configurable scheduling and management of multiple pipelines.

---

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/yourusername/katamaripipelines.git
cd katamaripipelines
pip install -r requirements.txt
```

---

## Classes and Functions

### 1. **Time String Parser**

This utility function converts human-readable time intervals into seconds. It supports quarters (`q`), months (`M`), weeks (`w`), days (`d`), hours (`h`), minutes (`m`), and seconds (`s`).

#### **Function Definition**

```python
def parse_time_string(time_str):
    """
    Convert a time string like '2w3d5h20m30s' to seconds.
    Supports quarters (q), months (M), weeks (w), days (d), hours (h), minutes (m), and seconds (s).
    """
```

#### **Example Usage**

```python
interval = parse_time_string('5m')
print(interval)  # 300 seconds (5 minutes)
```

---

### 2. **EventSystem**

The **EventSystem** allows subscribing to and publishing events. It is used to trigger actions based on the completion or failure of jobs.

#### **Class Definition**

```python
class EventSystem:
    """
    A basic event system to manage publishing and subscribing to events.
    """
    def __init__(self):
        self.events = {}
```

#### **Methods**

- **`subscribe(event_name)`**: Subscribes to an event, returning the asyncio `Event` object.

    ```python
    def subscribe(self, event_name):
        """
        Subscribe to an event, return the asyncio Event object.
        
        Args:
            event_name (str): The name of the event.
            
        Returns:
            asyncio.Event: The event object.
        """
    ```

- **`publish(event_name)`**: Publishes an event, notifying all subscribers.

    ```python
    def publish(self, event_name):
        """
        Publish an event, notifying all subscribers.
        
        Args:
            event_name (str): The name of the event.
        """
    ```

#### **Example Usage**

```python
event_system = EventSystem()

# Subscribe to an event
job_completed_event = event_system.subscribe('job_completed')

# Publish an event
event_system.publish('job_completed')
```

---

### 3. **StateMachine**

The **StateMachine** class tracks the state of pipelines and jobs. It allows for transitions between predefined states (e.g., `Pending`, `Running`, `Completed`, etc.).

#### **Class Definition**

```python
class StateMachine:
    """
    A state machine to manage state transitions of pipelines and jobs.
    """
    def __init__(self, states):
        self.states = states
        self.current_state = None
```

#### **Methods**

- **`set_state(state)`**: Sets the current state of the pipeline or job.

    ```python
    def set_state(self, state):
        """
        Set the current state of the pipeline or job.
        
        Args:
            state (str): The state to set.
        """
    ```

- **`get_state()`**: Returns the current state of the pipeline or job.

    ```python
    def get_state(self):
        """
        Get the current state of the pipeline or job.
        
        Returns:
            str: The current state.
        """
    ```

#### **Example Usage**

```python
state_machine = StateMachine(['Pending', 'Running', 'Completed'])
state_machine.set_state('Running')
print(state_machine.get_state())  # Outputs: Running
```

---

### 4. **PipelineModel**

The **PipelineModel** represents a data pipeline and its configuration. It inherits from **KatamariMVCC** to ensure that pipeline states are stored and versioned correctly using MVCC transactions.

#### **Class Definition**

```python
class PipelineModel(KatamariMVCC):
    """
    A model representing a data pipeline. Uses MVCC for state management and version control.
    """
    def __init__(self, name: str, config: dict, version: int = 1):
        super().__init__()
        self.name = name
        self.config = config
        self.version = version
        self.state_machine = StateMachine(['Scheduled', 'Running', 'Paused', 'Completed'])
        self.state_machine.set_state('Scheduled')
```

#### **Methods**

- **`save_pipeline(tx_id)`**: Saves the current pipeline state within a transaction.

    ```python
    async def save_pipeline(self, tx_id):
        """
        Save the current pipeline state within a transaction.
        
        Args:
            tx_id (str): The transaction ID.
        """
    ```

#### **Example Usage**

```python
pipeline_config = {
    'jobs': [
        {'name': 'Job1', 'schedule': '5m'},
        {'name': 'Job2', 'schedule': '10m'}
    ]
}

pipeline_model = PipelineModel(name='MyPipeline', config=pipeline_config)
tx_id = pipeline_model.begin_transaction()
await pipeline_model.save_pipeline(tx_id)
pipeline_model.commit(tx_id)
```

---

### 5. **JobModel**

The **JobModel** represents an individual job within a pipeline. It tracks the job's state using a state machine and supports job scheduling.

#### **Class Definition**

```python
class JobModel(KatamariMVCC):
    """
    A model representing a job within a pipeline. Uses MVCC for state management.
    """
    def __init__(self, pipeline_id: str, name: str, schedule: str = None):
        super().__init__()
        self.pipeline_id = pipeline_id
        self.name = name
        self.state_machine = StateMachine(['Pending', 'Running', 'Completed', 'Failed'])
        self.state_machine.set_state('Pending')
```

#### **Methods**

- **`save_job(tx_id)`**: Saves the current job state within a transaction.

    ```python
    async def save_job(self, tx_id):
        """
        Save the current job state within a transaction.
        
        Args:
            tx_id (str): The transaction ID.
        """
    ```

#### **Example Usage**

```python
job = JobModel(pipeline_id='MyPipeline', name='Job1', schedule='5m')
tx_id = job.begin_transaction()
await job.save_job(tx_id)
job.commit(tx_id)
```

---

### 6. **PipelineExecutor**

The **PipelineExecutor** is responsible for running the pipeline and executing jobs in the correct order. It manages job execution and transitions between states.

#### **Class Definition**

```python
class PipelineExecutor:
    """
    Executes a pipeline by running its jobs and managing state transitions.
    """
    def __init__(self, pipeline_model: PipelineModel, event_system: EventSystem):
        self.pipeline = pipeline_model
        self.event_system = event_system
        self.jobs = []
        asyncio.create_task(self.init_jobs())  # Initialize jobs asynchronously
```

#### **Methods**

- **`init_jobs()`**: Initializes the jobs from the pipeline configuration.

    ```python
    async def init_jobs(self):
        """
        Initialize jobs asynchronously from the pipeline configuration.
        """
    ```

- **`run_job(job)`**: Runs a specific job and manages its state transitions.

    ```python
    async def run_job(self, job: JobModel):
        """
        Run a job and manage state transitions.
        
        Args:
            job (JobModel): The job to run.
        """
    ```

- **`execute_pipeline()`**: Executes the entire pipeline by running all jobs and transitioning the pipeline state.

    ```python
    async def execute_pipeline(self):
        """
        Execute the entire pipeline by running all jobs.
        """
    ```

#### **Example Usage**

```python
pipeline_executor = PipelineExecutor(pipeline_model, event_system)
await pipeline_executor.execute_pipeline()
```

---

### 7. **PipelineManager**

The **PipelineManager** is responsible for managing multiple pipelines. It allows scheduling and executing pipelines either on startup or at regular intervals.

#### **Class Definition**

```python
class PipelineManager:
    """
    Manages multiple pipelines and schedules their execution.
    """
    def __init__(self, pipeline_configs, event_system):
        self.pipeline_configs = pipeline_configs
        self.event_system = event_system
        self.executors = []
```

#### **Methods**

- **`create_executors()`**: Creates pipeline executors for each pipeline configuration.

    ```python
    def create_executors(self):
        """
        Create pipeline executors for each pipeline config.
        """
    ```

- **`schedule_pipelines()`**: Schedules and executes all pipelines.

    ```python
    async def schedule_pipelines(self):
        """
        Schedule and execute all pipelines.
        """
    ```



- **`schedule_pipelines_with_interval(interval_str)`**: Runs pipelines at a defined interval.

    ```python
    async def schedule_pipelines_with_interval(self, interval_str):
        """
        Run pipelines at a defined interval.
        
        Args:
            interval_str (str): Interval as a time string (e.g., '5m').
        """
    ```

#### **Example Usage**

```python
pipeline_configs = [
    {'name': 'Pipeline1', 'jobs': [{'name': 'Job1', 'schedule': '5m'}]},
    {'name': 'Pipeline2', 'jobs': [{'name': 'Job2', 'schedule': '10m'}]}
]

pipeline_manager = PipelineManager(pipeline_configs, event_system)
await pipeline_manager.startup_event()
```

---

## Example Pipeline Execution

Here's a full example that demonstrates setting up pipelines, creating jobs, and running them.

```python
# Event System
event_system = EventSystem()

# Pipeline Configuration
pipeline_configs = [
    {
        'name': 'DataPipeline',
        'jobs': [
            {'name': 'ExtractJob', 'schedule': '5m'},
            {'name': 'TransformJob', 'schedule': '10m'}
        ]
    }
]

# Create and run the PipelineManager
pipeline_manager = PipelineManager(pipeline_configs, event_system)

# Schedule pipelines to run every 5 minutes
await pipeline_manager.schedule_pipelines_with_interval('5m')
```

---

## Contributing

Contributions are welcome! Feel free to submit pull requests, open issues, or suggest new features.

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.

---

This README provides a detailed overview of the **KatamariPipelines** project, explaining the main components, classes, functions, and their usage with examples.
