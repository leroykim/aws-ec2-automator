# core/ec2_automator.py

from botocore.exceptions import BotoCoreError, WaiterError
from .sso_authentication_checker import SSOAuthenticationChecker
from .sso_login_handler import SSOLoginHandler, SSOLoginError
from .ec2_manager import EC2Manager, EC2ManagerError
from .ssh_config_manager import SSHConfigManager, SSHConfigManagerError
from .ec2_cost_estimator import EC2CostEstimator, EC2CostEstimatorError
from .logger import logger


class EC2AutomatorError(Exception):
    """
    Custom exception for EC2Automator-related errors.

    Attributes
    ----------
    message : str
        Explanation of the error.
    """

    def __init__(self, message):
        """
        Initialize the EC2AutomatorError with a message.

        Parameters
        ----------
        message : str
            Explanation of the error.
        """
        super().__init__(message)
        self.message = message


class EC2Automator:
    """
    Integrates EC2 operations with SSH config management and cost estimation.

    This class orchestrates the workflow for managing an EC2 instance, including starting,
    stopping, updating SSH configurations, and estimating running costs. It ensures that
    the AWS session is authenticated, handles the state transitions of the EC2 instance,
    and maintains the SSH configuration for seamless access.

    Parameters
    ----------
    sso_authentication_checker : SSOAuthenticationChecker
        Instance to check AWS authentication status.
    sso_login_handler : SSOLoginHandler
        Instance to handle AWS SSO login process.
    ec2_manager : EC2Manager
        Instance to manage EC2 operations like start, stop, and state retrieval.
    ssh_manager : SSHConfigManager
        Instance to manage SSH configuration entries.
    cost_estimator : EC2CostEstimator
        Instance to estimate the running cost of the EC2 instance.
    instance_id : str
        The ID of the EC2 instance to manage.
    ssh_host_name : str
        The Host entry name in the SSH config to update for SSH access.

    Attributes
    ----------
    authentication_checker : SSOAuthenticationChecker
        Checker for AWS authentication.
    sso_login_handler : SSOLoginHandler
        Handler for AWS SSO login.
    ec2_manager : EC2Manager
        Manager for EC2 operations.
    ssh_manager : SSHConfigManager
        Manager for SSH configurations.
    cost_estimator : EC2CostEstimator
        Estimator for EC2 running costs.
    instance_id : str
        EC2 instance ID.
    ssh_host_name : str
        SSH Host entry name.
    """

    def __init__(
        self,
        sso_authentication_checker: SSOAuthenticationChecker,
        sso_login_handler: SSOLoginHandler,
        ec2_manager: EC2Manager,
        ssh_manager: SSHConfigManager,
        cost_estimator: EC2CostEstimator,
        instance_id: str,
        ssh_host_name: str,
    ):
        """
        Initialize the EC2Automator with necessary configurations and dependencies.

        Parameters
        ----------
        sso_authentication_checker : SSOAuthenticationChecker
            Checker for AWS authentication.
        sso_login_handler : SSOLoginHandler
            Handler for AWS SSO login.
        ec2_manager : EC2Manager
            Manager for EC2 operations.
        ssh_manager : SSHConfigManager
            Manager for SSH configurations.
        cost_estimator : EC2CostEstimator
            Estimator for EC2 running costs.
        instance_id : str
            The ID of the EC2 instance to manage.
        ssh_host_name : str
            The Host entry name in the SSH config to update for SSH access.
        """
        self.authentication_checker = sso_authentication_checker
        self.sso_login_handler = sso_login_handler
        self.ec2_manager = ec2_manager
        self.ssh_manager = ssh_manager
        self.cost_estimator = cost_estimator
        self.instance_id = instance_id
        self.ssh_host_name = ssh_host_name

        # Perform authentication upon initialization
        self.authenticate()

    def authenticate(self):
        """
        Authenticate the AWS session. Attempts login if not authenticated.

        This method checks if the AWS session is authenticated using the provided
        SSOAuthenticationChecker. If not authenticated, it initiates the SSO
        login process using the SSOLoginHandler. It ensures that the session is
        authenticated before proceeding with EC2 operations.

        Raises
        ------
        EC2AutomatorError
            If authentication fails after attempting SSO login.
        """
        if not self.authentication_checker.is_authenticated():
            logger.warning("AWS session is not authenticated or token has expired.")
            try:
                self.sso_login_handler.login()
            except SSOLoginError:
                logger.error("Failed to authenticate AWS SSO.")
                raise EC2AutomatorError("Failed to authenticate AWS SSO.") from None

            if not self.authentication_checker.is_authenticated():
                logger.error("AWS session is still not authenticated after login.")
                raise EC2AutomatorError("AWS session is not authenticated after login.")
        else:
            logger.info("AWS session is already authenticated.")

    def start_instance_workflow(self):
        """
        Execute the workflow to start an EC2 instance.

        This method performs the following steps:
        1. Checks the current state of the EC2 instance.
        2. If the instance is not running, initiates the start operation.
        3. Waits until the instance reaches the 'running' state.
        4. Retrieves the public DNS of the instance.
        5. Backs up the existing SSH configuration.
        6. Updates the SSH configuration with the new host entry.

        Raises
        ------
        EC2AutomatorError
            If any step in the workflow fails, including state retrieval,
            instance start operation, waiter failures, or SSH configuration updates.
        """
        # Check if the instance is already running
        try:
            current_state = self.ec2_manager.get_instance_state(self.instance_id)
        except EC2ManagerError as e:
            logger.error(f"Failed to get instance state: {e}")
            raise EC2AutomatorError(f"Failed to get instance state: {e}") from e

        if current_state == "running":
            logger.info(
                f"Instance {self.instance_id} is already running. No action needed."
            )
            print(f"Instance {self.instance_id} is already running.")
            return
        elif current_state in [
            "pending",
            "stopping",
            "stopped",
            "shutting-down",
            "terminated",
        ]:
            logger.info(
                f"Instance {self.instance_id} is in state '{current_state}'. Proceeding to start."
            )
        else:
            logger.warning(
                f"Instance {self.instance_id} is in an unexpected state: '{current_state}'."
            )

        # Start EC2 Instance
        if not self.ec2_manager.start_instance(self.instance_id):
            logger.error("Failed to start the EC2 instance.")
            raise EC2AutomatorError("Failed to start the EC2 instance.")

        # Initialize Boto3 Waiter for 'instance_running'
        try:
            waiter = self.ec2_manager.ec2_client.get_waiter("instance_running")
            logger.info(
                f"Waiting for instance {self.instance_id} to enter 'running' state."
            )
            waiter.wait(
                InstanceIds=[self.instance_id],
                WaiterConfig={
                    "Delay": 15,  # Wait 15 seconds between checks
                    "MaxAttempts": 40,  # Total wait time: 15 * 40 = 600 seconds (10 minutes)
                },
            )
            logger.info(f"Instance {self.instance_id} is now running.")
        except WaiterError as e:
            logger.error(f"Waiter failed: {e}")
            raise EC2AutomatorError(f"Waiter failed: {e}") from e
        except BotoCoreError as e:
            logger.error(f"Boto3 error during waiter: {e}")
            raise EC2AutomatorError(f"Boto3 error during waiter: {e}") from e

        # Get Public DNS
        try:
            public_dns = self.ec2_manager.get_public_dns(self.instance_id)
            if not public_dns:
                logger.error("Failed to retrieve Public IPv4 DNS.")
                raise EC2AutomatorError("Failed to retrieve Public IPv4 DNS.")
        except EC2ManagerError as e:
            logger.error(f"Failed to get Public DNS: {e}")
            raise EC2AutomatorError(f"Failed to get Public DNS: {e}") from e

        # Backup SSH Config
        try:
            backup_path = self.ssh_manager.backup_config()
            if not backup_path:
                logger.error("Failed to backup SSH config.")
                raise EC2AutomatorError("Failed to backup SSH config.")
        except SSHConfigManagerError as e:
            logger.error(f"Failed to backup SSH config: {e}")
            raise EC2AutomatorError(f"Failed to backup SSH config: {e}") from e

        # Update SSH Config
        try:
            self.ssh_manager.update_host(self.ssh_host_name, public_dns)
            logger.info(
                f"SSH config updated with new DNS: {public_dns} for Host: {self.ssh_host_name}"
            )
        except SSHConfigManagerError as e:
            logger.error(f"Failed to update SSH config: {e}")
            raise EC2AutomatorError(f"Failed to update SSH config: {e}") from e

    def stop_instance_workflow(self):
        """
        Execute the workflow to stop an EC2 instance.

        This method performs the following steps:
        1. Checks the current state of the EC2 instance.
        2. If the instance is running, initiates the stop operation.
        3. Waits until the instance reaches the 'stopped' state.
        4. Removes the SSH host entry from the SSH configuration.

        Raises
        ------
        EC2AutomatorError
            If any step in the workflow fails, including state retrieval,
            instance stop operation, or SSH configuration updates.
        """
        # Check if the instance is already stopped
        try:
            current_state = self.ec2_manager.get_instance_state(self.instance_id)
        except EC2ManagerError as e:
            logger.error(f"Failed to get instance state: {e}")
            raise EC2AutomatorError(f"Failed to get instance state: {e}") from e

        if current_state == "stopped":
            logger.info(
                f"Instance {self.instance_id} is already stopped. No action needed."
            )
            print(f"Instance {self.instance_id} is already stopped.")
            return
        elif current_state in [
            "pending",
            "stopping",
            "running",
            "shutting-down",
            "terminated",
        ]:
            logger.info(
                f"Instance {self.instance_id} is in state '{current_state}'. Proceeding to stop."
            )
        else:
            logger.warning(
                f"Instance {self.instance_id} is in an unexpected state: '{current_state}'."
            )

        # Stop EC2 Instance
        if not self.ec2_manager.stop_instance(self.instance_id):
            logger.error("Failed to stop the EC2 instance.")
            raise EC2AutomatorError("Failed to stop the EC2 instance.")

        # Initialize Boto3 Waiter for 'instance_stopped'
        try:
            waiter = self.ec2_manager.ec2_client.get_waiter("instance_stopped")
            logger.info(
                f"Waiting for instance {self.instance_id} to enter 'stopped' state."
            )
            waiter.wait(
                InstanceIds=[self.instance_id],
                WaiterConfig={
                    "Delay": 15,  # Wait 15 seconds between checks
                    "MaxAttempts": 40,  # Total wait time: 15 * 40 = 600 seconds (10 minutes)
                },
            )
            logger.info(f"Instance {self.instance_id} is now stopped.")
        except WaiterError as e:
            logger.error(f"Waiter failed: {e}")
            raise EC2AutomatorError(f"Waiter failed: {e}") from e
        except BotoCoreError as e:
            logger.error(f"Boto3 error during waiter: {e}")
            raise EC2AutomatorError(f"Boto3 error during waiter: {e}") from e

    def get_estimated_cost(self):
        """
        Retrieve the estimated cost of the running EC2 instance.

        This method delegates the cost estimation to the EC2CostEstimator and returns
        the estimated hourly cost of running the specified EC2 instance.

        Returns
        -------
        float
            The estimated hourly cost in USD.

        Raises
        ------
        EC2AutomatorError
            If cost estimation fails.
        """
        try:
            cost = self.cost_estimator.estimate_cost(self.instance_id)
            if cost is None:
                logger.error("Failed to estimate the cost.")
                raise EC2AutomatorError("Failed to estimate the cost.")
            return cost
        except EC2CostEstimatorError as e:
            logger.error(f"Cost Estimation Error: {e}")
            raise EC2AutomatorError("Failed to estimate the cost.") from e
        except Exception as e:
            logger.error(f"Error retrieving estimated cost: {e}")
            raise EC2AutomatorError("Error retrieving estimated cost.") from e
