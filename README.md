# EC2 Automator

<!-- ![EC2 Automator Logo](path_to_logo_image.png) -->

## Table of Contents

- [EC2 Automator](#ec2-automator)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Features](#features)
  - [Installation](#installation)
    - [Prerequisites](#prerequisites)
    - [Steps](#steps)
  - [Configuration](#configuration)
  - [Usage](#usage)
    - [GUI Overview](#gui-overview)
    - [Component Breakdown](#component-breakdown)
    - [Operational Workflow](#operational-workflow)
      - [1. Starting an EC2 Instance](#1-starting-an-ec2-instance)
      - [2. Stopping an EC2 Instance](#2-stopping-an-ec2-instance)
    - [Real-Time Cost Monitoring](#real-time-cost-monitoring)
  - [Logging](#logging)
    - [Log file example](#log-file-example)
  - [License](#license)
  - [Contact](#contact)

## Introduction

**EC2 Automator** is a user-friendly desktop application designed to streamline the management of your Amazon EC2 instances. Whether you're a developer, system administrator, or IT professional, EC2 Automator simplifies the process of starting, stopping, and monitoring your EC2 instances directly from a graphical interface. Additionally, it seamlessly updates your SSH configuration and provides real-time cost estimations, ensuring efficient and cost-effective cloud resource management.

## Features

- **Start and Stop EC2 Instances**: Easily initiate or terminate your EC2 instances with just a click.
- **Real-Time Status Monitoring**: Stay informed about the current state of your instances (`running`, `stopped`, `stopping`, etc.).
- **SSH Configuration Management**: Automatically updates your SSH config file to reflect the public DNS of your instances, facilitating seamless SSH access.
- **Cost Estimation**: Receive real-time estimations of your EC2 instance costs to manage your budget effectively.
- **User-Friendly Interface**: Intuitive GUI built with Tkinter, ensuring ease of use for both beginners and experienced users.
- **Threaded Operations**: Performs long-running operations in separate threads to maintain a responsive interface.
- **Robust Error Handling**: Comprehensive error notifications and status updates to keep you informed about the application's operations.

<!-- ## Screenshots

![Main Interface](path_to_main_interface_screenshot.png)
*Main interface of EC2 Automator showcasing the start and stop buttons, status label, and cost estimation.*

![Starting Instance](path_to_starting_instance_screenshot.png)
*Notification displayed when an instance is in the process of starting.*

![Instance Running](path_to_instance_running_screenshot.png)
*Status update indicating that the instance is running.* -->

## Installation

### Prerequisites

- Python 3.8 or higher

### Steps

Follow these simple steps to set up and run the **EC2 Automator** application on your local machine:

1. **Clone the Repository**

   Begin by cloning the EC2 Automator repository from GitHub to your local machine.

   ```bash
   git clone https://github.com/leroykim/aws-ec2-automator
   ```

2. **Navigate to the Project Directory**

   Change your current directory to the newly cloned repository.

   ```bash
   cd aws-ec2-automator
   ```

3. **Make the Installation Script Executable**

   Modify the permissions of the `installation.sh` script to make it executable. This script typically sets up the virtual environment and installs necessary dependencies.

   ```bash
   chmod +x installation.sh
   ```

4. **Run the Installation Script**

   Execute the installation script to set up the virtual environment and install all required Python packages.

   ```bash
   ./installation.sh
   ```

   *Ensure you understand its contents before execution.*

5. **Activate the Virtual Environment**

   Activate the Python virtual environment to ensure that all dependencies are correctly managed and isolated from your system-wide Python installation.

   ```bash
   source .venv/bin/activate
   ```

   *After activation, your terminal prompt will typically change to indicate that you're now working within the virtual environment.*

6. **Set Up Environment Variables**

   Create a `.env` file in the root directory of the project with the following content:

   ```bash
    EC2Automator/
    ├── core/
    │   ├── __init__.py
    │   ├── authenticator.py
    │   ├── ec2_manager.py
    │   ├── ssh_config_manager.py
    │   ├── ec2_automator.py
    │   └── logger.py
    ├── gui/
    │   ├── __init__.py
    │   └── main_gui.py
    └── .env  # Create .env here to provide AWS EC2 instance information.
    ```

   ```env
   AWS_PROFILE=your-sso-profile
   AWS_REGION=us-east-1
   EC2_INSTANCE_ID=i-0123456789abcdef0
   SSH_HOST=your-host-name
   SSH_CONFIG=~/.ssh/config
   ```

   - **AWS_PROFILE**: Your AWS SSO profile name.
   - **AWS_REGION**: The AWS region where your EC2 instances are located.
   - **EC2_INSTANCE_ID**: The ID of the EC2 instance you want to manage.
   - **SSH_HOST**: The Host entry name in your SSH config.
   - **SSH_CONFIG**: Path to your SSH config file.

7. **Launch the EC2 Automator Application**

   With the virtual environment activated, you can now start the EC2 Automator GUI application.

   ```bash
   python EC2Automator/gui/main_gui.py
   ```

   *The GUI should launch, allowing you to manage your EC2 instances with ease.*

## Configuration

1. **AWS Credentials**

   Ensure that your AWS credentials are properly configured. You can set up AWS SSO profiles using the AWS CLI:

   ```bash
   aws configure sso
   ```

   Follow the prompts to set up your SSO profile.

2. **SSH Configuration**

   The application will automatically create a backup of your existing SSH config file before making any changes. Ensure that the path to your SSH config is correctly specified in the `.env` file.

## Usage

### GUI Overview

```
+--------------------------------------------------------------+
|                          EC2 Automator                       |
+--------------------------------------------------------------+
|                                                              |
|  AWS Profile:     [__________________________]               |
|                                                              |
|  AWS Region:      [__________________________]               |
|                                                              |
|  EC2 Instance ID: [__________________________]               |
|                                                              |
|  SSH Host Name:   [__________________________]               |
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|         [ Start Instance ]         [ Stop Instance ]         |
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|                  Status: Instance is running                 |
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|                     Estimated Cost: $1.97                    |
|                                                              |
+--------------------------------------------------------------+
```

### Component Breakdown

1. **AWS Profile**
   - **Description**: Enter or select your AWS Single Sign-On (SSO) profile.
   - **Usage**: This profile is used to authenticate your AWS credentials securely.

2. **AWS Region**
   - **Description**: Specify the AWS region where your EC2 instances are hosted (e.g., `us-east-1`).
   - **Usage**: Determines the geographical location of the resources you intend to manage.

3. **EC2 Instance ID**
   - **Description**: Input the unique identifier of the EC2 instance you wish to control (e.g., `i-0123456789abcdef0`).
   - **Usage**: Specifies the exact instance to start or stop.

4. **SSH Host Name**
   - **Description**: Define the Host entry name in your SSH configuration for streamlined access.
   - **Usage**: Facilitates quick and easy SSH connections to your EC2 instances without repeatedly entering the public DNS.

5. **Start Instance Button**
   - **Description**: Initiates the start operation for the specified EC2 instance.
   - **Usage**:
     - **Click** to start the instance.
     - The application will display a notification once the instance is running.
     - The **Stop Instance** button will be enabled, allowing you to stop the instance if needed.

6. **Stop Instance Button**
   - **Description**: Initiates the stop operation for the specified EC2 instance.
   - **Usage**:
     - **Click** to stop the instance.
     - The button will be **disabled** while the instance is in the process of stopping to prevent multiple stop commands.
     - A notification will appear once the instance has been successfully stopped.

7. **Status Label**
   - **Description**: Displays the current status of the EC2 instance.
   - **Usage**:
     - **Idle**: No ongoing operations.
     - **Starting...**: Instance is in the process of starting.
     - **Running**: Instance is active and running.
     - **Stopping...**: Instance is in the process of stopping.
     - **Stopped**: Instance has been successfully stopped.
     - **Error**: An error occurred during an operation.

8. **Estimated Cost Label**
   - **Description**: Shows the real-time estimated cost of running the EC2 instance.
   - **Usage**:
     - Provides an approximate cost based on the instance's specifications and usage.
     - Updates periodically to reflect any changes in cost estimates.

### Operational Workflow

#### 1. Starting an EC2 Instance

1. **Enter Required Details**:
   - Input your AWS Profile, Region, EC2 Instance ID, and SSH Host Name in the respective fields.

2. **Initiate Start Operation**:
   - Click the **Start Instance** button.
   - The **Status Label** will update to indicate that the instance is starting (`Starting...`).
   - The application will wait until the instance transitions to the `running` state.

3. **Completion Notification**:
   - Once the instance is running, a notification will appear confirming the successful start.
   - The **Status Label** will update to `Running`.
   - The **Stop Instance** button will become enabled, allowing you to stop the instance if desired.

#### 2. Stopping an EC2 Instance

1. **Initiate Stop Operation**:
   - With the instance running, click the **Stop Instance** button.
   - The **Status Label** will update to indicate that the instance is stopping (`Stopping...`).
   - The **Stop Instance** button will be disabled to prevent multiple stop commands.

2. **Completion Notification**:
   - Once the instance is stopped, a notification will appear confirming the successful stop.
   - The **Status Label** will update to `Stopped`.
   - The **Start Instance** button will become enabled, allowing you to start the instance again if needed.

### Real-Time Cost Monitoring

- The **Estimated Cost Label** provides a real-time approximation of the running costs associated with your EC2 instance.
- This feature helps in monitoring and managing your AWS expenses effectively.
- The cost estimation updates automatically at regular intervals to reflect the most recent data.

## Logging

EC2 Automator maintains detailed logs to help you monitor operations and troubleshoot any issues that may arise. These log files are stored in the following directory: `EC2Automator/logs/`

### Log file example

```
2024-11-12 14:04:08,054 - core.logger - INFO - Initialized EC2Manager for profile 'user-profile' in region 'us-east-1'.
2024-11-12 14:04:08,054 - core.logger - INFO - Loaded SSH config from /Users/user1/.ssh/config
2024-11-12 14:04:08,056 - core.logger - INFO - Initialized EC2CostEstimator using EC2Manager for profile 'user-profile' in region 'us-east-1'.
2024-11-12 14:04:08,139 - botocore.tokens - INFO - Loading cached SSO token for aws_cri
2024-11-12 14:04:08,641 - core.logger - INFO - AWS session is authenticated.
```

## License

Distributed under the GPLv3 License. See [`LICENSE`](./LICENSE) for more information.

## Contact

- **Dae-young Kim (Leroy)**
- **Email**: leroy.kim@umbc.edu, dkim1@childrensnational.org
- **GitHub**: [@leroykim](https://github.com/leroykim)
- **LinkedIn**: [@leroykim](https://www.linkedin.com/in/leroykim/)