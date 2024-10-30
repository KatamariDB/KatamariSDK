import asyncio
import websockets
import json
import logging
from KatamariSDK.KatamariDB import KatamariDBM
from KatamariSDK.KatamariDB import KatamariMVCC
from KatamariSDK.KatamariPipelines import JobModel, PipelineModel
from KatamariSDK.KatamariLambda import KatamariLambdaFunction

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('WorkerNode')


class WorkerNode(KatamariMVCC):
    """
    WorkerNode processes jobs and Lambda functions, sends heartbeats to the MQ server, and tracks job state using MVCC.
    """

    def __init__(self, node_id: str, server_uri: str):
        super().__init__()
        self.node_id = node_id
        self.server_uri = server_uri
        self.workload = 0
        self.db = KatamariDBM(f"{self.node_id}_db.db")  # Each worker has its own local DB

    async def process_pipeline_job(self, job_data: dict):
        """
        Process a pipeline job using KatamariPipelines' JobModel and track state with MVCC.
        """
        job_name = job_data['job_name']
        pipeline_id = job_data['pipeline_id']
        schedule = job_data.get('schedule')

        tx_id = self.begin_transaction()
        job = JobModel(pipeline_id=pipeline_id, name=job_name, schedule=schedule)

        logger.info(f"Worker {self.node_id} processing pipeline job: {job_name}")
        job.state_machine.set_state('Running')
        await job.save_job(tx_id)  # Save job state as Running
        await asyncio.sleep(2)  # Simulate job execution

        job.state_machine.set_state('Completed')
        await job.save_job(tx_id)  # Save job state as Completed
        self.commit(tx_id)

        logger.info(f"Job {job_name} completed by worker {self.node_id}.")

    async def process_lambda_function(self, function_data: dict):
        """
        Process a Lambda function using KatamariLambdaFunction.
        """
        function_name = function_data['function_name']
        environment = function_data.get('environment', {})
        timeout_seconds = function_data.get('timeout_seconds', 300)
        memory_limit = function_data.get('memory_limit', 128)

        # Instantiate Lambda function
        lambda_function = KatamariLambdaFunction(
            name=function_name,
            handler=self.lambda_handler,
            environment=environment,
            timeout_seconds=timeout_seconds,
            memory_limit=memory_limit,
        )

        logger.info(f"Worker {self.node_id} processing Lambda function: {function_name}")

        # Invoke the Lambda function
        await lambda_function.invoke()

    async def lambda_handler(self, event=None, context=None):
        """
        Simulated Lambda handler.
        """
        logger.info(f"Lambda function executed with event: {event}")
        await asyncio.sleep(1)  # Simulate Lambda execution
        logger.info(f"Lambda function completed!")

    async def process_job(self, job):
        """
        Process a received job based on its type (pipeline or lambda).
        """
        if job.get('type') == 'pipeline':
            await self.process_pipeline_job(job)
        elif job.get('type') == 'lambda':
            await self.process_lambda_function(job)
        elif job.get('shard_key'):
            shard_data = self.db[job['shard_key']]['shard_data']
            logger.info(f"Processing shard {job['shard_key']} by worker {self.node_id}")
            await asyncio.sleep(1)  # Simulate shard processing
        else:
            logger.error(f"Unknown job type received by worker {self.node_id}: {job}")

    async def start(self):
        """
        Start the worker node and connect to the MQ server.
        """
        async with websockets.connect(self.server_uri) as websocket:
            logger.info(f"Worker {self.node_id} connected to server at {self.server_uri}")

            # Send initial registration data
            registration_data = json.dumps({'worker_id': self.node_id, 'workload': self.workload})
            await websocket.send(registration_data)

            # Start sending heartbeats and listening for jobs
            await asyncio.gather(self.send_heartbeat(websocket), self.receive_jobs(websocket))

    async def send_heartbeat(self, websocket):
        """
        Periodically send heartbeats to the server with the current workload.
        """
        while True:
            heartbeat = json.dumps({'worker_id': self.node_id, 'workload': self.workload})
            await websocket.send(heartbeat)
            logger.info(f"Sent heartbeat: worker_id={self.node_id}, workload={self.workload}")
            await asyncio.sleep(5)  # Send heartbeat every 5 seconds

    async def receive_jobs(self, websocket):
        """
        Receive jobs from the server and process them based on the job type.
        """
        async for message in websocket:
            job = json.loads(message)
            self.workload += 1  # Increase workload
            await self.process_job(job)
            self.workload -= 1  # Decrease workload after processing the job


# ----------------------- Running the WorkerNode -----------------------

async def main():
    worker = WorkerNode(node_id="worker_1", server_uri="ws://localhost:8765")
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())

