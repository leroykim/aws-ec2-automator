# core/ec2_automator.py

import sys
from .authenticator import SSOAuthenticator
from .ec2_manager import EC2Manager
from .ssh_config_manager import SSHConfigManager
from .ec2_cost_estimator import EC2CostEstimator
from .logger import logger


class EC2Automator:
    """
    Integrates EC2 operations with SSH config management and cost estimation.
    """

    def __init__(
        self,
        aws_profile,
        region,
        instance_id,
        ssh_host_name,
        ssh_config_path="~/.ssh/config",
    ):
        """
        Initializes the EC2Automator with necessary configurations and authenticates the AWS session.

        :param aws_profile: str. AWS CLI profile name configured for SSO.
        :param region: str. AWS region where the EC2 instance is located.
        :param instance_id: str. The ID of the EC2 instance to manage.
        :param ssh_host_name: str. The Host entry in the SSH config to update.
        :param ssh_config_path: str. Path to the SSH config file.
        """
        self.aws_profile = aws_profile
        self.region = region
        self.instance_id = instance_id
        self.ssh_host_name = ssh_host_name
        self.ssh_config_path = ssh_config_path
        self.ssh_manager = SSHConfigManager(self.ssh_config_path)
        self.authenticator = SSOAuthenticator(profile_name=self.aws_profile)
        self.ec2_manager = EC2Manager(profile_name=self.aws_profile, region=self.region)
        self.cost_estimator = EC2CostEstimator(ec2_manager=self.ec2_manager)

        # Perform authentication upon initialization
        self.authenticate()

    def authenticate(self):
        """
        Authenticates the AWS session. Logs in if not already authenticated.

        Exits the program if authentication fails.
        """
        if not self.authenticator.is_authenticated():
            logger.warning("AWS session is not authenticated or token has expired.")
            self.authenticator.login()
            if not self.authenticator.is_authenticated():
                logger.error("Failed to authenticate AWS SSO. Exiting.")
                sys.exit(1)
        else:
            logger.info("AWS session is already authenticated.")

    def start(self):
        """
        Executes the workflow to check instance state, start EC2, retrieve DNS, backup and update SSH config.
        """
        # Authentication is already handled in __init__

        # Check if the instance is already running
        current_state = self.ec2_manager.get_instance_state(self.instance_id)
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
            logger.error("Failed to start the EC2 instance. Exiting.")
            sys.exit(1)

        # Get Public DNS
        public_dns = self.ec2_manager.get_public_dns(self.instance_id)
        if not public_dns:
            logger.error("Failed to retrieve Public IPv4 DNS. Exiting.")
            sys.exit(1)

        # Backup SSH Config
        if not self.ssh_manager.backup_config():
            logger.error("Failed to backup SSH config. Exiting.")
            sys.exit(1)

        # Update SSH Config
        self.ssh_manager.update_host(self.ssh_host_name, public_dns)

    def stop(self):
        """
        Executes the workflow to stop the EC2 instance.
        """
        # Authentication is already handled in __init__

        # Stop EC2 Instance
        if not self.ec2_manager.stop_instance(self.instance_id):
            logger.error("Failed to stop the EC2 instance. Exiting.")
            sys.exit(1)

    def get_estimated_cost(self):
        """
        Retrieves the estimated cost of the running EC2 instance.

        :return: float or None. The estimated cost in USD, or None if estimation failed.
        """
        return self.cost_estimator.estimate_cost(self.instance_id)
