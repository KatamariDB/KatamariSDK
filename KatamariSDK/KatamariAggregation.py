import asyncio
from typing import Any, Dict, List, Optional
import logging
from KatamariSDK.KatamariDB import *
from KatamariSDK.KatamariPipelines import PipelineModel

logger = logging.getLogger('KatamariAggregation')

class KatamariAggregation:
    """
    A dynamic metric aggregation engine that runs on top of KatamariORM and KatamariMVCC.
    Supports real-time and historical aggregation, custom metrics, and querying with filters.
    """

    def __init__(self, db: KatamariORM):
        self.db = db
        self.aggregations = {
            "sum": self.sum_aggregation,
            "avg": self.avg_aggregation,
            "count": self.count_aggregation,
            "min": self.min_aggregation,
            "max": self.max_aggregation
        }

    async def run_metric(self, metric_definition: Dict[str, Any]) -> Any:
        """
        Run a metric based on the provided definition.
        :param metric_definition: A dictionary that defines the metric (operation, field, filters).
        :return: The result of the aggregation.
        """
        operation = metric_definition.get("operation")
        field = metric_definition.get("field")
        filter_condition = metric_definition.get("filter")

        # Fetch data and apply filter if provided
        data = await self.fetch_filtered_data(field, filter_condition)

        # Find the correct aggregation function dynamically
        aggregation_func = self.aggregations.get(operation)
        if aggregation_func:
            return await aggregation_func(field, data)

        raise ValueError(f"Unsupported aggregation operation: {operation}")

    async def fetch_filtered_data(self, field: str, filter_condition: Optional[Dict[str, Any]]) -> List[Any]:
        """
        Fetch data from the database with optional filtering.
        :param field: The field to fetch data from.
        :param filter_condition: An optional filter for data (e.g., filter logs by level).
        :return: List of field values that match the filter.
        """
        data = []
        items = await self.db.items()  # Fetch from ORM

        for _, item in items:
            if filter_condition:
                field_value = item.get(filter_condition['field'])
                if not self.apply_filter(field_value, filter_condition):
                    continue

            data.append(item.get(field))

        return data

    def apply_filter(self, field_value: Any, filter_condition: Dict[str, Any]) -> bool:
        """
        Apply a filter to a field value.
        :param field_value: The value of the field to be filtered.
        :param filter_condition: The filter condition.
        :return: Whether the field value passes the filter.
        """
        operator = filter_condition.get("operator")
        value = filter_condition.get("value")

        if operator == "==":
            return field_value == value
        elif operator == "!=":
            return field_value != value
        # Add more operators as needed
        return False

    async def sum_aggregation(self, field: str, data: List[Any]) -> float:
        """Sum the field values."""
        return sum(data)

    async def avg_aggregation(self, field: str, data: List[Any]) -> float:
        """Calculate the average of the field values."""
        return sum(data) / len(data) if data else None

    async def count_aggregation(self, field: str, data: List[Any]) -> int:
        """Count the number of occurrences of the field."""
        return len(data)

    async def min_aggregation(self, field: str, data: List[Any]) -> Any:
        """Get the minimum value of the field."""
        return min(data)

    async def max_aggregation(self, field: str, data: List[Any]) -> Any:
        """Get the maximum value of the field."""
        return max(data)

    async def run_aggregations(self, metrics_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run all metrics defined in the configuration.
        :param metrics_config: A dictionary defining all metrics to be run.
        :return: A dictionary of results for each metric.
        """
        results = {}
        for metric in metrics_config['metrics']:
            result = await self.run_metric(metric)
            results[metric['name']] = result
        return results

    async def run_real_time_aggregation(self, metric_definition: Dict[str, Any], pipeline_data: List[Dict[str, Any]]) -> Any:
        """
        Run real-time metrics on streaming data.
        :param metric_definition: The metric definition for real-time aggregation.
        :param pipeline_data: The incoming streaming data.
        :return: The aggregation result for real-time data.
        """
        # Instead of fetching from KatamariDB, you process data directly from the pipeline
        data = [item.get(metric_definition['field']) for item in pipeline_data]

        aggregation_func = self.aggregations.get(metric_definition['operation'])
        if aggregation_func:
            return await aggregation_func(metric_definition['field'], data)

        raise ValueError(f"Unsupported aggregation operation: {metric_definition['operation']}")

# Example of integrating KatamariAggregation with KatamariORM
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

