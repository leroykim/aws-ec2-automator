# core/sso_login_handler.py

import subprocess
from .logger import logger


class SSOLoginError(Exception):
    """Custom exception for SSO login-related errors."""

    pass


class SSOLoginHandler:
    """
    Manages the AWS SSO login process.
    """

    def __init__(self, profile_name):
        """
        Initializes the SSOLoginHandler with a specific AWS CLI profile.

        :param profile_name: str. The AWS CLI profile name configured for SSO.
        """
        self.profile_name = profile_name

    def login(self):
        """
        Performs AWS SSO login using the AWS CLI.

        Raises:
            SSOLoginError: If the login process fails.
        """
        try:
            logger.info(
                f"Initiating AWS SSO login for profile '{self.profile_name}'..."
            )
            subprocess.run(
                ["aws", "sso", "login", "--profile", self.profile_name], check=True
            )
            logger.info("AWS SSO login completed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during AWS SSO login: {e}")
            raise SSOLoginError("Failed to authenticate AWS SSO.") from e
