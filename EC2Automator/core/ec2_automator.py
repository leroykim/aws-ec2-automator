# core/ec2_automator.py

from botocore.exceptions import BotoCoreError, WaiterError
from .sso_authentication_checker import SSOAuthenticationChecker
from .sso_login_handler import SSOLoginHandler, SSOLoginError
from .ec2_manager import EC2Manager, EC2ManagerError
from .ssh_config_manager import SSHConfigManager, SSHConfigManagerError
from .ec2_cost_estimator import EC2CostEstimator, EC2CostEstimatorError
from .logger import logger


class EC2AutomatorError(Exception):
    """Custom exception for EC2Automator-related errors."""

    pass


class EC2Automator:
    """
    Integrates EC2 operations with SSH config management and cost estimation.
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
        Initializes the EC2Automator with necessary configurations and dependencies.

        :param sso_authentication_checker: SSOAuthenticationChecker. Checks AWS authentication.
        :param sso_login_handler: SSOLoginHandler. Manages AWS SSO login.
        :param ec2_manager: EC2Manager. Manages EC2 operations.
        :param ssh_manager: SSHConfigManager. Manages SSH configuration.
        :param cost_estimator: EC2CostEstimator. Estimates EC2 running costs.
        :param instance_id: str. The ID of the EC2 instance to manage.
        :param ssh_host_name: str. The Host entry in the SSH config to update.
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
        Authenticates the AWS session. Attempts login if not authenticated.

        Raises:
            EC2AutomatorError: If authentication fails.
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
        Executes the workflow to start an EC2 instance:
        - Checks instance state.
        - Starts the instance if not running.
        - Waits until the instance is running.
        - Retrieves public DNS.
        - Backs up and updates SSH config.

        Raises:
            EC2AutomatorError: If any step in the workflow fails.
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
        Executes the workflow to stop an EC2 instance:
        - Checks instance state.
        - Stops the instance if running.
        - Waits until the instance is stopped.

        Raises:
            EC2AutomatorError: If any step in the workflow fails.
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
        Retrieves the estimated cost of the running EC2 instance.

        :return: float. The estimated cost in USD.
        :raises EC2AutomatorError: If cost estimation fails.
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
