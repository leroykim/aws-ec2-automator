import os
import shutil
from pathlib import Path
from .logger import logger


class SSHConfigManager:
    """
    Manages SSH configuration file operations.
    """

    def __init__(self, ssh_config_path="~/.ssh/config"):
        """
        Initializes the SSHConfigManager with the path to the SSH config file.

        :param ssh_config_path: str. Path to the SSH config file.
        """
        self.ssh_config_path = Path(ssh_config_path).expanduser()

    def backup_config(self):
        """
        Creates a backup of the SSH config file.

        :return: str or None. Path to the backup file if successful, else None.
        """
        backup_path = self.ssh_config_path.with_suffix(".backup")
        try:
            shutil.copy(self.ssh_config_path, backup_path)
            os.chmod(backup_path, 0o600)
            logger.info(f"Backup of SSH config created at {backup_path}")
            return backup_path
        except IOError as e:
            logger.error(f"Failed to create backup of SSH config: {e}")
            return None

    def update_host(self, host_name, new_dns):
        """
        Updates the Hostname for a specified Host in the SSH config file.

        :param host_name: str. The Host entry in the SSH config to update.
        :param new_dns: str. The new Public IPv4 DNS to set as Hostname.
        """
        try:
            with open(self.ssh_config_path, "r") as file:
                lines = file.readlines()

            with open(self.ssh_config_path, "w") as file:
                in_host_block = False
                host_found = False

                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line.lower().startswith("host "):
                        # Check if this is the host we want to update
                        current_host = stripped_line[5:].strip().lower()
                        if current_host == host_name.lower():
                            in_host_block = True
                            host_found = True
                            file.write(line)
                            continue
                        else:
                            in_host_block = False

                    if in_host_block:
                        if stripped_line.lower().startswith("hostname "):
                            # Replace the Hostname with the new DNS
                            file.write(f"    Hostname {new_dns}\n")
                            in_host_block = False  # Assuming only one Hostname per Host
                            continue

                    # Write the original line if not modifying
                    file.write(line)

                if not host_found:
                    logger.info(
                        f"Host '{host_name}' not found in SSH config. Adding it."
                    )
                    file.write(f"\nHost {host_name}\n")
                    file.write(f"    Hostname {new_dns}\n")

            logger.info(
                f"Updated ~/.ssh/config with new DNS: {new_dns} for Host: {host_name}"
            )

        except IOError as e:
            logger.error(f"Failed to update SSH config: {e}")
