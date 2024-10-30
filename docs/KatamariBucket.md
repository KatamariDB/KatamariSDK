# KatamariBucket

**KatamariBucket** is a flexible and scalable storage system built on top of **KatamariMVCC**. It is designed to handle large binary objects (blobs), files, and other types of data with support for versioning, compression, metadata management, and secure storage. By leveraging **KatamariDB's** transactional capabilities, **KatamariBucket** ensures consistency and reliability in all operations.

## Key Features

1. **File Storage with Versioning**:
   - Automatically store and manage different versions of files.
   - Retrieve specific versions of files when needed.

2. **Compression**:
   - Supports **zlib** and **zstandard** compression methods to save storage space.
   - Files are compressed during upload and decompressed when retrieved.

3. **Metadata Support**:
   - Attach and store metadata with each file (e.g., file descriptions, user information, upload timestamps).

4. **Transaction Consistency with MVCC**:
   - Built on **KatamariMVCC** for multi-version concurrency control.
   - Ensures safe, consistent transactions even in a distributed environment.

5. **Checksum Verification**:
   - Automatically calculate and store file checksums during upload.
   - Verifies data integrity by returning checksums for validation.

6. **File Deletion**:
   - Supports deleting specific versions of a file or the entire file.

7. **List Files**:
   - List all files stored in the bucket along with their associated metadata.

---

## Installation

### Dependencies

- Python 3.8+
- Required Python libraries:
  ```bash
  pip install aiofiles zstandard orjson
  ```

You must also have **KatamariDB** installed for the **KatamariMVCC** and **FileProcessor** components.

### Getting Started

Clone the **KatamariBucket** repository and integrate it into your project:

```bash
git clone https://github.com/gddisney/katamari.git
```

## Example Usage

### Initializing the Bucket

```python
from KatamariBucket import KatamariBucket

# Initialize the KatamariBucket
bucket = KatamariBucket("my_bucket", compression="zlib")
```

### Uploading a File

```python
# Upload a file with optional metadata
await bucket.put("file1", b"Some binary content", metadata={"description": "Test file"})
```

### Retrieving a File

```python
# Retrieve the latest version of the file
file_content = await bucket.get("file1")
print(file_content)

# Retrieve a specific version of the file
older_file_content = await bucket.get("file1", version=1)
print(older_file_content)
```

### Deleting a File

```python
# Delete the latest version of the file
await bucket.delete("file1")

# Delete a specific version of the file
await bucket.delete("file1", version=1)
```

### Listing All Files

```python
# List all files in the bucket
all_files = bucket.list_files()
print(all_files)
```

---

## Use Cases

### 1. **Backup and Restore System**
   **Scenario**: A company needs a reliable backup solution for critical data, where different versions of the same file (e.g., daily backups) need to be stored, retrieved, and possibly rolled back in case of data corruption or failure.
   
   **KatamariBucket** can store backups with versioning enabled, allowing the company to easily retrieve a previous version if needed. The built-in **checksum validation** ensures data integrity, ensuring that stored backups are not corrupted during transmission or storage.

### 2. **File Version Control for Application Assets**
   **Scenario**: A development team needs to manage multiple versions of assets like images, configuration files, or scripts for an application.
   
   **KatamariBucket** allows developers to store different versions of files, such as configuration scripts or UI assets, with the ability to retrieve older versions. Versioned assets help teams track changes over time, making debugging and rollback easy.

### 3. **User-Generated Content (UGC) Storage with Metadata**
   **Scenario**: A social media platform needs to manage user-uploaded content such as images and videos.
   
   **KatamariBucket** supports storing user-uploaded files along with metadata like user IDs, tags, and upload timestamps. Versioning ensures that when users upload a new version of a document or image, the previous versions are still retrievable if needed.

### 4. **Secure Encrypted File Storage for Sensitive Data**
   **Scenario**: A financial institution needs to store sensitive documents like bank statements securely.
   
   **KatamariBucket** can be configured to use **encryption** for secure storage. Files are encrypted before being written to disk, and the encrypted content can be decrypted only with the correct key upon retrieval. This ensures that sensitive data remains secure and compliant with regulations.

---

## API Reference

### `KatamariBucket(bucket_name: str, storage_path: str = './storage', compression: str = 'zlib', enable_versioning: bool = True)`

- **bucket_name**: The name of the bucket for organizing stored files.
- **storage_path**: Directory where the bucket's files are stored. Default is `./storage`.
- **compression**: Compression method to use. Options are `'zlib'`, `'zstandard'`, or `None` (no compression).
- **enable_versioning**: Enable or disable versioning for the stored files.

### `async def put(key: str, value: bytes, metadata: Optional[Dict] = None) -> str`
Stores a file with optional metadata and returns a checksum.

- **key**: The key (filename) for the stored file.
- **value**: The file content as a byte string.
- **metadata**: (Optional) A dictionary of metadata to associate with the file.
  
### `async def get(key: str, version: Optional[int] = None) -> Optional[bytes]`
Retrieves the latest or specified version of a file from the bucket.

- **key**: The key (filename) of the file to retrieve.
- **version**: (Optional) The version number to retrieve. If not provided, retrieves the latest version.

### `async def delete(key: str, version: Optional[int] = None)`
Deletes a file or a specific version of a file from the bucket.

- **key**: The key (filename) of the file to delete.
- **version**: (Optional) The version number to delete. If not provided, deletes the entire file.

### `def list_files() -> Dict[str, Any]`
Lists all files in the bucket, along with their metadata (e.g., version, checksum, timestamp).

---

## License

This project is licensed under the [MIT License](LICENSE).

## Contribution

We welcome contributions to **KatamariBucket**. Please check the [CONTRIBUTING](CONTRIBUTING.md) guide for details on how to contribute to this project.

---

**KatamariBucket** provides a robust, scalable, and flexible solution for file storage with versioning, compression, and transactional consistency. It integrates smoothly with the **Katamari Ecosystem**, making it a perfect fit for modern, data-driven applications.
