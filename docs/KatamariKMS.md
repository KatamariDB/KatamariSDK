# KatamariKMS: Key Management System

**KatamariKMS** is an advanced Key Management System designed to provide secure encryption, key rotation, and version-controlled key storage using **AES-256 encryption**. Built on top of **KatamariMVCC** for full transactional integrity, it ensures secure and versioned key management for distributed systems, pipelines, and serverless functions.

## Key Features

- **AES-256 Encryption**: KatamariKMS utilizes strong AES-256 encryption for securely managing sensitive data.
- **Key Rotation with Version Control**: The system allows for seamless key rotation while maintaining version control using **KatamariMVCC**. Each key is versioned and stored with transactional consistency.
- **Encryption & Decryption**: Easily encrypt and decrypt data using versioned keys.
- **KatamariMVCC Integration**: Ensures that each operation (key generation, encryption, decryption, and key rotation) is fully transactional and version-controlled.

## Table of Contents
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Key Generation](#key-generation)
  - [Encrypting Data](#encrypting-data)
  - [Decrypting Data](#decrypting-data)
  - [Key Rotation](#key-rotation)
- [Version Control](#version-control)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Installation

KatamariKMS can be easily installed as part of the **Katamari Ecosystem**:

```bash
git clone https://github.com/gddisney/katamari.git
cd katamari
pip install -r requirements.txt
```

This will install all required dependencies, including **KatamariMVCC**.

## Configuration

KatamariKMS uses a simple directory structure to store keys with **AES-256 encryption**. Ensure that the desired key storage path is correctly configured. By default, keys are stored in `./kms_keys`.

Example configuration (YAML):

```yaml
kms:
  key_store_path: ./kms_keys
```

## Usage

### Key Generation

You can easily generate a new AES-256 key for secure encryption purposes. Each key is automatically versioned and stored in the **KatamariMVCC** system.

```python
from KatamariKMS import KatamariKMS

kms = KatamariKMS()
key = kms.generate_key("my_secret_key")
```

### Encrypting Data

KatamariKMS allows you to encrypt sensitive data using a specified key and optional version.

```python
encrypted_data = kms.encrypt("my_secret_key", b"My sensitive data")
print(encrypted_data)
```

### Decrypting Data

To decrypt data, simply provide the key name and the encrypted payload. The system automatically retrieves the correct key version if not specified.

```python
decrypted_data = kms.decrypt("my_secret_key", encrypted_data)
print(decrypted_data.decode('utf-8'))
```

### Key Rotation

You can rotate the key while maintaining all previous versions using **KatamariMVCC**.

```python
new_key = kms.rotate_key("my_secret_key")
```

This will store the new key version and leave previous versions intact for historical access.

## Version Control

Thanks to **KatamariMVCC**, each key is stored with full version control. You can retrieve older key versions or roll back changes if necessary.

- **Version Retrieval**: Retrieve specific versions of a key by version number.
- **Historical Access**: Easily access previous key versions for auditing or decryption of old data.

Example:

```python
old_key = kms.load_key("my_secret_key", version=1)
```

## Examples

### Storing and Encrypting a Database Password

```python
# Step 1: Generate a key
kms = KatamariKMS()
kms.generate_key("db_encryption_key")

# Step 2: Encrypt the database password
encrypted_password = kms.encrypt("db_encryption_key", b"my_db_password")

# Step 3: Decrypt the password later
decrypted_password = kms.decrypt("db_encryption_key", encrypted_password)
print(f"Decrypted password: {decrypted_password.decode('utf-8')}")
```

### Key Rotation Example

```python
# Rotate the encryption key
new_key = kms.rotate_key("db_encryption_key")
print(f"New key generated: {new_key}")
```

## Contributing

We welcome contributions to **KatamariKMS**! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Open a pull request.

## License

**KatamariKMS** is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

KatamariKMS is a part of the **Katamari Ecosystem** and is designed to integrate seamlessly with other components, including **KatamariIAM**, **KatamariPipelines**, and **KatamariBucket** for secure data and credential management.
