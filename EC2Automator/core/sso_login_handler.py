# core/sso_login_handler.py

import subprocess
from .logger import logger


class SSOLoginError(Exception):
    """
    Custom exception for SSO login-related errors.

    Attributes
    ----------
    message : str
        Explanation of the error.
    """

    def __init__(self, message):
        """
        Initialize the SSOLoginError with a message.

        Parameters
        ----------
        message : str
            Explanation of the error.
        """
        super().__init__(message)
        self.message = message


class SSOLoginHandler:
    """
    Manages the AWS SSO login process.

    This class handles the authentication process for AWS Single Sign-On (SSO) profiles
    by invoking the AWS CLI command to perform the login. It ensures that the specified
    AWS CLI profile is authenticated and ready for use in subsequent AWS service operations.
    """

    def __init__(self, profile_name):
        """
        Initialize the SSOLoginHandler with a specific AWS CLI profile.

        Parameters
        ----------
        profile_name : str
            The AWS CLI profile name configured for SSO.

        Raises
        ------
        ValueError
            If the provided profile_name is not a non-empty string.
        """
        if not isinstance(profile_name, str) or not profile_name.strip():
            logger.error("Invalid profile name provided for SSOLoginHandler.")
            raise ValueError("profile_name must be a non-empty string.")

        self.profile_name = profile_name
        logger.debug(f"SSOLoginHandler initialized for profile '{self.profile_name}'.")

    def login(self):
        """
        Perform AWS SSO login using the AWS CLI.

        This method executes the AWS CLI command to initiate the SSO login process
        for the specified profile. It ensures that the login process completes successfully.
        If the login fails, it raises a `SSOLoginError`.

        Raises
        ------
        SSOLoginError
            If the login process fails due to subprocess errors or non-zero exit codes.
        """
        try:
            logger.info(
                f"Initiating AWS SSO login for profile '{self.profile_name}'..."
            )
            subprocess.run(
                ["aws", "sso", "login", "--profile", self.profile_name],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            logger.info("AWS SSO login completed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error during AWS SSO login: {e.stderr.strip()}")
            raise SSOLoginError("Failed to authenticate AWS SSO.") from e
        except FileNotFoundError:
            logger.error(
                "AWS CLI not found. Please ensure it is installed and in PATH."
            )
            raise SSOLoginError("AWS CLI not found. Please install it and try again.")
        except Exception as e:
            logger.exception("An unexpected error occurred during AWS SSO login.")
            raise SSOLoginError(
                "An unexpected error occurred during AWS SSO login."
            ) from e
