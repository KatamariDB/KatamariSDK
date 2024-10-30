from google.cloud import storage, compute_v1
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KatamariGCPProvider')

class KatamariGCPProvider:
    def __init__(self, config_path):
        # Load YAML configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

        self.services = {}
        self.project_id = self.config['providers']['gcp']['project_id']

        # Initialize GCP services
        for service in self.config['providers']['gcp']['services']:
            service_name = service['name']
            if service_name == 'storage':
                self.services[service_name] = storage.Client()
            elif service_name == 'compute':
                self.services[service_name] = compute_v1.InstancesClient()
            else:
                raise ValueError(f"Unknown GCP service: {service_name}")

    def execute_service_action(self, service_name, action, params):
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found.")

        try:
            if service_name == 'storage':
                if action == 'create_bucket':
                    bucket = service.create_bucket(params['bucket_name'])
                    logger.info(f"Bucket {params['bucket_name']} created.")
                    return bucket
            elif service_name == 'compute':
                if action == 'create_instance':
                    operation = service.insert(
                        project=self.project_id,
                        zone=params.get('zone', 'us-central1-a'),
                        instance_resource=params
                    )
                    logger.info(f"Instance {params['name']} created.")
                    return operation
        except Exception as e:
            logger.error(f"Failed to execute {action} for {service_name}: {e}")

    def run(self):
        for service in self.config['providers']['gcp']['services']:
            service_name = service['name']
            for action in service['actions']:
                self.execute_service_action(service_name, action['action'], action['params'])

# Example usage
if __name__ == "__main__":
    provider = KatamariGCPProvider("katamari_config.yaml")
    provider.run()

