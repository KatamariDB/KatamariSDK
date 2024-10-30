import boto3
import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KatamariAWSProvider')

class KatamariAWSProvider:
    def __init__(self, config_path):
        # Load YAML configuration
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        
        self.services = {}
        region = self.config['providers']['aws']['region']
        
        for service in self.config['providers']['aws']['services']:
            service_name = service['name']
            service_type = service['type']
            
            if service_type == 'resource':
                self.services[service_name] = boto3.resource(service_name, region_name=region)
            elif service_type == 'client':
                self.services[service_name] = boto3.client(service_name, region_name=region)
            else:
                raise ValueError(f"Unknown service type: {service_type}")
    
    def execute_service_action(self, service_name, action, params):
        service = self.services.get(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found.")
        
        try:
            service_action = getattr(service, action)
            response = service_action(**params)
            logger.info(f"Successfully executed {action} on {service_name}. Response: {response}")
            return response
        except AttributeError:
            raise ValueError(f"Action {action} not available for service {service_name}.")
    
    def run(self):
        for service in self.config['providers']['aws']['services']:
            service_name = service['name']
            for action in service['actions']:
                self.execute_service_action(service_name, action['action'], action['params'])

# Example usage
if __name__ == "__main__":
    provider = KatamariAWSProvider("katamari_config.yaml")
    provider.run()

