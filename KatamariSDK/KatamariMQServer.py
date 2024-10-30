import asyncio
import websockets
import json
import logging
from datetime import datetime
from KatamariSDK.KatamariDB import KatamariDBM
from KatamariSDK.KatamariDB import KatamariMVCC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KatamariMQServer')


class KatamariMQServer(KatamariMVCC):
    """
    KatamariMQServer manages:
    - Distributing pipelines across workers.
    - Sending lambda functions to workers.
    - Sharding data and clustering it for efficient processing.
    - Tracking job states and workloads using KatamariMVCC and KatamariDBM.
    """

    def __init__(self, db_filename='katamari_mq.db'):
        super().__init__()
        self.db = KatamariDBM(db_filename)
        self.workers = {}  # Stores worker_id -> {'workload': int, 'last_heartbeat': timestamp, 'websocket': ws}
        self.jobs_queue = asyncio.Queue()  # Queue to hold jobs to be dispatched
        self.worker_data_shards = {}  # Maps worker_id to data shards assigned for parallel processing

    async def register_worker(self, websocket, worker_id: str):
        """
        Register a new worker and store its state in the KatamariDBM.
        """
        tx_id = self.begin_transaction()
        self.workers[worker_id] = {
            'workload': 0,
            'last_heartbeat': datetime.now(),
            'websocket': websocket
        }
        # Store worker details in the database
        self.db[worker_id] = {'worker_id': worker_id, 'workload': 0, 'registered_at': str(datetime.now())}
        self.commit(tx_id)

        logger.info(f"Worker {worker_id} registered.")

    async def update_heartbeat(self, worker_id: str, workload: int):
        """
        Update the heartbeat from a worker, including its workload, and store it in the database.
        """
        if worker_id in self.workers:
            self.workers[worker_id]['workload'] = workload
            self.workers[worker_id]['last_heartbeat'] = datetime.now()

            tx_id = self.begin_transaction()
            # Update worker state in the database
            self.db[worker_id] = {'worker_id': worker_id, 'workload': workload, 'last_heartbeat': str(datetime.now())}
            self.commit(tx_id)

            logger.info(f"Updated heartbeat for {worker_id}: workload={workload}")

    async def shard_data(self, data: list, num_shards: int) -> list:
        """
        Shard data into smaller pieces based on the number of available workers or specified shards.
        """
        shard_size = len(data) // num_shards
        shards = [data[i:i + shard_size] for i in range(0, len(data), shard_size)]
        return shards

    async def assign_shards(self, job_data: dict):
        """
        Assign data shards to workers based on their current workload.
        Each shard is a portion of the data that will be processed in parallel by the workers.
        """
        if self.workers:
            shards = await self.shard_data(job_data['data'], len(self.workers))
            workers_sorted_by_workload = sorted(self.workers.keys(), key=lambda w: self.workers[w]['workload'])

            # Assign each shard to the least loaded workers
            for i, shard in enumerate(shards):
                worker_id = workers_sorted_by_workload[i % len(workers_sorted_by_workload)]
                shard_key = f"shard_{job_data['job_id']}_{i}"

                # Store the shard in the database
                self.db[shard_key] = {'shard_data': shard, 'assigned_to': worker_id}

                # Send shard details to the worker
                await self.send_job_to_worker(worker_id, {'job_id': job_data['job_id'], 'shard_key': shard_key})

                # Track shard assignment
                if worker_id not in self.worker_data_shards:
                    self.worker_data_shards[worker_id] = []
                self.worker_data_shards[worker_id].append(shard_key)

                logger.info(f"Assigned shard {shard_key} to worker {worker_id}")

    async def send_job_to_worker(self, worker_id: str, job_data: dict):
        """
        Send a job or shard to a specific worker.
        """
        worker = self.workers.get(worker_id)
        if worker:
            websocket = worker['websocket']
            await websocket.send(json.dumps(job_data))
            logger.info(f"Sent job {job_data['job_id']} to worker {worker_id}")

    async def dispatch_pipeline(self, pipeline_data: dict):
        """
        Dispatch a pipeline job to workers.
        """
        job_data = {
            'type': 'pipeline',
            'pipeline_id': pipeline_data['pipeline_id'],
            'jobs': pipeline_data['jobs']
        }
        await self.assign_shards(job_data)

    async def dispatch_lambda(self, lambda_data: dict):
        """
        Dispatch a Lambda function to workers for execution.
        """
        job_data = {
            'type': 'lambda',
            'function_name': lambda_data['function_name'],
            'environment': lambda_data.get('environment', {}),
            'timeout_seconds': lambda_data.get('timeout_seconds', 300),
            'memory_limit': lambda_data.get('memory_limit', 128)
        }
        # Send the Lambda job to the least loaded worker
        least_loaded_worker = min(self.workers, key=lambda w: self.workers[w]['workload'])
        await self.send_job_to_worker(least_loaded_worker, job_data)

    async def receive_messages(self, websocket, worker_id: str):
        """
        Receive messages from a worker (such as heartbeats, job completion).
        """
        async for message in websocket:
            data = json.loads(message)

            # Handle heartbeats
            if 'workload' in data:
                await self.update_heartbeat(worker_id, data['workload'])

            # Handle job completion (if necessary)
            if 'job_completed' in data:
                job_id = data['job_completed']
                logger.info(f"Worker {worker_id} completed job {job_id}")

    async def handle_worker(self, websocket, path):
        """
        Handle new worker connections.
        """
        worker_id = await websocket.recv()
        await self.register_worker(websocket, worker_id)
        await self.receive_messages(websocket, worker_id)

    async def start(self):
        """
        Start the WebSocket server to accept worker connections.
        """
        server = await websockets.serve(self.handle_worker, "localhost", 8765)
        logger.info("KatamariMQServer started on ws://localhost:8765")
        await server.wait_closed()


# ----------------------- Running the KatamariMQServer -----------------------

async def main():
    server = KatamariMQServer(db_filename='katamari_mq.db')
    await server.start()

if __name__ == "__main__":
    asyncio.run(main())

