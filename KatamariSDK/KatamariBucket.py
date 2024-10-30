import os
import hashlib
import aiofiles
from datetime import datetime
from typing import Optional, Dict, Any
from KatamariSDK.KatamariDB import KatamariMVCC, FileProcessor


class KatamariBucket:
    """KatamariBucket: A storage system for files and binary objects with versioning, compression, and encryption support."""

    def __init__(self, bucket_name: str, storage_path: str = './storage', compression: str = 'zlib', enable_versioning: bool = True):
        """
        Initialize the KatamariBucket.

        :param bucket_name: Name of the bucket.
        :param storage_path: Path where the bucket's files will be stored.
        :param compression: Compression method ('zlib', 'zstandard', or None).
        :param enable_versioning: Whether versioning is enabled.
        """
        self.bucket_name = bucket_name
        self.storage_path = os.path.join(storage_path, bucket_name)
        self.enable_versioning = enable_versioning
        self.mvcc = KatamariMVCC()  # Leverage KatamariMVCC for consistency and versioning
        self.file_processor = FileProcessor(compression_method=compression)  # FileProcessor for handling compression

        # Create storage directory for the bucket if it doesn't exist
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)

    def _generate_file_path(self, key: str, version: Optional[int] = None) -> str:
        """
        Generate the file path for the stored object, supporting versioning.

        :param key: The key (or filename) for the stored object.
        :param version: The version number (if versioning is enabled).
        :return: The full path to the file.
        """
        if version is not None and self.enable_versioning:
            return os.path.join(self.storage_path, f"{key}_v{version}")
        return os.path.join(self.storage_path, key)

    def _get_latest_version(self, key: str) -> int:
        """
        Retrieve the latest version number for a key.

        :param key: The key for the object.
        :return: The latest version number.
        """
        versions = [int(file.split('_v')[-1]) for file in os.listdir(self.storage_path) if file.startswith(key + "_v")]
        return max(versions) if versions else 0

    async def put(self, key: str, value: bytes, metadata: Optional[Dict] = None) -> str:
        """
        Store a file in the bucket with optional versioning, compression, and metadata.

        :param key: The key (or filename) for the stored object.
        :param value: The file content as bytes.
        :param metadata: Optional metadata associated with the file.
        :return: The checksum of the stored file.
        """
        tx_id = self.mvcc.begin_transaction()

        # Process the file (compression, checksum, etc.)
        processed_file = self.file_processor.process_value(value)
        file_data = processed_file['binary_data']  # Encoded and compressed binary data
        checksum = processed_file['checksum']

        # Get the latest version if versioning is enabled
        version = self._get_latest_version(key) + 1 if self.enable_versioning else None
        file_path = self._generate_file_path(key, version)

        # Write the file to disk
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_data.encode())  # Write compressed and encoded data

        # Store metadata and version information in KatamariDB (using MVCC)
        metadata_entry = {
            "key": key,
            "version": version if self.enable_versioning else 1,
            "checksum": checksum,
            "file_path": file_path,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.mvcc.put(key, metadata_entry, tx_id)

        self.mvcc.commit(tx_id)
        return checksum  # Return the checksum as a validation of the uploaded content

    async def get(self, key: str, version: Optional[int] = None) -> Optional[bytes]:
        """
        Retrieve a file from the bucket, optionally retrieving a specific version.

        :param key: The key (or filename) for the stored object.
        :param version: The version number to retrieve (if versioning is enabled).
        :return: The file content as bytes.
        """
        tx_id = self.mvcc.begin_transaction()

        # Retrieve metadata from the KatamariDB
        metadata_entry = self.mvcc.get(key, tx_id)
        if not metadata_entry:
            raise FileNotFoundError(f"File with key '{key}' not found.")

        # Determine which version to retrieve (latest or specified)
        file_version = version or metadata_entry['version']
        file_path = self._generate_file_path(key, file_version)

        # Read the file from disk
        async with aiofiles.open(file_path, 'rb') as f:
            file_data = await f.read()

        # Decompress and decode the file data
        decoded_data = self.file_processor.decode_data(file_data)
        decompressed_data = self.file_processor.decompress_data(decoded_data)

        return decompressed_data

    async def delete(self, key: str, version: Optional[int] = None):
        """
        Delete a file or a specific version of a file from the bucket.

        :param key: The key (or filename) for the stored object.
        :param version: The version number to delete (if versioning is enabled).
        """
        tx_id = self.mvcc.begin_transaction()

        # Retrieve the metadata to find the correct file path
        metadata_entry = self.mvcc.get(key, tx_id)
        if not metadata_entry:
            raise FileNotFoundError(f"File with key '{key}' not found.")

        # Determine which version to delete
        file_version = version or metadata_entry['version']
        file_path = self._generate_file_path(key, file_version)

        # Remove the file from disk
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            raise FileNotFoundError(f"File with key '{key}' and version '{file_version}' not found.")

        # If no specific version is provided, remove the metadata entry completely
        if version is None:
            self.mvcc.put(key, {}, tx_id)  # Clear metadata entry
        else:
            # Update metadata to remove only the specified version
            # Custom logic to adjust versions can be added here
            pass

        self.mvcc.commit(tx_id)

    def list_files(self) -> Dict[str, Any]:
        """
        List all files and their metadata in the bucket.

        :return: A dictionary containing all the files and their metadata.
        """
        tx_id = self.mvcc.begin_transaction()
        all_files = {}
        for key, metadata in self.mvcc.store.items():
            all_files[key] = metadata
        return all_files

