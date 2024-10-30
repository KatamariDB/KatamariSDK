from azure.mgmt.compute import ComputeManagementClient
from azure.identity import DefaultAzureCredential
from azure.mgmt.storage import StorageManagementClient
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KatamariAzureProvider')

class KatamariAzureProvider:
    def __init__(self, config_path):
        # Load YAML configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

        self.services = {}
        self.subscription_id = self.config['providers']['azure']['subscription_id']
        self.credentials = DefaultAzureCredential()

        # Initialize Azure services
        for service in self.config['providers']['azure']['services']:
            service_name = service['name']
            if service_name == 'compute':
                self.services[service_name] = ComputeManagementClient(self.credentials, self.subscription_id)
            elif service_name == 'storage':
                self.services[service_name] = StorageManagementClient(self.credentials, self.subscription_id)
            else:
                raise ValueError(f"Unknown Azure service: {service_name}")

    def execute_service_action(self, service_name, action, params):
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found.")

        try:
            if service_name == 'storage':
                if action == 'create_container':
                    container = service.blob_containers.create(
                        params['resource_group'],
                        params['account_name'],
                        params['container_name'],
                        {}
                    )
                    logger.info(f"Container {params['container_name']} created.")
                    return container
            elif service_name == 'compute':
                if action == 'create_vm':
                    vm = service.virtual_machines.begin_create_or_update(
                        params['resource_group'],
                        params['vm_name'],
                        params['vm_parameters']
                    )
                    logger.info(f"VM {params['vm_name']} created.")
                    return vm
        except Exception as e:
            logger.error(f"Failed to execute {action} for {service_name}: {e}")

    def run(self):
        for service in self.config['providers']['azure']['services']:
            service_name = service['name']
            for action in service['actions']:
                self.execute_service_action(service_name, action['action'], action['params'])

# Example usage
if __name__ == "__main__":
    provider = KatamariAzureProvider("katamari_config.yaml")
    provider.run()

