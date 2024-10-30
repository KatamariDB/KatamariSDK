Here's a combined markdown write-up for **KatamariAWSProvider**, **KatamariGCPProvider**, and **KatamariAzureProvider**.

---

# Katamari Cloud Providers: AWS, GCP, and Azure

The **Katamari Ecosystem** integrates with the three major cloud platforms: AWS, GCP, and Azure. Each provider allows you to manage infrastructure services like compute, storage, serverless functions, and more through a unified interface that supports dynamic scaling, key management, and event-driven architecture.

## Overview

- **KatamariAWSProvider**: Handles AWS-specific services using the `boto3` SDK.
- **KatamariGCPProvider**: Manages Google Cloud Platform services using the `google.cloud` SDK.
- **KatamariAzureProvider**: Interfaces with Microsoft Azure services using the `azure-mgmt` libraries.

### Common Features:
- **IAM Management**: Create, manage, and authenticate users or service accounts across the providers.
- **Serverless Lambda Functions**: Manage serverless compute resources to run event-triggered code.
- **Pipelines**: Orchestrate ETL processes and workflows across cloud services.
- **Bucket Management**: Provides S3, GCS, and Azure Blob-like object storage.
- **Encryption & Key Management**: Supports **KatamariKMS** integration for secure management of API keys, credentials, and sensitive data.
- **Secrets Management**: Uses **KatamariVault** for storing and retrieving secrets securely, encrypted by the **KMS** service.

## Configuration Structure

Each provider is configured through the YAML file, allowing you to define region, services, and scaling rules. Below is a breakdown of the configuration for each provider:

### KatamariAWSProvider

**KatamariAWSProvider** uses the `boto3` SDK to interface with AWS services. You can define resources like EC2, S3, Lambda, IAM, and more.

#### Example YAML Configuration:
```yaml
providers:
  aws:
    region: us-west-2
    dry_run: true
    services:
      - name: ec2
        type: resource
        actions:
          - action: create_instances
            params:
              InstanceType: t2.micro
              MinCount: 1
              MaxCount: 3
      - name: s3
        type: client
        actions:
          - action: create_bucket
            params:
              Bucket: my-aws-bucket
```

### KatamariGCPProvider

**KatamariGCPProvider** uses the `google.cloud` SDK to interact with Google Cloud services like Compute Engine, Cloud Functions, Cloud Storage, and IAM.

#### Example YAML Configuration:
```yaml
providers:
  gcp:
    region: us-central1
    dry_run: true
    services:
      - name: compute
        type: resource
        actions:
          - action: create_instances
            params:
              machine_type: n1-standard-1
              count: 2
      - name: storage
        type: client
        actions:
          - action: create_bucket
            params:
              bucket_name: my-gcp-bucket
```

### KatamariAzureProvider

**KatamariAzureProvider** uses the `azure-mgmt` SDK to manage Azure services, including Virtual Machines, Azure Blob Storage, and Azure Functions.

#### Example YAML Configuration:
```yaml
providers:
  azure:
    region: eastus
    dry_run: true
    services:
      - name: vm
        type: resource
        actions:
          - action: provision_vms
            params:
              vm_size: Standard_B1s
              count: 2
      - name: storage
        type: client
        actions:
          - action: create_storage_account
            params:
              account_name: my-azure-storage
```

## Key Services

### 1. **IAM Management**
   Each provider allows the creation and management of users and service accounts. You can configure roles, manage user authentication, and securely handle API keys and credentials using **KatamariKMS** for encryption.

### 2. **Serverless Functions (Lambda/Functions)**
   Serverless compute capabilities are provided across AWS (Lambda), GCP (Cloud Functions), and Azure (Functions). You can define, deploy, and manage serverless functions that respond to events such as file uploads, HTTP requests, or scheduled triggers.

### 3. **Pipelines (ETL/Workflows)**
   Katamari's pipeline management supports ETL jobs and workflow orchestration across all providers. Define tasks, schedule them, and let the system automatically manage dependencies between jobs.

### 4. **Bucket (Object Storage)**
   Manage object storage (S3, GCS, Azure Blob) for storing files, media, backups, or any type of unstructured data. With KatamariBucket, you can handle file uploads, downloads, and versioning across providers.

### 5. **Encryption (KMS) and Secrets (Vault)**
   Secure management of credentials and secrets is made possible by **KatamariKMS** and **KatamariVault**, allowing you to store, encrypt, and retrieve sensitive information using your preferred cloud provider.

## How to Use

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/gddisney/katamari.git
   cd katamari
   ```

2. **Configure Your YAML File:**
   Edit the `katamari_config.yaml` file to include the desired services and actions for AWS, GCP, and Azure. Include user roles, pipelines, lambda functions, and bucket operations as per your needs.

3. **Run KatamariProvider:**
   ```bash
   python katamari_provider.py
   ```

   You can also perform a dry-run to test the configuration:
   ```bash
   python katamari_provider.py --dry-run
   ```

4. **Deploy Services:**
   After the dry-run, confirm deployment:
   ```bash
   python katamari_provider.py --deploy
   ```

## License

This project is licensed under the terms of the [MIT License](LICENSE).

--- 

With **KatamariAWSProvider**, **KatamariGCPProvider**, and **KatamariAzureProvider**, you can orchestrate complex cloud architectures across multiple platforms, ensuring consistency, security, and scalability in your cloud infrastructure.
