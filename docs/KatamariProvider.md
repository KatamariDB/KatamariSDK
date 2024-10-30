Here's an updated version of the **KatamariProvider** documentation markdown that includes the **KatamariVault** and **KatamariKMS** components.

---

# KatamariProvider Documentation

**KatamariProvider** is a unified service management solution within the Katamari Ecosystem. It provides streamlined integration of **IAM**, **Pipelines**, **Lambda**, **Bucket**, **KMS**, and **Vault** services. The provider enables easy configuration and management of these services across multiple cloud platforms.

## Features

- **IAM (Identity and Access Management):** Handles user and service account creation and management with secure authentication.
- **Pipelines:** Manages ETL (Extract, Transform, Load) workflows, job orchestration, and real-time data processing.
- **Lambda Functions:** Serverless compute capabilities that handle event-driven functions.
- **Bucket:** Object storage management, including file upload and download, with versioning support.
- **KMS (Key Management Service):** Manages encryption keys for securing data, including credentials for other services.
- **Vault:** Stores and retrieves secrets such as API keys, passwords, and database credentials securely, using KMS for encryption.

## Configuration

### YAML Configuration File

The configuration file (`katamari_config.yaml`) drives the setup and execution of the services. Below is a sample configuration structure for KatamariProvider:

```yaml
katamari:
  iam:
    secret_key: my_iam_secret
    users:
      - username: admin
        password: supersecurepassword
        roles:
          - admin
          - user

  pipelines:
    - name: DataPipeline1
      jobs:
        - name: Job1
          schedule: "5m"
        - name: Job2
          schedule: "10m"

  lambda:
    - function_name: DataProcessor
      handler: process_data
      schedule: "5m"
      environment:
        DB_HOST: 'localhost'

  bucket:
    name: my_bucket
    storage_path: './storage'
    operations:
      - action: upload
        key: report.csv
        file_data: 'data,1,2,3'

  kms:
    keys:
      - key_id: my_key
        description: 'Main key for secrets encryption'
        create_if_not_exists: true

  vault:
    vault_name: my_vault
    secrets:
      - action: store
        key: db_password
        value: 'my_db_password'
        kms_key_id: 'my_key'
      - action: retrieve
        key: db_password
        kms_key_id: 'my_key'
```

### KatamariProvider Initialization

To initialize and run the **KatamariProvider**, include the path to your YAML configuration file:

```python
provider = KatamariProvider('katamari_config.yaml')
provider.execute()
```

## Services

### IAM (Identity and Access Management)
- **Service Name:** `iam`
- **Actions:** Manage users and roles for your application.
- **Example Configuration:**
  ```yaml
  iam:
    secret_key: my_iam_secret
    users:
      - username: admin
        password: supersecurepassword
        roles:
          - admin
          - user
  ```

### Pipelines
- **Service Name:** `pipelines`
- **Actions:** Define and schedule pipeline jobs for ETL and data processing tasks.
- **Example Configuration:**
  ```yaml
  pipelines:
    - name: DataPipeline1
      jobs:
        - name: Job1
          schedule: "5m"
  ```

### Lambda Functions
- **Service Name:** `lambda`
- **Actions:** Deploy, manage, and invoke serverless functions.
- **Example Configuration:**
  ```yaml
  lambda:
    - function_name: DataProcessor
      handler: process_data
      schedule: "5m"
  ```

### Bucket (Object Storage)
- **Service Name:** `bucket`
- **Actions:** Manage file uploads and downloads with support for versioning.
- **Example Configuration:**
  ```yaml
  bucket:
    name: my_bucket
    storage_path: './storage'
    operations:
      - action: upload
        key: report.csv
        file_data: 'data,1,2,3'
  ```

### KMS (Key Management Service)
- **Service Name:** `kms`
- **Actions:** Manage encryption keys and use them to secure sensitive data like credentials.
- **Example Configuration:**
  ```yaml
  kms:
    keys:
      - key_id: my_key
        description: 'Main key for secrets encryption'
        create_if_not_exists: true
  ```

### Vault (Secrets Management)
- **Service Name:** `vault`
- **Actions:** Store and retrieve secrets such as API keys, passwords, and other credentials. Secrets are encrypted with KMS.
- **Example Configuration:**
  ```yaml
  vault:
    vault_name: my_vault
    secrets:
      - action: store
        key: db_password
        value: 'my_db_password'
        kms_key_id: 'my_key'
      - action: retrieve
        key: db_password
        kms_key_id: 'my_key'
  ```

## Example Usage

```bash
# Clone the repository
git clone https://github.com/gddisney/katamari.git

# Run the KatamariProvider service
python katamari_provider.py
```

## License

This project is licensed under the terms of the [MIT License](LICENSE).

---

By integrating IAM, Pipelines, Lambda, Buckets, KMS, and Vault management, **KatamariProvider** simplifies multi-service orchestration across cloud platforms.
