import boto3
from botocore.exceptions import ClientError
from .logger import logger


class EC2Manager:
    """
    Manages EC2 instance operations.
    """

    def __init__(self, profile_name, region):
        """
        Initializes the EC2Manager with a specific AWS CLI profile and region.

        :param profile_name: str. The AWS CLI profile name.
        :param region: str. AWS region where the instance is located.
        """
        self.profile_name = profile_name
        self.region = region
        self.session = boto3.Session(
            profile_name=self.profile_name, region_name=self.region
        )
        self.ec2_client = self.session.client("ec2")

    def start_instance(self, instance_id):
        """
        Starts an EC2 instance and waits until it's running.

        :param instance_id: str. The ID of the EC2 instance to start.
        :return: bool. True if successful, False otherwise.
        """
        try:
            logger.info(f"Starting instance {instance_id}...")
            response = self.ec2_client.start_instances(InstanceIds=[instance_id])
            logger.info(f"Start request response: {response}")

            # Create a waiter to wait until the instance is running
            waiter = self.ec2_client.get_waiter("instance_running")
            logger.info(
                f"Waiting for instance {instance_id} to reach 'running' state..."
            )
            waiter.wait(InstanceIds=[instance_id])
            logger.info(f"Instance {instance_id} is now running.")
            return True

        except ClientError as e:
            logger.error(f"An error occurred while starting the instance: {e}")
            return False

    def stop_instance(self, instance_id):
        """
        Stops an EC2 instance and waits until it's stopped.

        :param instance_id: str. The ID of the EC2 instance to stop.
        :return: bool. True if successful, False otherwise.
        """
        try:
            logger.info(f"Stopping instance {instance_id}...")
            response = self.ec2_client.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Stop request response: {response}")

            # Create a waiter to wait until the instance is stopped
            waiter = self.ec2_client.get_waiter("instance_stopped")
            logger.info(
                f"Waiting for instance {instance_id} to reach 'stopped' state..."
            )
            waiter.wait(InstanceIds=[instance_id])
            logger.info(f"Instance {instance_id} is now stopped.")
            return True

        except ClientError as e:
            logger.error(f"An error occurred while stopping the instance: {e}")
            return False

    def get_public_dns(self, instance_id):
        """
        Retrieves the Public IPv4 DNS of an EC2 instance.

        :param instance_id: str. The ID of the EC2 instance.
        :return: str or None. The Public IPv4 DNS of the instance.
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            public_dns = instance.get("PublicDnsName")

            if public_dns:
                logger.info(
                    f"The Public IPv4 DNS for instance {instance_id} is: {public_dns}"
                )
                return public_dns
            else:
                logger.warning(
                    f"Instance {instance_id} does not have a Public IPv4 DNS."
                )
                return None

        except ClientError as e:
            logger.error(f"An error occurred while retrieving the Public DNS: {e}")
            return None

    def get_instance_state(self, instance_id):
        """
        Retrieves the current state of an EC2 instance.

        :param instance_id: str. The ID of the EC2 instance.
        :return: str or None. The current state of the instance (e.g., 'running', 'stopped'), or None if not found.
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            state = instance["State"]["Name"]
            logger.info(f"Instance {instance_id} is currently in state: {state}")
            return state

        except ClientError as e:
            logger.error(f"An error occurred while retrieving the instance state: {e}")
            return None
