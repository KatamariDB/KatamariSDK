import logging
import yaml
from KatamariSDK.KatamariIAM import KatamariIAM
from KatamariSDK.KatamariPipelines import KatamariPipelineManager
from KatamariSDK.KatamariLambda import KatamariLambdaManager
from KatamariSDK.KatamariBucket import KatamariBucket
from KatamariSDK.KatamariVault import KatamariVault
from KatamariSDK.KatamariKMS import KatamariKMS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('KatamariProvider')


class KatamariProvider:
    """
    KatamariProvider integrates IAM, Pipelines, Lambda, Bucket, Vault, and KMS services
    to provide unified management of these components.
    """
    def __init__(self, config_path):
        self.config = self.load_config(config_path)
        self.iam_service = KatamariIAM(self.config['iam']['secret_key'])
        self.pipeline_service = KatamariPipelineManager(self.config['pipelines'])
        self.lambda_service = KatamariLambdaManager(self.config['lambda'])
        self.bucket_service = KatamariBucket(self.config['bucket']['name'], self.config['bucket']['storage_path'])
        self.vault_service = KatamariVault(self.config['vault']['vault_name'])
        self.kms_service = KatamariKMS()

    def load_config(self, config_path):
        """Load YAML configuration for KatamariProvider."""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def manage_iam(self):
        """Manage Identity and Access Management (IAM) for users and service accounts."""
        for user in self.config['iam']['users']:
            self.iam_service.create_user(user['username'], user['password'], roles=user['roles'])
            logger.info(f"Created IAM user: {user['username']}")

    def manage_pipelines(self):
        """Manage and execute pipelines based on the configuration."""
        for pipeline in self.config['pipelines']:
            self.pipeline_service.execute_pipeline(pipeline)
            logger.info(f"Pipeline {pipeline['name']} executed successfully.")

    def manage_lambda(self):
        """Deploy and manage Lambda functions based on the configuration."""
        for lambda_func in self.config['lambda']:
            self.lambda_service.deploy_lambda_function(lambda_func)
            logger.info(f"Deployed Lambda function: {lambda_func['function_name']}")

    def manage_bucket(self):
        """Manage object storage buckets (S3-like functionality)."""
        for operation in self.config['bucket']['operations']:
            if operation['action'] == 'upload':
                self.bucket_service.put(operation['key'], operation['file_data'].encode())
                logger.info(f"File {operation['key']} uploaded successfully.")
            elif operation['action'] == 'download':
                file_data = self.bucket_service.get(operation['key'])
                logger.info(f"File {operation['key']} downloaded successfully.")

    def manage_vault(self):
        """Manage secrets in KatamariVault."""
        for secret in self.config['vault']['secrets']:
            if secret['action'] == 'store':
                self.vault_service.store_secret(secret['key'], secret['value'])
                logger.info(f"Stored secret {secret['key']} in Vault.")
            elif secret['action'] == 'retrieve':
                retrieved_value = self.vault_service.retrieve_secret(secret['key'])
                logger.info(f"Retrieved secret {secret['key']} from Vault: {retrieved_value}")

    def manage_kms(self):
        """Manage encryption and decryption using KatamariKMS."""
        for key in self.config['kms']['keys']:
            if key['action'] == 'encrypt':
                encrypted_data = self.kms_service.encrypt(key['key_id'], key['data'])
                logger.info(f"Data encrypted with key {key['key_id']}. Encrypted value: {encrypted_data}")
            elif key['action'] == 'decrypt':
                decrypted_data = self.kms_service.decrypt(key['key_id'], key['encrypted_data'])
                logger.info(f"Data decrypted with key {key['key_id']}. Decrypted value: {decrypted_data}")

    def execute(self):
        """Execute all managed services (IAM, Pipelines, Lambda, Bucket, Vault, KMS)."""
        logger.info("Starting KatamariProvider execution.")
        self.manage_iam()
        self.manage_pipelines()
        self.manage_lambda()
        self.manage_bucket()
        self.manage_vault()
        self.manage_kms()
        logger.info("KatamariProvider execution completed.")


if __name__ == "__main__":
    provider = KatamariProvider('katamari_config.yaml')
    provider.execute()

