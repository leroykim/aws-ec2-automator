# core/sso_authentication_checker.py

import boto3
from botocore.exceptions import (
    ClientError,
    NoCredentialsError,
    PartialCredentialsError,
    SSOTokenLoadError,
)
from .logger import logger


class AuthenticationError(Exception):
    """
    Custom exception for authentication-related errors.

    Attributes
    ----------
    message : str
        Explanation of the error.
    """

    def __init__(self, message):
        """
        Initialize the AuthenticationError with a message.

        Parameters
        ----------
        message : str
            Explanation of the error.
        """
        super().__init__(message)
        self.message = message


class SSOAuthenticationChecker:
    """
    Checks the authentication status of an AWS session.

    This class verifies whether the provided AWS Single Sign-On (SSO) profile is authenticated
    and can successfully retrieve the caller identity. It utilizes the AWS Security Token Service (STS)
    to validate the authentication status.
    """

    def __init__(self, profile_name):
        """
        Initialize the SSOAuthenticationChecker with a specific AWS CLI profile.

        Parameters
        ----------
        profile_name : str
            The AWS CLI profile name configured for SSO.

        Raises
        ------
        AuthenticationError
            If the provided profile name is invalid or cannot be used to create a session.
        """
        self.profile_name = profile_name
        try:
            self.session = boto3.Session(profile_name=self.profile_name)
            logger.debug(
                f"Initialized boto3 session with profile '{self.profile_name}'."
            )
        except (ClientError, NoCredentialsError, PartialCredentialsError) as e:
            logger.error(
                f"Failed to initialize boto3 session with profile '{self.profile_name}': {e}"
            )
            raise AuthenticationError(
                f"Failed to initialize boto3 session with profile '{self.profile_name}'."
            ) from e

    def is_authenticated(self):
        """
        Check if the AWS session is authenticated by attempting to retrieve caller identity.

        This method attempts to call the AWS STS service to get the caller identity. If successful,
        it indicates that the session is authenticated. Otherwise, it catches exceptions related
        to authentication failures.

        Returns
        -------
        bool
            True if authenticated, False otherwise.

        Raises
        ------
        AuthenticationError
            If there is an unexpected error during the authentication check.
        """
        try:
            sts_client = self.session.client("sts")
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
        except Exception as e:
            logger.exception(f"Unexpected error during authentication check: {e}")
            raise AuthenticationError(
                "An unexpected error occurred during authentication."
            ) from e
