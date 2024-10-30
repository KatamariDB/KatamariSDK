# KatamariSDK

**KatamariSDK** is a comprehensive, modular, and event-driven framework designed to support real-time data applications. Built to offer flexibility in handling data workflows and cloud infrastructure, KatamariSDK is inspired by the versatility of MongoDB, Redis, and Elasticsearch and provides a robust ecosystem to support complex, resilient, and high-performance applications.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Components](#core-components)
  - [KatamariDB](#katamaridb)
  - [KatamariProvider](#katamariprovider)
  - [KatamariPipelines](#katamaripipelines)
  - [KatamariUI](#katamariui)
  - [Event System](#event-system)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

KatamariSDK is designed to make it easy to build and deploy real-time applications by offering a modular architecture that includes key components for cloud integration, database management, pipeline orchestration, and a custom UI framework. Each component is designed to work independently or as part of a broader ecosystem, allowing users to build flexible and scalable applications across multiple cloud platforms.

## Features

- **Real-Time Database**: KatamariDB supports transactional, near real-time data operations with MVCC (Multi-Version Concurrency Control) and ORM-like capabilities.
- **Multi-Cloud Failover**: Automatically failover across cloud providers with minimal latency.
- **Pipeline Management**: Easily define, schedule, and manage complex data workflows with built-in state machines.
- **Cloud Integrations**: Pre-built support for Azure, Google Cloud, and AWS, with extensible modules for adding other cloud providers.
- **Identity Management**: Secure your applications with KatamariIAM for identity and access management.
- **Custom UI Framework**: KatamariUI allows real-time data visualization and interaction with a Streamlit-like, async-first approach.

## Installation

To install and set up KatamariSDK, follow these steps:

1. **Clone the repository**:

   ```bash
   git clone https://github.com/KatamariDB/Katamari.git
   cd Katamari
   ```

2. **Install Dependencies**:

   KatamariSDK depends on cloud and utility packages. Install them with:

   ```bash
   pip install azure-identity azure-mgmt-storage python-dateutil google-cloud-compute google-cloud-storage
   ```

3. **Build and Install the Package**:

   Run the following commands using Python 3.11 to build and install the package:

   ```bash
   python3.11 setup.py build
   python3.11 setup.py install
   ```

   > **Note**: For development, use an editable install with:
   >
   > ```bash
   > python3.11 setup.py develop
   > ```

4. **Verify Installation**:

   To confirm that the installation was successful, open a Python shell and import a module:

   ```python
   python3.11
   >>> from KatamariSDK import KatamariUI  # or any other module
   ```

## Quick Start

Here's a quick example to help you get started with setting up and managing a pipeline in KatamariSDK:

```python
from KatamariSDK.KatamariPipelines import PipelineManager
from KatamariSDK.KatamariProvider import KatamariAWSProvider, KatamariAzureProvider
from KatamariSDK.KatamariFailover import KatamariFailover

# Initialize cloud providers
aws_provider = KatamariAWSProvider('ACCESS_KEY', 'SECRET_KEY', 'us-east-1')
azure_provider = KatamariAzureProvider('SUBSCRIPTION_ID')

# Set up failover manager with multiple providers
failover_manager = KatamariFailover(providers={'aws': aws_provider, 'azure': azure_provider})

# Define pipeline configurations
pipeline_configs = [
    {'name': 'DataPipeline', 'jobs': [{'name': 'IngestData'}, {'name': 'ProcessData'}]}
]

# Initialize pipeline manager and start scheduling pipelines
pipeline_manager = PipelineManager(pipeline_configs=pipeline_configs)
pipeline_manager.schedule_pipelines()
```

## Core Components

### KatamariDB
A powerful database layer that combines MongoDB and Redis-like features with Elasticsearch-inspired querying capabilities. KatamariDB supports MVCC, full-text search, and an ORM for schema-based management.

### KatamariProvider
Handles cloud provider interactions and abstracts common operations across AWS, Azure, and Google Cloud. Providers can be added, configured, and managed individually to allow seamless failover and multi-cloud setups.

### KatamariPipelines
Provides a robust way to define, schedule, and execute complex workflows with real-time tracking and state management for data processing tasks.

### KatamariUI
An async-first UI framework inspired by Streamlit, built on FastAPI and Jinja2, allowing real-time interactions and WebSocket support for real-time data visualizations.

### Event System
A flexible, event-driven architecture to manage and track events across your application, allowing for complex data and state transitions with minimal latency.

## Examples

See the [examples directory](https://github.com/KatamariDB/Katamari/tree/main/examples) for sample applications demonstrating KatamariSDK's features, including pipeline scheduling, failover handling, and cloud integrations.

## Contributing

We welcome contributions! If you're interested in improving or extending KatamariSDK, please read our [contribution guidelines](https://github.com/KatamariDB/Katamari/blob/main/CONTRIBUTING.md) and submit a pull request.

## License

KatamariSDK is licensed under the MIT License. See the [LICENSE](https://github.com/KatamariDB/Katamari/blob/main/LICENSE) file for details.

