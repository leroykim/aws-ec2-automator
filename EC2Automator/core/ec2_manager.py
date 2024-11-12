# core/ec2_manager.py

import boto3
from botocore.exceptions import ClientError
from .logger import logger


class EC2ManagerError(Exception):
    """
    Custom exception for EC2Manager-related errors.

    Attributes
    ----------
    message : str
        Explanation of the error.
    """

    def __init__(self, message):
        """
        Initialize the EC2ManagerError with a message.

        Parameters
        ----------
        message : str
            Explanation of the error.
        """
        super().__init__(message)
        self.message = message


class EC2Manager:
    """
    Manages EC2 instance operations.

    This class provides functionalities to describe, start, stop, and retrieve information
    about EC2 instances. It interacts directly with the AWS EC2 service using the boto3
    library and handles exceptions related to EC2 operations.

    Parameters
    ----------
    session : boto3.Session, optional
        The boto3 session to use for AWS service calls. If `None`, a new session is created.

    Attributes
    ----------
    session : boto3.Session
        The boto3 session used for AWS service interactions.
    ec2_client : boto3.client
        The EC2 client for making API calls.

    Methods
    -------
    describe_instance(instance_id)
        Retrieves the full description of the specified EC2 instance.
    get_instance_state(instance_id)
        Retrieves the current state of the specified EC2 instance.
    get_instance_type(instance_id)
        Retrieves the instance type of the specified EC2 instance.
    get_launch_time(instance_id)
        Retrieves the launch time of the specified EC2 instance.
    start_instance(instance_id)
        Starts the specified EC2 instance.
    stop_instance(instance_id)
        Stops the specified EC2 instance.
    get_public_dns(instance_id)
        Retrieves the public DNS of the specified EC2 instance.
    """

    def __init__(self, session=None):
        """
        Initializes the EC2Manager with a boto3 session.

        Parameters
        ----------
        session : boto3.Session, optional
            The boto3 session to use for AWS service calls. If `None`, a new session is created.
        """
        self.session = session or boto3.Session()
        self.ec2_client = self.session.client("ec2")
        logger.info(
            f"Initialized EC2Manager for profile '{self.session.profile_name}' in region '{self.session.region_name}'."
        )

    def describe_instance(self, instance_id):
        """
        Retrieves the full description of the specified EC2 instance.

        Parameters
        ----------
        instance_id : str
            The ID of the EC2 instance.

        Returns
        -------
        dict
            The instance description as returned by the AWS EC2 API.

        Raises
        ------
        EC2ManagerError
            If the instance cannot be described due to AWS service errors or invalid instance ID.
        """
        try:
            logger.debug(f"Describing instance {instance_id}.")
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            return instance
        except ClientError as e:
            logger.error(f"Error describing instance {instance_id}: {e}")
            raise EC2ManagerError(f"Error describing instance {instance_id}") from e
        except IndexError:
            logger.error(f"Instance {instance_id} not found.")
            raise EC2ManagerError(f"Instance {instance_id} not found.") from None

    def get_instance_state(self, instance_id):
        """
        Retrieves the current state of the specified EC2 instance.

        Parameters
        ----------
        instance_id : str
            The ID of the EC2 instance.

        Returns
        -------
        str
            The state of the instance (e.g., 'running', 'stopped').

        Raises
        ------
        EC2ManagerError
            If the state cannot be retrieved due to AWS service errors or invalid instance ID.
        """
        try:
            instance = self.describe_instance(instance_id)
            state = instance["State"]["Name"]
            logger.debug(f"Instance {instance_id} is in state: {state}")
            return state
        except EC2ManagerError as e:
            logger.error(f"Failed to get state for instance {instance_id}: {e}")
            raise

    def get_instance_type(self, instance_id):
        """
        Retrieves the instance type of the specified EC2 instance.

        Parameters
        ----------
        instance_id : str
            The ID of the EC2 instance.

        Returns
        -------
        str
            The instance type (e.g., 't2.micro').

        Raises
        ------
        EC2ManagerError
            If the instance type cannot be retrieved due to AWS service errors or invalid instance ID.
        """
        try:
            instance = self.describe_instance(instance_id)
            instance_type = instance["InstanceType"]
            logger.debug(f"Instance {instance_id} is of type: {instance_type}")
            return instance_type
        except EC2ManagerError as e:
            logger.error(f"Failed to get instance type for {instance_id}: {e}")
            raise

    def get_launch_time(self, instance_id):
        """
        Retrieves the launch time of the specified EC2 instance.

        Parameters
        ----------
        instance_id : str
            The ID of the EC2 instance.

        Returns
        -------
        datetime
            The launch time in UTC.

        Raises
        ------
        EC2ManagerError
            If the launch time cannot be retrieved due to AWS service errors or invalid instance ID.
        """
        try:
            instance = self.describe_instance(instance_id)
            launch_time = instance["LaunchTime"]
            logger.debug(f"Instance {instance_id} launch time: {launch_time}")
            return launch_time
        except EC2ManagerError as e:
            logger.error(f"Failed to get launch time for {instance_id}: {e}")
            raise

    def start_instance(self, instance_id):
        """
        Starts the specified EC2 instance.

        Parameters
        ----------
        instance_id : str
            The ID of the EC2 instance.

        Returns
        -------
        bool
            True if the start operation was successfully initiated, False otherwise.

        Raises
        ------
        EC2ManagerError
            If the start operation fails due to AWS service errors or invalid instance ID.
        """
        try:
            logger.info(f"Starting instance {instance_id}.")
            self.ec2_client.start_instances(InstanceIds=[instance_id])
            logger.info(f"Instance {instance_id} start initiated.")
            return True
        except ClientError as e:
            logger.error(f"Error starting instance {instance_id}: {e}")
            raise EC2ManagerError(f"Error starting instance {instance_id}") from e

    def stop_instance(self, instance_id):
        """
        Stops the specified EC2 instance.

        Parameters
        ----------
        instance_id : str
            The ID of the EC2 instance.

        Returns
        -------
        bool
            True if the stop operation was successfully initiated, False otherwise.

        Raises
        ------
        EC2ManagerError
            If the stop operation fails due to AWS service errors or invalid instance ID.
        """
        try:
            logger.info(f"Stopping instance {instance_id}.")
            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            logger.info(f"Instance {instance_id} stop initiated.")
            return True
        except ClientError as e:
            logger.error(f"Error stopping instance {instance_id}: {e}")
            raise EC2ManagerError(f"Error stopping instance {instance_id}") from e

    def get_public_dns(self, instance_id):
        """
        Retrieves the public DNS of the specified EC2 instance.

        Parameters
        ----------
        instance_id : str
            The ID of the EC2 instance.

        Returns
        -------
        str
            The public DNS name of the instance. Returns an empty string if not available.

        Raises
        ------
        EC2ManagerError
            If the public DNS cannot be retrieved due to AWS service errors or invalid instance ID.
        """
        try:
            instance = self.describe_instance(instance_id)
            public_dns = instance.get("PublicDnsName", "")
            if public_dns:
                logger.debug(f"Instance {instance_id} public DNS: {public_dns}")
                return public_dns
            else:
                logger.warning(f"Instance {instance_id} does not have a public DNS.")
                return ""
        except EC2ManagerError as e:
            logger.error(f"Failed to get public DNS for {instance_id}: {e}")
            raise
