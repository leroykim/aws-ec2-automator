# core/ssh_config_manager.py

import os
import shutil
from pathlib import Path
from .logger import logger
import tempfile


class SSHConfigManagerError(Exception):
    """Custom exception for SSHConfigManager-related errors."""

    pass


class SSHConfigManager:
    """
    Manages SSH configuration file operations without external parsing libraries.
    """

    def __init__(self, ssh_config_path="~/.ssh/config"):
        """
        Initializes the SSHConfigManager with the path to the SSH config file.

        :param ssh_config_path: str. Path to the SSH config file.
        """
        self.ssh_config_path = Path(ssh_config_path).expanduser()
        self.config_lines = []
        self._load_config()

    def _load_config(self):
        """
        Loads the SSH config file into memory.

        Raises:
            SSHConfigManagerError: If the SSH config file cannot be read.
        """
        try:
            if not self.ssh_config_path.exists():
                logger.warning(
                    f"SSH config file does not exist at {self.ssh_config_path}. Creating a new one."
                )
                self.config_lines = []
                return

            with self.ssh_config_path.open("r") as file:
                self.config_lines = file.readlines()
            logger.info(f"Loaded SSH config from {self.ssh_config_path}")
        except IOError as e:
            logger.error(f"Failed to read SSH config file: {e}")
            raise SSHConfigManagerError("Failed to read SSH config file.") from e

    def backup_config(self):
        """
        Creates a backup of the SSH config file.

        :return: Path. Path to the backup file.
        :raises SSHConfigManagerError: If the backup process fails.
        """
        backup_path = self.ssh_config_path.with_suffix(".backup")
        try:
            shutil.copy(self.ssh_config_path, backup_path)
            os.chmod(backup_path, 0o600)
            logger.info(f"Backup of SSH config created at {backup_path}")
            return backup_path
        except IOError as e:
            logger.error(f"Failed to create backup of SSH config: {e}")
            raise SSHConfigManagerError("Failed to backup SSH config.") from e

    def update_host(self, host_name, new_dns):
        """
        Updates the Hostname for a specified Host in the SSH config file.
        If the Host does not exist, it adds a new Host block.

        :param host_name: str. The Host entry in the SSH config to update.
        :param new_dns: str. The new Public IPv4 DNS to set as Hostname.
        :raises SSHConfigManagerError: If the update process fails.
        """
        try:
            updated = False
            in_target_host_block = False
            new_config_lines = []
            logger.info(f"Updating Host '{host_name}' with new DNS '{new_dns}'.")

            for line in self.config_lines:
                stripped_line = line.strip()
                if stripped_line.lower().startswith("host "):
                    current_host = stripped_line[5:].strip().lower()
                    if current_host == host_name.lower():
                        in_target_host_block = True
                        logger.debug(f"Found Host block for '{host_name}'.")
                    else:
                        in_target_host_block = False

                if in_target_host_block and stripped_line.lower().startswith(
                    "hostname "
                ):
                    # Replace the Hostname line with the new DNS
                    indentation = line[: line.find("Hostname")]
                    new_line = f"{indentation}Hostname {new_dns}\n"
                    new_config_lines.append(new_line)
                    updated = True
                    logger.debug(
                        f"Replaced Hostname for '{host_name}' with '{new_dns}'."
                    )
                    continue

                new_config_lines.append(line)

            if not updated:
                # Host not found or Hostname not present; add Host block
                logger.info(
                    f"Host '{host_name}' not found or Hostname not present. Adding new Host block."
                )
                new_config_lines.append(f"\nHost {host_name}\n")
                new_config_lines.append(f"    Hostname {new_dns}\n")
                updated = True

            if updated:
                # Write the updated config to a temporary file first
                with tempfile.NamedTemporaryFile("w", delete=False) as tmp_file:
                    tmp_file.writelines(new_config_lines)
                    temp_path = Path(tmp_file.name)

                # Atomically replace the original config with the updated one
                shutil.move(str(temp_path), self.ssh_config_path)
                logger.info(f"SSH config updated successfully for Host '{host_name}'.")
                # Reload the config to reflect changes in memory
                self._load_config()
            else:
                logger.warning(f"No changes made to SSH config for Host '{host_name}'.")

        except Exception as e:
            logger.error(f"Failed to update SSH config: {e}")
            raise SSHConfigManagerError("Failed to update SSH config.") from e
