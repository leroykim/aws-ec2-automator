# gui/main_gui.py

import tkinter as tk
from tkinter import messagebox, ttk
import threading
import os
import sys
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Ensure core modules are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Updated imports based on refactored core classes
from core.sso_authentication_checker import (
    SSOAuthenticationChecker,
    AuthenticationError,
)
from core.sso_login_handler import SSOLoginHandler, SSOLoginError
from core.ec2_manager import EC2Manager, EC2ManagerError
from core.ssh_config_manager import SSHConfigManager, SSHConfigManagerError
from core.ec2_cost_estimator import EC2CostEstimator, EC2CostEstimatorError
from core.ec2_automator import EC2Automator, EC2AutomatorError
from core.logger import logger


class EC2AutomatorGUI:
    def __init__(self, master):
        self.master = master
        master.title("EC2 Automator")

        # Create input fields
        self.create_input_fields()

        # Create action buttons
        self.create_buttons()

        # Create a status label
        self.status_label = ttk.Label(master, text="Status: Idle", foreground="blue")
        self.status_label.pack(pady=10)

        # Create a label for estimated cost
        self.cost_label = ttk.Label(
            master, text="Estimated Cost: $0.00", foreground="green"
        )
        self.cost_label.pack(pady=5)

        # Initialize EC2Automator
        self.initialize_ec2_automator()

        # Start cost estimation updates
        self.update_cost_estimation()

    def create_input_fields(self):
        frame = ttk.Frame(self.master, padding="10")
        frame.pack(fill=tk.X)

        # AWS Profile
        ttk.Label(frame, text="AWS Profile:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.aws_profile_entry = ttk.Entry(frame)
        self.aws_profile_entry.grid(row=0, column=1, pady=2, sticky=tk.EW)
        self.aws_profile_entry.insert(
            0, os.environ.get("AWS_PROFILE", "your-sso-profile")
        )  # Default value

        # AWS Region
        ttk.Label(frame, text="AWS Region:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.region_entry = ttk.Entry(frame)
        self.region_entry.grid(row=1, column=1, pady=2, sticky=tk.EW)
        self.region_entry.insert(
            0, os.environ.get("AWS_REGION", "us-east-1")
        )  # Default value

        # EC2 Instance ID
        ttk.Label(frame, text="EC2 Instance ID:").grid(
            row=2, column=0, sticky=tk.W, pady=2
        )
        self.instance_id_entry = ttk.Entry(frame)
        self.instance_id_entry.grid(row=2, column=1, pady=2, sticky=tk.EW)
        self.instance_id_entry.insert(
            0, os.environ.get("EC2_INSTANCE_ID", "i-0123456789abcdef0")
        )  # Default value

        # SSH Host Name
        ttk.Label(frame, text="SSH Host Name:").grid(
            row=3, column=0, sticky=tk.W, pady=2
        )
        self.ssh_host_entry = ttk.Entry(frame)
        self.ssh_host_entry.grid(row=3, column=1, pady=2, sticky=tk.EW)
        self.ssh_host_entry.insert(
            0, os.environ.get("SSH_HOST", "your-host-name")
        )  # Default value

        # Configure grid weights
        frame.columnconfigure(1, weight=1)

    def create_buttons(self):
        frame = ttk.Frame(self.master, padding="10")
        frame.pack(fill=tk.X)

        self.start_button = ttk.Button(
            frame, text="Start Instance", command=self.start_instance
        )
        self.start_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.stop_button = ttk.Button(
            frame, text="Stop Instance", command=self.stop_instance
        )
        self.stop_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

    def initialize_ec2_automator(self):
        """
        Initializes the EC2Automator instance based on user input.
        """
        try:
            aws_profile = self.aws_profile_entry.get().strip()
            region = self.region_entry.get().strip()
            instance_id = self.instance_id_entry.get().strip()
            ssh_host = self.ssh_host_entry.get().strip()
            ssh_config_path = os.environ.get("SSH_CONFIG", "~/.ssh/config")

            if not all([aws_profile, region, instance_id, ssh_host]):
                logger.warning(
                    "Incomplete configuration. Cost estimation will not be available."
                )
                self.update_status(
                    "Incomplete configuration. Please fill out all fields.", "orange"
                )
                return

            # Initialize dependencies
            sso_authentication_checker = SSOAuthenticationChecker(
                profile_name=aws_profile
            )
            sso_login_handler = SSOLoginHandler(profile_name=aws_profile)
            ec2_manager = EC2Manager(session=None)  # Pass a boto3 session if needed
            ssh_manager = SSHConfigManager(ssh_config_path=ssh_config_path)
            cost_estimator = EC2CostEstimator(ec2_manager=ec2_manager)

            # Initialize EC2Automator with dependency injection
            self.ec2_automator = EC2Automator(
                sso_authentication_checker=sso_authentication_checker,
                sso_login_handler=sso_login_handler,
                ec2_manager=ec2_manager,
                ssh_manager=ssh_manager,
                cost_estimator=cost_estimator,
                instance_id=instance_id,
                ssh_host_name=ssh_host,
            )

            # Check if instance is running
            current_state = self.ec2_automator.ec2_manager.get_instance_state(
                instance_id
            )
            if current_state == "running":
                logger.info(f"Instance {instance_id} is already running.")
                self.update_status(f"Instance {instance_id} is running.", "green")
                self.update_button_states(current_state)
            else:
                logger.info(f"Instance {instance_id} is not running.")
                self.update_status(f"Instance {instance_id} is not running.", "orange")
                self.update_button_states(current_state)

        except EC2AutomatorError as e:
            logger.error(f"Error during EC2Automator initialization: {e}")
            self.update_status(f"Error initializing EC2Automator: {e}", "red")
            messagebox.showerror("Initialization Error", f"Error: {e}")

        except Exception as e:
            logger.exception("Unexpected error during EC2Automator initialization.")
            self.update_status(f"Unexpected error: {e}", "red")
            messagebox.showerror("Unexpected Error", f"Error: {e}")

    def start_instance(self):
        threading.Thread(target=self._start_instance_thread, daemon=True).start()

    def _start_instance_thread(self):
        self.update_status("Starting instance...", "blue")
        try:
            aws_profile = self.aws_profile_entry.get().strip()
            region = self.region_entry.get().strip()
            instance_id = self.instance_id_entry.get().strip()
            ssh_host = self.ssh_host_entry.get().strip()
            ssh_config_path = os.environ.get("SSH_CONFIG", "~/.ssh/config")

            if not all([aws_profile, region, instance_id, ssh_host]):
                messagebox.showerror("Input Error", "All fields must be filled out.")
                self.update_status("Failed to start instance: Missing input.", "red")
                logger.error("Start Instance: Missing input fields.")
                return

            # Initialize dependencies (if EC2Automator wasn't initialized)
            if not hasattr(self, "ec2_automator"):
                authentication_checker = SSOAuthenticationChecker(
                    profile_name=aws_profile
                )
                sso_login_handler = SSOLoginHandler(profile_name=aws_profile)
                ec2_manager = EC2Manager(session=None)  # Pass a boto3 session if needed
                ssh_manager = SSHConfigManager(ssh_config_path=ssh_config_path)
                cost_estimator = EC2CostEstimator(ec2_manager=ec2_manager)

                self.ec2_automator = EC2Automator(
                    authentication_checker=authentication_checker,
                    sso_login_handler=sso_login_handler,
                    ec2_manager=ec2_manager,
                    ssh_manager=ssh_manager,
                    cost_estimator=cost_estimator,
                    instance_id=instance_id,
                    ssh_host_name=ssh_host,
                )

            # Start the instance workflow
            self.ec2_automator.start_instance_workflow()

            # After starting, check the instance state to confirm
            current_state = self.ec2_automator.ec2_manager.get_instance_state(
                instance_id
            )
            if current_state == "running":
                # Instance is running
                self.update_status(f"Instance {instance_id} is running.", "green")
                messagebox.showinfo(
                    "Instance Status", f"Instance {instance_id} is running."
                )
            else:
                # Instance was started successfully but not yet running
                self.update_status(
                    f"Instance {instance_id} start initiated. Current state: {current_state}.",
                    "green",
                )
                messagebox.showinfo(
                    "Success",
                    f"Instance {instance_id} start initiated.\nCurrent state: {current_state}.",
                )

            logger.info(
                f"Start Instance: Instance {instance_id} state: {current_state}"
            )

            # Update button states based on the new instance state
            self.master.after(0, lambda: self.update_button_states(current_state))

        except EC2AutomatorError as e:
            messagebox.showerror("Error", f"Failed to start instance: {e}")
            self.update_status(f"Failed to start instance: {e}", "red")
            logger.error(f"Start Instance Error: {e}")

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.update_status(f"Failed to start instance: {e}", "red")
            logger.exception("Exception occurred while starting instance.")

    def stop_instance(self):
        threading.Thread(target=self._stop_instance_thread, daemon=True).start()

    def _stop_instance_thread(self):
        self.update_status("Stopping instance...", "blue")
        try:
            aws_profile = self.aws_profile_entry.get().strip()
            region = self.region_entry.get().strip()
            instance_id = self.instance_id_entry.get().strip()
            ssh_config_path = os.environ.get("SSH_CONFIG", "~/.ssh/config")

            if not all([aws_profile, region, instance_id]):
                messagebox.showerror(
                    "Input Error",
                    "AWS Profile, Region, and Instance ID must be filled out.",
                )
                self.update_status("Failed to stop instance: Missing input.", "red")
                logger.error("Stop Instance: Missing input fields.")
                return

            # Initialize dependencies (if EC2Automator wasn't initialized)
            if not hasattr(self, "ec2_automator"):
                ssh_host = self.ssh_host_entry.get().strip()
                authentication_checker = SSOAuthenticationChecker(
                    profile_name=aws_profile
                )
                sso_login_handler = SSOLoginHandler(profile_name=aws_profile)
                ec2_manager = EC2Manager(session=None)  # Pass a boto3 session if needed
                ssh_manager = SSHConfigManager(ssh_config_path=ssh_config_path)
                cost_estimator = EC2CostEstimator(ec2_manager=ec2_manager)

                self.ec2_automator = EC2Automator(
                    authentication_checker=authentication_checker,
                    sso_login_handler=sso_login_handler,
                    ec2_manager=ec2_manager,
                    ssh_manager=ssh_manager,
                    cost_estimator=cost_estimator,
                    instance_id=instance_id,
                    ssh_host_name=ssh_host,
                )

            # Stop the instance workflow
            self.ec2_automator.stop_instance_workflow()

            self.update_status(f"Instance {instance_id} stopped successfully.", "green")
            messagebox.showinfo(
                "Success", f"Instance {instance_id} stopped successfully."
            )
            logger.info(f"Stop Instance: Instance {instance_id} stopped successfully.")

            # After stopping, check the instance state to confirm
            current_state = self.ec2_automator.ec2_manager.get_instance_state(
                instance_id
            )
            self.master.after(0, lambda: self.update_button_states(current_state))

        except EC2AutomatorError as e:
            messagebox.showerror("Error", f"Failed to stop instance: {e}")
            self.update_status(f"Failed to stop instance: {e}", "red")
            logger.error(f"Stop Instance Error: {e}")

        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
            self.update_status(f"Failed to stop instance: {e}", "red")
            logger.exception("Exception occurred while stopping instance.")

    def update_status(self, message, color):
        self.status_label.config(text=f"Status: {message}", foreground=color)

    def update_cost_estimation(self):
        """
        Fetches and updates the estimated cost of the running instance.
        This function schedules itself to run every 600 seconds (10 minutes).
        """
        try:
            if hasattr(self, "ec2_automator") and self.ec2_automator:
                logger.info("Fetching estimated cost...")
                estimated_cost = self.ec2_automator.get_estimated_cost()
                if estimated_cost is not None:
                    self.cost_label.config(
                        text=f"Estimated Cost: ${estimated_cost:.2f}",
                        foreground="green",
                    )
                    logger.info(f"Updated estimated cost: ${estimated_cost:.2f}")
                else:
                    self.cost_label.config(text="Estimated Cost: N/A", foreground="red")
                    logger.warning("Estimated cost is N/A.")
            else:
                self.cost_label.config(text="Estimated Cost: N/A", foreground="gray")
                logger.info("EC2Automator instance not initialized.")
        except EC2CostEstimatorError as e:
            logger.error(f"Cost Estimation Error: {e}")
            self.cost_label.config(text="Estimated Cost: Error", foreground="red")
        except Exception as e:
            logger.error(f"Error updating cost estimation: {e}")
            self.cost_label.config(text="Estimated Cost: Error", foreground="red")

        # Schedule the next update in 600,000 milliseconds (600 seconds)
        self.master.after(
            600000, self.update_cost_estimation
        )  # Update every 600 seconds

    def update_button_states(self, state):
        """
        Enables or disables buttons based on the instance state.

        :param state: str. The current state of the EC2 instance.
        """
        if state == "running":
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update_status("Instance is running.", "green")
        elif state == "stopped":
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.update_status("Instance is stopped.", "blue")
        else:
            # For states like 'pending', 'stopping', etc.
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.DISABLED)
            self.update_status(f"Instance is {state}.", "orange")


class EC2AutomatorError(Exception):
    """Custom exception for EC2Automator-related errors."""

    pass


def main():
    root = tk.Tk()
    app = EC2AutomatorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
