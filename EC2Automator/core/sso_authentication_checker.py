# core/authenticator.py

import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    SSOTokenLoadError,
)
from .logger import logger


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""

    pass


class SSOAuthenticationChecker:
    """
    Checks the authentication status of an AWS session.
    """

    def __init__(self, profile_name):
        """
        Initializes the AuthenticationChecker with a specific AWS CLI profile.

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
