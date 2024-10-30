import asyncio
import logging
from datetime import datetime
from KatamariSDK.KatamariDB import KatamariMVCC  # Adjust based on your KatamariDB module
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('Pipeline')

# ----------------------- Time String Parser -----------------------

def parse_time_string(time_str):
    """
    Convert a time string like '2w3d5h20m30s' to seconds.
    Supports quarters (q), months (M), weeks (w), days (d), hours (h), minutes (m), and seconds (s).
    """
    time_units = {
        'q': 7884000,  # Approx 3 months in seconds (91.25 days)
        'M': 2628000,  # Approx 1 month in seconds (30.42 days)
        'w': 604800,   # 1 week in seconds
        'd': 86400,    # 1 day in seconds
        'h': 3600,     # 1 hour in seconds
        'm': 60,       # 1 minute in seconds
        's': 1         # 1 second
    }

    total_seconds = 0

    # Regex pattern to match time components (e.g., 2w, 3d, 5h, 20m, 30s)
    pattern = re.compile(r'(\d+)([qMwdhms])')

    # Find all matches and sum their equivalent seconds
    for amount, unit in pattern.findall(time_str):
        total_seconds += int(amount) * time_units[unit]

    return total_seconds

# ----------------------- Event System -----------------------

class EventSystem:
    def __init__(self):
        self.events = {}

    def subscribe(self, event_name):
        """Subscribe to an event, return the asyncio Event object."""
        if event_name not in self.events:
            self.events[event_name] = asyncio.Event()
        return self.events[event_name]

    def publish(self, event_name):
        """Publish an event, notifying all subscribers."""
        if event_name in self.events:
            self.events[event_name].set()
            self.events[event_name].clear()  # Reset event for future use

# ----------------------- State Machine -----------------------

class StateMachine:
    def __init__(self, states):
        self.states = states
        self.current_state = None

    def set_state(self, state):
        """Set the current state."""
        if state not in self.states:
            raise ValueError(f"Invalid state: {state}")
        logger.info(f"State changed to {state}")
        self.current_state = state

    def get_state(self):
        """Get the current state."""
        return self.current_state

# ----------------------- PipelineModel with State Machine -----------------------

class PipelineModel(KatamariMVCC):
    def __init__(self, name: str, config: dict, version: int = 1):
        super().__init__()
        self.name = name
        self.config = config
        self.version = version
        self.state_machine = StateMachine(['Scheduled', 'Running', 'Paused', 'Completed'])
        self.state_machine.set_state('Scheduled')
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    async def save_pipeline(self, tx_id):
        """Save the current pipeline state within a transaction."""
        pipeline_data = {
            'name': self.name,
            'config': self.config,
            'version': self.version,
            'state': self.state_machine.get_state(),
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        self.put(self.name, pipeline_data, tx_id)

# ----------------------- JobModel with State Machine -----------------------

class JobModel(KatamariMVCC):
    def __init__(self, pipeline_id: str, name: str, schedule: str = None):
        super().__init__()
        self.pipeline_id = pipeline_id
        self.name = name
        self.state_machine = StateMachine(['Pending', 'Running', 'Completed', 'Failed'])
        self.state_machine.set_state('Pending')
        self.schedule = schedule
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    async def save_job(self, tx_id):
        """Save the current job state within a transaction."""
        job_data = {
            'pipeline_id': self.pipeline_id,
            'name': self.name,
            'state': self.state_machine.get_state(),
            'schedule': self.schedule,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        self.put(self.name, job_data, tx_id)

# ----------------------- PipelineExecutor -----------------------

class PipelineExecutor:
    def __init__(self, pipeline_model: PipelineModel, event_system: EventSystem):
        self.pipeline = pipeline_model
        self.event_system = event_system
        self.jobs = []  # Initialize jobs list
        asyncio.create_task(self.init_jobs())  # Initialize jobs asynchronously

    async def init_jobs(self):
        """Initialize jobs asynchronously."""
        self.jobs = await self.load_jobs_from_config(self.pipeline.config)

    async def load_jobs_from_config(self, config: dict):
        """Load jobs from the pipeline configuration."""
        jobs = []
        tx_id = self.pipeline.begin_transaction()  # Start MVCC transaction
        for job_conf in config.get('jobs', []):
            job = JobModel(
                pipeline_id=self.pipeline.name,
                name=job_conf['name'],
                schedule=job_conf.get('schedule')
            )
            await job.save_job(tx_id)  # Save job within transaction
            jobs.append(job)
        self.pipeline.commit(tx_id)  # Commit the transaction
        return jobs

    async def run_job(self, job: JobModel):
        """Run a job and manage state transitions."""
        tx_id = self.pipeline.begin_transaction()  # Start MVCC transaction
        try:
            logger.info(f"Running job {job.name}...")
            job.state_machine.set_state('Running')
            await job.save_job(tx_id)  # Save job state as Running

            await asyncio.sleep(2)  # Simulate job execution
            logger.info(f"Job {job.name} completed.")

            job.state_machine.set_state('Completed')
            await job.save_job(tx_id)  # Save job state as Completed

            # Trigger job completion event
            self.event_system.publish('job_completed')

        except Exception as e:
            logger.error(f"Job {job.name} failed: {e}")
            job.state_machine.set_state('Failed')
            await job.save_job(tx_id)  # Save job state as Failed
            self.event_system.publish('job_failed')

        self.pipeline.commit(tx_id)  # Commit the transaction

    async def execute_pipeline(self):
        """Execute the entire pipeline by listening to events and transitioning states."""
        tx_id = self.pipeline.begin_transaction()  # Start pipeline transaction
        self.pipeline.state_machine.set_state('Running')
        await self.pipeline.save_pipeline(tx_id)  # Save pipeline state as Running
        self.pipeline.commit(tx_id)  # Commit the transaction

        job_completed_event = self.event_system.subscribe('job_completed')

        for job in self.jobs:
            await self.run_job(job)
            await job_completed_event.wait()  # Wait for the job to complete

        tx_id = self.pipeline.begin_transaction()
        self.pipeline.state_machine.set_state('Completed')
        await self.pipeline.save_pipeline(tx_id)  # Save pipeline state as Completed
        self.pipeline.commit(tx_id)  # Commit the transaction

# ----------------------- PipelineManager with Configurable Scheduler -----------------------

class PipelineManager:
    def __init__(self, pipeline_configs, event_system):
        self.pipeline_configs = pipeline_configs
        self.event_system = event_system
        self.executors = []

    def create_executors(self):
        """Create pipeline executors for each pipeline config."""
        for config in self.pipeline_configs:
            pipeline_model = PipelineModel(name=config['name'], config=config)
            executor = PipelineExecutor(pipeline_model, self.event_system)
            self.executors.append(executor)

    async def schedule_pipelines(self):
        """Schedule and execute all pipelines."""
        tasks = [executor.execute_pipeline() for executor in self.executors]
        await asyncio.gather(*tasks)

    async def startup_event(self):
        """Initialize pipelines and start the event loop."""
        self.create_executors()
        await self.schedule_pipelines()

    async def schedule_pipelines_with_interval(self, interval_str):
        """Run pipelines at a defined interval (in a user-friendly format like 5m)."""
        interval = parse_time_string(interval_str)
        while True:
            logger.info(f"Scheduling pipelines to run every {interval_str}.")
            await self.schedule_pipelines()
            await asyncio.sleep(interval)  # Wait for the next scheduled run
