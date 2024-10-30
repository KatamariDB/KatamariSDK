import asyncio
import logging
from datetime import datetime, timedelta
import re
from KatamariSDK.KatamariPipelines import *
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KatamariLambda')

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

# ----------------------- Lambda Context -----------------------

class LambdaContext:
    """
    Mimics the AWS Lambda context object, containing information about the invocation.
    """
    def __init__(self, function_name, memory_limit, timeout_seconds):
        self.function_name = function_name
        self.memory_limit_in_mb = memory_limit
        self.timeout_seconds = timeout_seconds
        self.request_id = 'req_' + datetime.now().strftime("%Y%m%d%H%M%S")

    def get_remaining_time_in_millis(self):
        """Returns the remaining execution time in milliseconds before the function times out."""
        return max(0, int((self.start_time + timedelta(seconds=self.timeout_seconds) - datetime.now()).total_seconds() * 1000))

# ----------------------- KatamariLambda Function -----------------------

class KatamariLambdaFunction:
    """
    Represents a Lambda function in KatamariLambda.
    Each function has a state machine, can be triggered by events, and can have environment variables, concurrency, and timeouts.
    """
    def __init__(self, name: str, handler: callable, schedule: str = None, environment=None, timeout_seconds=300, memory_limit=128, concurrency_limit=1):
        self.name = name
        self.handler = handler
        self.schedule = schedule  # e.g., '5m' for every 5 minutes
        self.environment = environment or {}  # Environment variables for the function
        self.timeout_seconds = timeout_seconds  # Timeout in seconds
        self.memory_limit = memory_limit  # Memory limit in MB
        self.concurrency_limit = concurrency_limit  # Concurrency limit (number of simultaneous executions)
        self.active_executions = 0  # Track the number of active executions
        self.state_machine = StateMachine(['Pending', 'Running', 'Completed', 'Failed'])
        self.state_machine.set_state('Pending')
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

    async def invoke(self, event=None, invocation_type='RequestResponse'):
        """Invoke the Lambda function and manage its state transitions."""
        if self.active_executions >= self.concurrency_limit:
            logger.error(f"Concurrency limit reached for Lambda function: {self.name}. Skipping invocation.")
            return

        try:
            logger.info(f"Invoking Lambda function: {self.name}...")
            self.state_machine.set_state('Running')
            self.active_executions += 1

            # Prepare Lambda context
            context = LambdaContext(function_name=self.name, memory_limit=self.memory_limit, timeout_seconds=self.timeout_seconds)
            context.start_time = datetime.now()

            # Use asyncio's timeout feature to emulate Lambda timeouts
            await asyncio.wait_for(self.handler(event, context), timeout=self.timeout_seconds)

            self.state_machine.set_state('Completed')
            logger.info(f"Lambda function {self.name} completed.")
        except asyncio.TimeoutError:
            self.state_machine.set_state('Failed')
            logger.error(f"Lambda function {self.name} timed out after {self.timeout_seconds} seconds.")
        except Exception as e:
            self.state_machine.set_state('Failed')
            logger.error(f"Lambda function {self.name} failed: {e}")
        finally:
            self.active_executions -= 1
            self.updated_at = datetime.now().isoformat()

# ----------------------- KatamariLambda Manager -----------------------

class KatamariLambdaManager:
    """
    Manages the lifecycle of KatamariLambda functions, including scheduling, concurrency, and event-driven invocation.
    """
    def __init__(self, functions):
        self.functions = functions  # List of KatamariLambdaFunction objects

    async def invoke_event_based(self, event_name, event_data=None):
        """
        Invoke functions based on an event trigger.
        """
        for function in self.functions:
            if function.schedule is None:  # Invoke event-driven functions only
                await function.invoke(event_data)

    async def schedule_functions(self):
        """
        Schedule functions to run at specified intervals.
        """
        while True:
            for function in self.functions:
                if function.schedule:  # Only schedule functions with a schedule
                    interval = parse_time_string(function.schedule)
                    logger.info(f"Scheduling Lambda function {function.name} to run every {function.schedule}.")
                    await function.invoke()  # Invoke the function
                    await asyncio.sleep(interval)  # Wait for the next scheduled run

# ----------------------- Example Usage -----------------------

# Define Lambda functions (jobs) with environment variables, timeouts, and concurrency
async def pull_rss_data(event=None, context=None):
    """Simulates pulling RSS data."""
    logger.info(f"Pulling RSS data... Remaining time: {context.get_remaining_time_in_millis()}ms")
    await asyncio.sleep(1)  # Simulate delay
    logger.info(f"RSS data pulled successfully! Memory Limit: {context.memory_limit_in_mb}MB")

async def process_rss_data(event=None, context=None):
    """Simulates processing RSS data."""
    logger.info(f"Processing RSS data... Remaining time: {context.get_remaining_time_in_millis()}ms")
    await asyncio.sleep(1)  # Simulate processing delay
    logger.info(f"RSS data processed successfully!")

# Example configuration for KatamariLambda functions
lambda_functions = [
    KatamariLambdaFunction(name='PullRSSData', handler=pull_rss_data, schedule='1m', environment={'SOURCE': 'news_rss_feed'}, timeout_seconds=240, memory_limit=256, concurrency_limit=2),
    KatamariLambdaFunction(name='ProcessRSSData', handler=process_rss_data, schedule='2m', environment={'TARGET': 'data_processor'}, timeout_seconds=180, memory_limit=512, concurrency_limit=1)
]

# Instantiate the manager
lambda_manager = KatamariLambdaManager(lambda_functions)

# Start the event loop with scheduling
async def main():
    # Event-driven invocation example
    await lambda_manager.invoke_event_based('rss_data_pulled')
    # Schedule Lambda functions to run based on the defined schedule
    await lambda_manager.schedule_functions()

if __name__ == "__main__":
    asyncio.run(main())
