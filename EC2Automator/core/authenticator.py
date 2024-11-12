# core/authenticator.py

import boto3
import subprocess
import sys
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    SSOTokenLoadError,
)
from .logger import logger


class SSOAuthenticator:
    """
    Handles AWS SSO authentication.
    """

    def __init__(self, profile_name):
        """
        Initializes the SSOAuthenticator with a specific AWS CLI profile.

        :param profile_name: str. The AWS CLI profile name configured for SSO.
        """
        self.profile_name = profile_name

    def is_authenticated(self):
        """
        Checks if the AWS session is authenticated by attempting to retrieve caller identity.

        :return: bool. True if authenticated, False otherwise.
        """
        try:
            session = boto3.Session(profile_name=self.profile_name)
            sts_client = session.client("sts")
            sts_client.get_caller_identity()
            logger.info("AWS session is authenticated.")
            return True
        except (
            NoCredentialsError,
            ClientError,
            PartialCredentialsError,
            SSOTokenLoadError,
        ) as e:
            logger.warning(f"AWS session is not authenticated: {e}")
            return False

    def login(self):
        """
        Performs AWS SSO login using the AWS CLI.

        Raises:
            SystemExit: If the login process fails.
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
            sys.exit(1)
