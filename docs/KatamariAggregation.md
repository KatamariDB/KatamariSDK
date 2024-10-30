Here is the full documentation for **KatamariAggregation** in markdown format:

# KatamariAggregation

**KatamariAggregation** is a dynamic metric aggregation engine that runs on top of **KatamariORM** and **KatamariMVCC**, supporting real-time and historical aggregation, custom metrics, and querying with filters. It integrates with **KatamariPipelines** for real-time data processing.

---

## Features

- **Dynamic Metric Aggregation**: Supports operations such as `sum`, `avg`, `count`, `min`, and `max`.
- **Real-Time Aggregation**: Processes metrics on real-time streaming data.
- **Filterable Aggregations**: Allows for the application of filters on field values during aggregation.
- **KatamariORM Integration**: Uses **KatamariORM** for fetching and storing data.
- **KatamariPipelines Integration**: Supports real-time data ingestion and aggregation through pipelines.

---

## Installation

Ensure you have the following dependencies installed:

- `KatamariORM` for database operations.
- `KatamariMVCC` for transactional support.
- `KatamariPipelines` for real-time data processing.

---

## Schema Setup

Before using **KatamariAggregation**, define your schema in **KatamariORM**. For example, to aggregate log data:

```python
schema_fields = {
    'log_level': 'TEXT',
    'processing_time': 'NUMERIC',
    'timestamp': 'DATETIME',
    'status': 'TEXT'
}

db = KatamariORM(schema_fields=schema_fields)
```

This schema defines the fields `log_level`, `processing_time`, `timestamp`, and `status`, which will be used in the aggregations.

---

## Classes

### 1. `KatamariAggregation`

The core class that handles the aggregation logic.

#### **Initialization**

```python
KatamariAggregation(db: KatamariORM)
```

- **db**: An instance of **KatamariORM** that handles the storage and querying of data.

#### **Methods**

##### `run_metric(metric_definition: Dict[str, Any]) -> Any`
Runs a specific metric based on the provided definition.

- **metric_definition**: A dictionary defining the metric to be run, including the operation, field, and optional filter.
- **Returns**: The result of the aggregation.

Example:

```python
metric_definition = {
    "name": "avg_response_time",
    "operation": "avg",
    "field": "processing_time",
    "filter": {
        "field": "status",
        "operator": "==",
        "value": "success"
    }
}
result = await aggregation.run_metric(metric_definition)
```

##### `fetch_filtered_data(field: str, filter_condition: Optional[Dict[str, Any]]) -> List[Any]`
Fetches the data from the ORM with optional filtering.

- **field**: The field to fetch data from.
- **filter_condition**: An optional dictionary that defines the filtering condition.

Example:

```python
data = await aggregation.fetch_filtered_data('processing_time', {'field': 'status', 'operator': '==', 'value': 'success'})
```

##### `apply_filter(field_value: Any, filter_condition: Dict[str, Any]) -> bool`
Applies a filter condition to a field value.

- **field_value**: The value of the field being filtered.
- **filter_condition**: A dictionary defining the filter (e.g., `{"field": "status", "operator": "==", "value": "success"}`).

Example:

```python
result = aggregation.apply_filter("ERROR", {"operator": "==", "value": "ERROR"})
```

##### `sum_aggregation(field: str, data: List[Any]) -> float`
Calculates the sum of the values in the field.

- **field**: The field to sum.
- **data**: A list of values from the field.

Example:

```python
result = await aggregation.sum_aggregation("processing_time", [100, 200, 300])
```

##### `avg_aggregation(field: str, data: List[Any]) -> float`
Calculates the average of the values in the field.

- **field**: The field to average.
- **data**: A list of values from the field.

Example:

```python
result = await aggregation.avg_aggregation("processing_time", [100, 200, 300])
```

##### `count_aggregation(field: str, data: List[Any]) -> int`
Counts the occurrences of the field values.

- **field**: The field to count.
- **data**: A list of values from the field.

Example:

```python
result = await aggregation.count_aggregation("log_level", ["INFO", "ERROR", "INFO"])
```

##### `min_aggregation(field: str, data: List[Any]) -> Any`
Finds the minimum value in the field.

- **field**: The field to find the minimum of.
- **data**: A list of values from the field.

Example:

```python
result = await aggregation.min_aggregation("processing_time", [100, 200, 50])
```

##### `max_aggregation(field: str, data: List[Any]) -> Any`
Finds the maximum value in the field.

- **field**: The field to find the maximum of.
- **data**: A list of values from the field.

Example:

```python
result = await aggregation.max_aggregation("processing_time", [100, 200, 50])
```

##### `run_aggregations(metrics_config: Dict[str, Any]) -> Dict[str, Any]`
Runs all the metrics defined in the configuration.

- **metrics_config**: A dictionary defining all the metrics.
- **Returns**: A dictionary containing the results of each metric.

Example:

```python
metrics_config = {
    "metrics": [
        {
            "name": "avg_response_time",
            "operation": "avg",
            "field": "processing_time",
            "filter": {
                "field": "status",
                "operator": "==",
                "value": "success"
            }
        },
        {
            "name": "error_count",
            "operation": "count",
            "field": "log_level",
            "filter": {
                "field": "log_level",
                "operator": "==",
                "value": "ERROR"
            }
        }
    ]
}
results = await aggregation.run_aggregations(metrics_config)
print(results)
```

##### `run_real_time_aggregation(metric_definition: Dict[str, Any], pipeline_data: List[Dict[str, Any]]) -> Any`
Processes real-time data from pipelines.

- **metric_definition**: The metric definition for real-time aggregation.
- **pipeline_data**: A list of data from the real-time pipeline.
- **Returns**: The result of the real-time aggregation.

Example:

```python
pipeline_data = [
    {"processing_time": 150, "status": "success"},
    {"processing_time": 200, "status": "failed"}
]
result = await aggregation.run_real_time_aggregation(metric_definition, pipeline_data)
print(result)
```

---

## Example: Integrating with KatamariORM

```python
async def main():
    schema_fields = {
        'log_level': 'TEXT',
        'processing_time': 'NUMERIC',
        'timestamp': 'DATETIME',
        'status': 'TEXT'
    }

    # Initialize ORM
    db = KatamariORM(schema_fields=schema_fields)

    # Create the aggregation engine
    aggregation = KatamariAggregation(db)

    # Example metric definition
    metrics_config = {
        "metrics": [
            {
                "name": "avg_response_time",
                "operation": "avg",
                "field": "processing_time",
                "filter": {
                    "field": "status",
                    "operator": "==",
                    "value": "success"
                }
            },
            {
                "name": "error_count",
                "operation": "count",
                "field": "log_level",
                "filter": {
                    "field": "log_level",
                    "operator": "==",
                    "value": "ERROR"
                }
            }
        ]
    }

    # Run the aggregation
    results = await aggregation.run_aggregations(metrics_config)

    # Output the results
    print(results)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Real-Time Aggregation Example

```python
async def real_time_example():
    schema_fields = {
        'log_level': 'TEXT',
        'processing_time': 'NUMERIC',
        'timestamp': 'DATETIME',
        'status': 'TEXT'
    }

    db = KatamariORM(schema_fields=schema_fields)
    aggregation = KatamariAggregation(db)

    metric_definition = {
        "operation": "avg",
        "field": "processing_time",
        "filter": {
            "field": "status",
            "operator": "==",
            "value": "success"
        }
    }

    # Simulate real-time pipeline data
    pipeline_data = [
        {"processing_time": 150, "status": "success"},
        {"processing_time": 200, "status": "success"},
        {"processing_time": 300, "status": "failed"}
    ]

    # Run the real-time aggregation
    result = await aggregation.run_real_time_aggregation(metric_definition, pipeline_data)
    print(result)

if __name__ == "__main__":
    asyncio.run(real_time_example())
```

---

## Conclusion

The **KatamariAggregation** module allows dynamic and flexible metric aggregations on both historical and real-time data. It integrates with **KatamariORM** for data storage and querying, supports complex filters, and offers the ability to handle real-time metrics

 through **KatamariPipelines**.

With this system, any metric can be dynamically defined and computed, making it suitable for logging systems, monitoring tools, and any other use case where real-time and historical data aggregation is needed.
