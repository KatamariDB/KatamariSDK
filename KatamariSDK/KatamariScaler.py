import logging

logger = logging.getLogger('KatamariScaler')

class KatamariScaler:
    """Handles scaling infrastructure up and down based on provider capabilities."""
    def __init__(self, provider):
        self.provider = provider

    async def scale_up(self, instance_type: str, region: str) -> dict:
        """Scale up infrastructure by provisioning more instances."""
        logger.info(f"Scaling up infrastructure in {region}")
        return await self.provider.provision_instance(instance_type, region)

    async def scale_down(self, instance_id: str) -> bool:
        """Scale down infrastructure by terminating instances."""
        logger.info(f"Scaling down infrastructure, terminating instance: {instance_id}")
        return await self.provider.terminate_instance(instance_id)

