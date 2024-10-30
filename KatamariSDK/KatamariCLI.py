# cli.py
import argparse
import asyncio
from KatamariSDK.KatamariDB import KatamariORM, KatamariMVCC
from KatamariSDK.KatamariPipelines import PipelineManager
from KatamariSDK.KatamariAggregation import KatamariAggregation
from KatamariSDK.KatamariIAM import KatamariIAM
from KatamariSDK.KatamariLambda import KatamariLambdaFunction

# Define async wrapper for running async commands from the CLI
def async_command(command):
    asyncio.run(command)

def main():
    parser = argparse.ArgumentParser(
        description="Katamari CLI - Command-line interface for managing the Katamari ecosystem"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: katamari-cli query
    query_parser = subparsers.add_parser("query", help="Run a database query")
    query_parser.add_argument("query", type=str, help="Query to run on KatamariDB")

    # Command: katamari-cli pipeline
    pipeline_parser = subparsers.add_parser("pipeline", help="Manage pipelines")
    pipeline_parser.add_argument("action", choices=["start", "stop", "list"], help="Pipeline action")

    # Command: katamari-cli aggregate
    aggregate_parser = subparsers.add_parser("aggregate", help="Run data aggregation")
    aggregate_parser.add_argument(
        "metric", type=str, help="Metric name for aggregation"
    )
    aggregate_parser.add_argument(
        "--start_date", type=str, help="Start date for aggregation (YYYY-MM-DD)"
    )
    aggregate_parser.add_argument(
        "--end_date", type=str, help="End date for aggregation (YYYY-MM-DD)"
    )

    # Command: katamari-cli auth
    auth_parser = subparsers.add_parser("auth", help="Manage user authentication")
    auth_parser.add_argument(
        "username", type=str, help="Username to authenticate"
    )
    auth_parser.add_argument(
        "action", choices=["login", "logout", "status"], help="Authentication action"
    )

    # Command: katamari-cli lambda
    lambda_parser = subparsers.add_parser("lambda", help="Invoke a Lambda function")
    lambda_parser.add_argument(
        "function_name", type=str, help="Name of the Lambda function to invoke"
    )

    args = parser.parse_args()

    # Command logic
    if args.command == "query":
        async_command(KatamariORM.search(args.query))

    elif args.command == "pipeline":
        manager = PipelineManager()
        if args.action == "start":
            async_command(manager.start_pipeline())
        elif args.action == "stop":
            async_command(manager.stop_pipeline())
        elif args.action == "list":
            async_command(manager.list_pipelines())

    elif args.command == "aggregate":
        aggregator = KatamariAggregate()
        async_command(
            aggregator.run_aggregation(
                metric=args.metric, start_date=args.start_date, end_date=args.end_date
            )
        )

    elif args.command == "auth":
        iam = KatamariIAM()
        if args.action == "login":
            async_command(iam.login(args.username))
        elif args.action == "logout":
            async_command(iam.logout(args.username))
        elif args.action == "status":
            async_command(iam.status(args.username))

    elif args.command == "lambda":
        lambda_func = KatamariLambdaFunction(args.function_name)
        async_command(lambda_func.invoke())

if __name__ == "__main__":
    main()

