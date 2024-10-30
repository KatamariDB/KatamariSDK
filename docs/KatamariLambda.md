Here's a detailed markdown documentation for the provided code that can be used in a GitHub README file.

---

# KatamariLambda Documentation

This repository contains **KatamariLambda**, a lightweight, event-driven Lambda-like framework designed to manage function invocations based on time schedules or event triggers. It includes:

- **KatamariLambdaFunction**: Defines individual Lambda functions with configurable concurrency, memory limits, timeouts, and schedules.
- **KatamariLambdaManager**: Manages the lifecycle of multiple Lambda functions, handling event-driven or scheduled invocations.
- **Time String Parser**: Converts human-readable time intervals into seconds (e.g., "2w3d5h20m30s" into seconds).

---

## Features

- **Time-based Scheduling**: Define Lambda functions that can run at specific intervals (e.g., every 5 minutes).
- **Event-driven Invocation**: Invoke Lambda functions based on specific events.
- **Concurrency Control**: Limit the number of concurrent executions per Lambda function.
- **Memory and Timeout Management**: Set memory and timeout limits for each Lambda function.
- **State Management**: Functions manage their state through transitions like `Pending`, `Running`, `Completed`, or `Failed`.

---

## Installation

Clone the repository and install any required dependencies:

```bash
git clone https://github.com/yourusername/katamarilambda.git
cd katamarilambda
pip install -r requirements.txt
```

---

## Classes and Functions

### 1. **Time String Parser**

This utility converts human-readable time intervals into seconds. It supports quarters (`q`), months (`M`), weeks (`w`), days (`d`), hours (`h`), minutes (`m`), and seconds (`s`).

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
interval = parse_time_string('1h30m')
print(interval)  # 5400 seconds (1 hour 30 minutes)
```

---

### 2. **LambdaContext**

The `LambdaContext` class mimics the AWS Lambda context object, providing information about the function invocation, such as memory limit and the remaining execution time.

#### **Class Definition**

```python
class LambdaContext:
    """
    Mimics the AWS Lambda context object, containing information about the invocation.
    """
```

#### **Methods**

- **`get_remaining_time_in_millis()`**: Returns the remaining execution time in milliseconds before the function times out.

    ```python
    def get_remaining_time_in_millis(self):
        """
        Returns the remaining execution time in milliseconds before the function times out.
        """
    ```

#### **Example Usage**

```python
context = LambdaContext('MyLambda', 128, 300)
remaining_time = context.get_remaining_time_in_millis()
print(remaining_time)
```

---

### 3. **KatamariLambdaFunction**

The `KatamariLambdaFunction` class represents a function in the KatamariLambda framework. Each Lambda function can have environment variables, memory limits, concurrency limits, and timeouts.

#### **Class Definition**

```python
class KatamariLambdaFunction:
    """
    Represents a Lambda function in KatamariLambda.
    Each function has a state machine, can be triggered by events, and can have environment variables, concurrency, and timeouts.
    """
```

#### **Methods**

- **`__init__(...)`**: Initializes the Lambda function with a name, handler, schedule, environment variables, memory limits, concurrency limits, and timeout.

    ```python
    def __init__(self, name: str, handler: callable, schedule: str = None, environment=None, timeout_seconds=300, memory_limit=128, concurrency_limit=1):
        """
        Initialize a Lambda function with the provided settings.
        
        Args:
            name (str): The name of the function.
            handler (callable): The handler function to execute.
            schedule (str): Optional time schedule (e.g., '5m' for every 5 minutes).
            environment (dict): Environment variables for the function.
            timeout_seconds (int): Timeout in seconds for each invocation.
            memory_limit (int): Memory limit in MB.
            concurrency_limit (int): Max number of concurrent executions.
        """
    ```

- **`invoke(event=None, invocation_type='RequestResponse')`**: Invokes the Lambda function while managing its state transitions.

    ```python
    async def invoke(self, event=None, invocation_type='RequestResponse'):
        """
        Invoke the Lambda function and manage its state transitions.
        
        Args:
            event (dict): Optional event data.
            invocation_type (str): Type of invocation (RequestResponse).
        """
    ```

#### **Example Usage**

```python
async def handler(event, context):
    print(f"Handling event: {event}")

lambda_function = KatamariLambdaFunction(
    name='MyLambda',
    handler=handler,
    schedule='5m',
    environment={'VAR': 'value'},
    timeout_seconds=300,
    memory_limit=128,
    concurrency_limit=2
)

await lambda_function.invoke(event={'key': 'value'})
```

---

### 4. **KatamariLambdaManager**

The `KatamariLambdaManager` manages multiple **KatamariLambdaFunction** instances. It handles function scheduling, event-based invocation, and concurrency.

#### **Class Definition**

```python
class KatamariLambdaManager:
    """
    Manages the lifecycle of KatamariLambda functions, including scheduling, concurrency, and event-driven invocation.
    """
```

#### **Methods**

- **`invoke_event_based(event_name, event_data=None)`**: Invokes functions based on event triggers.

    ```python
    async def invoke_event_based(self, event_name, event_data=None):
        """
        Invoke functions based on an event trigger.
        
        Args:
            event_name (str): Name of the event.
            event_data (dict): Optional event data to pass to the handler.
        """
    ```

- **`schedule_functions()`**: Schedules functions to run at specific intervals based on their defined schedules.

    ```python
    async def schedule_functions(self):
        """
        Schedule functions to run at specified intervals based on their defined schedules.
        """
    ```

#### **Example Usage**

```python
# Create a manager with multiple Lambda functions
lambda_manager = KatamariLambdaManager(lambda_functions)

# Schedule Lambda functions to run at intervals
await lambda_manager.schedule_functions()

# Invoke event-based functions
await lambda_manager.invoke_event_based('data_ingestion_event')
```

---

### Example Usage

In this example, two Lambda functions are created: one to pull RSS data and another to process it. The `KatamariLambdaManager` is used to manage and schedule these functions.

```python
# Define Lambda functions
async def pull_rss_data(event=None, context=None):
    logger.info(f"Pulling RSS data... Remaining time: {context.get_remaining_time_in_millis()}ms")
    await asyncio.sleep(1)  # Simulate delay
    logger.info(f"RSS data pulled successfully! Memory Limit: {context.memory_limit_in_mb}MB")

async def process_rss_data(event=None, context=None):
    logger.info(f"Processing RSS data... Remaining time: {context.get_remaining_time_in_millis()}ms")
    await asyncio.sleep(1)  # Simulate delay
    logger.info(f"RSS data processed successfully!")

# Configure Lambda functions
lambda_functions = [
    KatamariLambdaFunction(
        name='PullRSSData',
        handler=pull_rss_data,
        schedule='1m',
        environment={'SOURCE': 'news_rss_feed'},
        timeout_seconds=240,
        memory_limit=256,
        concurrency_limit=2
    ),
    KatamariLambdaFunction(
        name='ProcessRSSData',
        handler=process_rss_data,
        schedule='2m',
        environment={'TARGET': 'data_processor'},
        timeout_seconds=180,
        memory_limit=512,
        concurrency_limit=1
    )
]

# Instantiate the manager
lambda_manager = KatamariLambdaManager(lambda_functions)

# Start the event loop with scheduling
async def main():
    await lambda_manager.invoke_event_based('rss_data_pulled')
    await lambda_manager.schedule_functions()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Contributing

We welcome contributions! If you find any bugs or have ideas for improvements, feel free to open an issue or submit a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.

---

This README file provides detailed documentation for the **KatamariLambda** project, explaining the main components, classes, functions, and their usage with examples.
