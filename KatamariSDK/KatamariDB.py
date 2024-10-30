import asyncio
import logging
import os
import tempfile
import time
import heapq
import contextlib
import threading
import struct
import sys
from collections import defaultdict
from typing import Any, Dict, Optional, List, Tuple
from datetime import datetime
import dateutil.parser
import uuid

import aiofiles
import orjson
import orjson as json
from cachetools import LRUCache
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import BOOLEAN, DATETIME, ID, KEYWORD, NUMERIC, Schema, TEXT
from whoosh.index import create_in, exists_in, open_dir
from whoosh.qparser import AndGroup, MultifieldParser
from whoosh.qparser.dateparse import DateParserPlugin
import mimetypes
import zlib
import zstandard as zstd
import base64
import hashlib
import portalocker
# Import platform-specific modules for file locking
if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl
logging.basicConfig(level=logging.INFO)

# ----------------------- Version Control (MVCC) Implementation -----------------------
class VersionedValue:
    def __init__(self, value, version, timestamp, transaction_id):
        self.value = value
        self.version = version
        self.timestamp = timestamp
        self.transaction_id = transaction_id

class KatamariMVCC:
    """A key-value store with Multi-Version Concurrency Control (MVCC)."""

    def __init__(self):
        self.store = defaultdict(list)  # Store multiple versions per key
        self.transactions = {}  # Active transactions with start timestamps
        self.lock = threading.Lock()

    def begin_transaction(self):
        """Start a new transaction."""
        tx_id = f"tx_{time.time_ns()}"  # Unique transaction ID using a timestamp
        self.transactions[tx_id] = time.time()  # Use a timestamp for snapshot isolation
        return tx_id

    def get(self, key: str, tx_id: Optional[str] = None) -> Optional[Any]:
        """Retrieve the most recent version visible to the transaction or the latest version if tx_id is None."""
        with self.lock:
            if key not in self.store:
                return None
            
            # If no transaction is provided, return the latest version of the key
            if tx_id is None:
                return self.store[key][-1].value if self.store[key] else None

            # Get the most recent version visible to the transaction
            transaction_start_time = self.transactions.get(tx_id, time.time())
            for version in reversed(self.store[key]):
                if version.timestamp <= transaction_start_time:
                    return version.value  # Return the value visible to this transaction
            return None

    def put(self, key: str, value: Any, tx_id: str):
        """Write a new version of the key."""
        new_version = VersionedValue(value, len(self.store[key]) + 1, time.time(), tx_id)
        with self.lock:
            self.store[key].append(new_version)

    def commit(self, tx_id: str):
        """Commit a transaction."""
        with self.lock:
            if tx_id in self.transactions:
                del self.transactions[tx_id]  # Transaction is no longer tracked


    def rollback(self, tx_id):
        """Rollback all changes made within a transaction."""
        if tx_id in self.transactions:
            for key, versions in self.transactions[tx_id].items():
                # Restore the previous version of each key in the transaction snapshot
                self.store[key] = versions
            del self.transactions[tx_id]  # Clear transaction snapshot

# ----------------------- FileProcessor Implementation -----------------------

class FileProcessor:
    """FileProcessor for compressing, encoding, and decompressing binary files."""

    DEFAULT_SUPPORTED_TYPES = ['text/json', 'application/pdf', 'image/gif', 'image/png', 'image/svg+xml', 'text/html', 'audio/mpeg', 'video/mp4']

    def __init__(self, compression_method="zlib", supported_types=None, compression_level=None):
        self.compression_method = compression_method
        self.supported_types = supported_types if supported_types else self.DEFAULT_SUPPORTED_TYPES
        self.compression_level = compression_level if compression_level else zlib.Z_DEFAULT_COMPRESSION

    def compress_data(self, data):
        if self.compression_method == "zlib":
            return zlib.compress(data, level=self.compression_level)
        elif self.compression_method == "zstandard":
            cctx = zstd.ZstdCompressor(level=self.compression_level)
            return cctx.compress(data)
        else:
            raise ValueError("Invalid compression method")

    def decompress_data(self, compressed_data):
        if self.compression_method == "zlib":
            return zlib.decompress(compressed_data)
        elif self.compression_method == "zstandard":
            dctx = zstd.ZstdDecompressor()
            return dctx.decompress(compressed_data)

    def encode_data(self, data):
        return base64.b64encode(data).decode('utf-8')

    def decode_data(self, encoded_data):
        return base64.b64decode(encoded_data)

    def calculate_checksum(self, data):
        sha256 = hashlib.sha256()
        sha256.update(data)
        return sha256.hexdigest()

    def process_value(self, value):
        """Process regular JSON value by converting it to binary and compressing."""
        value_data = orjson.dumps(value)
        compressed_data = self.compress_data(value_data)
        encoded_data = self.encode_data(compressed_data)
        checksum = self.calculate_checksum(compressed_data)
        return {
            "file_type": 'text/json',
            "binary_data": encoded_data,
            "checksum": checksum
        }

# ----------------------- Transaction Log Implementation -----------------------

class TransactionLog:
    """Transaction log for atomicity."""

    def __init__(self, log_file: str = 'transaction.log'):
        self.log_file = log_file

    async def write_log(self, transaction: Dict[str, Any]):
        """Write a transaction to the log asynchronously."""
        async with aiofiles.open(self.log_file, 'a') as log:
            await log.write(orjson.dumps(transaction).decode() + '\n')

    async def read_log(self) -> List[Dict[str, Any]]:
        """Read all transactions from the log asynchronously."""
        try:
            async with aiofiles.open(self.log_file, 'r') as log:
                transactions = await log.readlines()
                return [orjson.loads(tx) for tx in transactions]
        except FileNotFoundError:
            return []

    async def clear_log(self):
        """Clear the transaction log asynchronously."""
        async with aiofiles.open(self.log_file, 'w') as log:
            await log.truncate(0)

# ----------------------- KatamariDBM Implementation -----------------------

class KatamariDBM:
    """A robust, file-based key-value store with basic transaction support."""

    DATA_FILE_SUFFIX = '.dat'
    INDEX_FILE_SUFFIX = '.idx'
    WAL_FILE_SUFFIX = '.wal'

    def __init__(self, filename: str):
        self.filename = filename
        self.data_file = filename + self.DATA_FILE_SUFFIX
        self.index_file = filename + self.INDEX_FILE_SUFFIX
        self.wal_file = filename + self.WAL_FILE_SUFFIX
        self.lock = threading.Lock()
        self.index = {}
        self._load_index()
        self._recover_from_wal()

    def _load_index(self):
        """Load the index from the index file or rebuild it from the data file."""
        if os.path.exists(self.index_file):
            with open(self.index_file, 'rb') as idx_file:
                self.index = orjson.loads(idx_file.read())
        else:
            # Rebuild index from data file
            self.index = {}
            if os.path.exists(self.data_file):
                with open(self.data_file, 'rb') as data_f:
                    offset = 0
                    while True:
                        header = data_f.read(8)
                        if not header:
                            break
                        key_size, value_size = struct.unpack('>II', header)
                        key = data_f.read(key_size).decode()
                        data_f.seek(value_size, os.SEEK_CUR)
                        self.index[key] = offset
                        offset += 8 + key_size + value_size

    def _write_index(self):
        """Write the in-memory index to the index file."""
        with open(self.index_file, 'wb') as idx_file:
            idx_file.write(orjson.dumps(self.index))

    def _recover_from_wal(self):
        """Recover any incomplete transactions from the WAL file."""
        if os.path.exists(self.wal_file):
            with open(self.wal_file, 'rb') as wal_f, open(self.data_file, 'ab') as data_f:
                while True:
                    entry = wal_f.read(8)
                    if not entry:
                        break
                    key_size, value_size = struct.unpack('>II', entry)
                    key = wal_f.read(key_size).decode()
                    value = wal_f.read(value_size)
                    offset = data_f.tell()
                    data_f.write(entry)
                    data_f.write(key.encode())
                    data_f.write(value)
                    self.index[key] = offset
            os.remove(self.wal_file)
            self._write_index()

    def __getitem__(self, key: str) -> Any:
        """Retrieve an item by key."""
        if key not in self.index:
            raise KeyError(f"Key '{key}' not found.")
        offset = self.index[key]
        with self.lock, open(self.data_file, 'rb') as data_f:
            data_f.seek(offset)
            header = data_f.read(8)
            key_size, value_size = struct.unpack('>II', header)
            data_f.seek(key_size, os.SEEK_CUR)  # Skip the key
            value_data = data_f.read(value_size)
            value = orjson.loads(value_data)
            return value

    def __setitem__(self, key: str, value: Any):
        """Set an item by key."""
        value_data = orjson.dumps(value)
        key_data = key.encode()
        key_size = len(key_data)
        value_size = len(value_data)
        entry_header = struct.pack('>II', key_size, value_size)

        with self.lock:
            # Write to WAL first
            with open(self.wal_file, 'ab') as wal_f:
                portalocker.lock(wal_f, portalocker.LOCK_EX)  # Lock the WAL file
                wal_f.write(entry_header)
                wal_f.write(key_data)
                wal_f.write(value_data)
                wal_f.flush()
                os.fsync(wal_f.fileno())
                portalocker.unlock(wal_f)  # Unlock the WAL file after writing

            # Append to data file
            with open(self.data_file, 'ab') as data_f:
                portalocker.lock(data_f, portalocker.LOCK_EX)  # Lock the data file
                offset = data_f.tell()
                data_f.write(entry_header)
                data_f.write(key_data)
                data_f.write(value_data)
                data_f.flush()
                os.fsync(data_f.fileno())
                portalocker.unlock(data_f)  # Unlock the data file after writing

            # Update index
            self.index[key] = offset
            self._write_index()

            # Clear WAL
            with open(self.wal_file, 'wb') as wal_f:
                pass

    def __delitem__(self, key: str):
        """Delete an item by key."""
        if key not in self.index:
            raise KeyError(f"Key '{key}' not found.")

        with self.lock:
            del self.index[key]
            self._write_index()
            # Note: The data remains in the data file, but it's no longer referenced.

    def keys(self):
        """Return all keys."""
        return self.index.keys()
    def items(self):
        return self.index.items()

    def close(self):
        """Close the database (no action needed for this implementation)."""
        pass

# ----------------------- KatamariSearch (Search Integration) -----------------------

class KatamariSearch:
    """Search index integrated with MVCC."""
    
    def __init__(self, schema_fields: Optional[Dict[str, str]] = None, index_dir: Optional[str] = None):
        self.index_dir = index_dir or tempfile.mkdtemp()  # Use temporary directory for the index
        self.schema = self._create_schema(schema_fields)
        self.index = self._create_or_open_index()

    def _create_schema(self, fields: Dict[str, str]) -> Schema:
        """Create schema from fields."""
        schema_dict = {
            'id': ID(stored=True, unique=True),
            'timestamp': DATETIME(stored=True)
        }
        schema_dict.update({field_name: TEXT(stored=True) for field_name in fields.keys()})
        return Schema(**schema_dict)

    def _create_or_open_index(self):
        """Create or open the Whoosh index."""
        if not exists_in(self.index_dir):
            os.makedirs(self.index_dir, exist_ok=True)
            return create_in(self.index_dir, self.schema)
        else:
            return open_dir(self.index_dir)

    def _index_document(self, key, value, version, timestamp):
        """Immediately index a document after it's written."""
        with self.index.writer() as writer:
            document = {
                'id': key,
                'timestamp': datetime.utcfromtimestamp(timestamp),
                'version': version
            }
            document.update(value)
            writer.update_document(**document)

    async def search(self, query_str: str, tx_start_time: float, schema_fields: List[str]):
        """Search for documents with version-awareness (filter by timestamp)."""
        with self.index.searcher() as searcher:
            query = MultifieldParser(schema_fields, self.schema).parse(query_str)
            results = searcher.search(query, limit=None)
            
            # Filter results by transaction start time (version-awareness)
            filtered_results = [result for result in results if result['timestamp'] <= datetime.utcfromtimestamp(tx_start_time)]
            return filtered_results

    def close(self):
        """Close the index."""
        self.index.close()

# ----------------------- KatamariORM Implementation -----------------------

class KatamariORM:
    """Key-value store with ORM-like capabilities and file handling."""

    def __init__(
        self,
        schema_fields: Optional[Dict[str, str]] = None,
        cache_size: int = 1000,
        cache_ttl: int = 300,
        use_temp_index: bool = True,
        namespace: Optional[str] = None,
        database: str = None
    ):
        self.store: Dict[str, Any] = {}
        self.ttl_store: Dict[str, float] = {}
        self.use_temp_index = use_temp_index
        self.namespace = namespace
        self.database = database or os.path.join(os.getcwd(), 'default.db')  # Ensure default path
        self.running = True
        self.ttl_task: Optional[asyncio.Task] = None
        self.index_task: Optional[asyncio.Task] = None
        self.ttl_heap: List[Tuple[float, str]] = []
        self.ttl_event = asyncio.Event()
        self.locks = defaultdict(asyncio.Lock)
        self.transaction_log = TransactionLog()
        self.lru_cache = LRUCache(maxsize=cache_size)
        self.index_update_queue = asyncio.Queue()
        self.schema = self._create_schema(schema_fields) if schema_fields else self._create_default_schema()
        self.index_dir = self._create_index_dir()
        self.index = self._create_or_open_index()
        self.file_processor = FileProcessor()  # FileProcessor instance for handling files

    def _create_default_schema(self) -> Schema:
        """Create default schema."""
        return Schema(id=ID(stored=True, unique=True), content=TEXT(stored=True, analyzer=StemmingAnalyzer()))

    def _create_schema(self, fields: Dict[str, str]) -> Schema:
        """Create schema from fields."""
        schema_dict = {}
        for field_name, field_type in fields.items():
            if field_type == 'TEXT':
                schema_dict[field_name] = TEXT(stored=True, analyzer=StemmingAnalyzer(), phrase=True)  # Enable phrase search for TEXT
            elif field_type == 'KEYWORD':
                schema_dict[field_name] = TEXT(stored=True, analyzer=StemmingAnalyzer(), phrase=True)
            elif field_type == 'DATETIME':
                schema_dict[field_name] = DATETIME(stored=True)
            elif field_type == 'NUMERIC':
                schema_dict[field_name] = NUMERIC(stored=True)
            elif field_type == 'BOOLEAN':
                schema_dict[field_name] = BOOLEAN(stored=True)
            elif field_type == 'ID':
                schema_dict[field_name] = ID(stored=True, unique=True)
            else:
                raise ValueError(f"Unsupported field type: {field_type}")
        logging.info(f"Schema created with fields: {fields}")
        return Schema(**schema_dict)

    async def start(self):
        """Start background tasks."""
        self.ttl_task = asyncio.create_task(self._process_ttl())
        self.index_task = asyncio.create_task(self._process_index_updates())

    def _create_index_dir(self) -> str:
        """Create index directory."""
        if self.use_temp_index:
            index_dir = tempfile.mkdtemp()
        else:
            index_dir = os.path.join(os.getcwd(), f'katamari_index_{self.namespace or "default"}')
            os.makedirs(index_dir, exist_ok=True)
        logging.info(f"Index directory created at: {index_dir}")
        return index_dir

    def _create_or_open_index(self):
        """Create or open index."""
        if not exists_in(self.index_dir):
            logging.info("Creating new index...")
            return create_in(self.index_dir, self.schema)
        else:
            try:
                logging.info("Opening existing index...")
                return open_dir(self.index_dir)
            except Exception as e:
                logging.error(f"Failed to open index, creating new one. Error: {e}")
                return create_in(self.index_dir, self.schema)

    @contextlib.asynccontextmanager
    async def lock_key(self, key: str):
        """Asynchronous context manager for locking a key."""
        lock = self.locks[key]
        await lock.acquire()
        try:
            yield
        finally:
            lock.release()

    async def start_transaction(self, transaction_data: Dict[str, Any]):
        """Start a transaction and return a unique transaction ID."""
        transaction_id = str(uuid.uuid4())  # Generate a unique transaction ID
        transaction_data['transaction_id'] = transaction_id
        await self.transaction_log.write_log(transaction_data)
        return transaction_id  # Return the generated transaction ID

    async def commit_transaction(self):
        """Commit the transaction."""
        await self.transaction_log.clear_log()

    async def rollback_transaction(self):
        """Rollback the transaction."""
        transactions = await self.transaction_log.read_log()
        for tx in transactions:
            await self.__delitem__(tx['key'])
        await self.transaction_log.clear_log()

    def _format_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Helper function to format DATETIME fields to a readable string."""
        if value:
            return value.strftime("%Y-%m-%dT%H:%M:%S")
        return None

    async def set(self, key: str, value: Any, append: bool = False, ttl: Optional[int] = None):
        """Wrapper for setting a value."""
        # Ensure created_at is converted to datetime object
        if 'created_at' in value and isinstance(value['created_at'], str):
            try:
                value['created_at'] = dateutil.parser.parse(value['created_at'])
            except ValueError as e:
                logging.error(f"Error parsing date field 'created_at': {e}")
        
        # Check if the value contains a file path and handle with FileProcessor
        if isinstance(value, dict) and value.get('file_path'):
            file_info = self.file_processor.process_file(value['file_path'])
            value['file_info'] = json.loads(file_info)
            del value['file_path']
        else:
            # Default to processing JSON values as text/json
            file_info = self.file_processor.process_value(value)
            value['file_info'] = file_info

        await self.__setitem__(key, value, append=append, ttl=ttl)

    async def search(
        self,
        query_str: str,
        sort_by: Optional[str] = None,
        cluster_by: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search the index dynamically based on schema fields."""
        # Get all field names from the schema
        searchable_fields = list(self.schema.names())

        if not searchable_fields:
            logging.error("No searchable fields found in the schema.")
            return []

        with self.index.searcher() as searcher:
            # Use dynamically generated searchable fields
            parser = MultifieldParser(searchable_fields, self.index.schema, group=AndGroup)
            parser.add_plugin(DateParserPlugin())  # Adding DateParserPlugin for handling dates
            query = parser.parse(query_str)
            results = searcher.search(query, limit=None)

            search_results = []
            for result in results:
                try:
                    # Dynamically retrieve all fields from the result
                    matches = {}
                    for field in searchable_fields:
                        value = result.get(field)

                        # If the field is a DATETIME, format it using the helper function
                        if isinstance(self.schema[field], DATETIME):
                            value = self._format_datetime(value)

                        matches[field] = value

                    search_results.append({"id": result["id"], "matches": matches})
                except orjson.JSONDecodeError:
                    logging.error(f"Error parsing matches for result: {result}")

            # Apply filters if provided
            if filters:
                search_results = self._apply_filters(search_results, filters)

            # Sort results if a sort field is provided
            if sort_by:
                search_results = self._sort_by_field(search_results, sort_by)

            # Cluster results if a cluster field is provided
            if cluster_by:
                search_results = self._cluster_by_field(search_results, cluster_by)

            return search_results

    async def __setitem__(self, key: str, value: Any, append: bool = False, ttl: Optional[int] = None):
        """Set a value in the store with optional TTL."""


        current_time = time.time()
        transaction_data = {'key': key, 'value': value, 'ttl': ttl}

        async with self.lock_key(key):
            try:
                await self.start_transaction(transaction_data)

                if key in self.ttl_store and current_time > self.ttl_store[key]:
                    await self.__delitem__(key)

                if key in self.store:
                    existing_value = self.store[key]
                    if append and isinstance(existing_value, list):
                        existing_value += value
                        self.store[key] = existing_value
                    elif existing_value != value:
                        self.store[key] = value
                else:
                    self.store[key] = value

                self.lru_cache[key] = self.store[key]

                if ttl:
                    expire_time = current_time + ttl
                    self.ttl_store[key] = expire_time
                    heapq.heappush(self.ttl_heap, (expire_time, key))
                    self.ttl_event.set()
                else:
                    if key in self.ttl_store:
                        del self.ttl_store[key]

                await self._update_index(key, self.store[key])

                await self.commit_transaction()

            except Exception as e:
                logging.error(f"Error during transaction for key '{key}': {e}")
                await self.rollback_transaction()

    async def __getitem__(self, key: str) -> Optional[Any]:
        """Get a value from the store."""
        current_time = time.time()
        if key in self.ttl_store and current_time > self.ttl_store[key]:
            await self.__delitem__(key)
            return None

        if key in self.lru_cache:
            return self.lru_cache[key]

        value = self.store.get(key)
        if value:
            self.lru_cache[key] = value
        return value

    async def __delitem__(self, key: str):
        """Delete a key from the store."""
        async with self.lock_key(key):
            if key in self.store:
                del self.store[key]
                await self._delete_from_index(key)
            if key in self.ttl_store:
                del self.ttl_store[key]
            if key in self.lru_cache:
                del self.lru_cache[key]

    async def _update_index(self, key: str, value: Any):
        """Queue an update for the index."""
        await self.index_update_queue.put(('update', key, value))

    async def _delete_from_index(self, key: str):
        """Queue a deletion from the index."""
        await self.index_update_queue.put(('delete', key, None))

    async def _process_index_updates(self):
        """Process index updates in a background task."""
        while self.running:
            try:
                updates = []
                # Wait for at least one update
                action, key, value = await self.index_update_queue.get()
                updates.append((action, key, value))
                # Get other pending updates
                while not self.index_update_queue.empty():
                    action, key, value = await self.index_update_queue.get()
                    updates.append((action, key, value))

                # Dynamically update documents for all schema fields
                with self.index.writer() as writer:
                    for action, key, value in updates:
                        if action == 'update':
                            document = {'id': key}  # Start with the key as the ID
                            for field_name in self.schema.names():
                                if field_name in value:
                                    document[field_name] = value[field_name]
                            writer.update_document(**document)
                        elif action == 'delete':
                            writer.delete_by_term('id', key)
                # Mark tasks as done
                for _ in updates:
                    self.index_update_queue.task_done()
            except Exception as e:
                logging.error(f"Error processing index updates: {e}")

    async def _process_ttl(self):
        """Process TTL expirations."""
        while self.running:
            if not self.ttl_heap:
                self.ttl_event.clear()
                await self.ttl_event.wait()
                continue

            expire_time, key = self.ttl_heap[0]
            now = time.time()
            sleep_time = expire_time - now
            if sleep_time > 0:
                try:
                    await asyncio.wait_for(self.ttl_event.wait(), timeout=sleep_time)
                    continue
                except asyncio.TimeoutError:
                    pass

            # Time to expire the key
            heapq.heappop(self.ttl_heap)
            if key in self.ttl_store and self.ttl_store[key] == expire_time:
                await self.__delitem__(key)

    def close(self):
        """Gracefully close the store."""
        self.running = False

    def items(self):
        """Return an iterator over the key-value pairs in the store."""
        return self.store.items()
    
    def keys(self):
        """Return an iterator over the key-value pairs in the store."""
        return self.store.keys()

