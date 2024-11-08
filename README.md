# aws-ec2-automator

## Features
### When instance state == stopped
- Starts corresponding instance with one button click.
- Updates `Hostname` of corresponding `Host` in `~/.ssh/config`. This relieves hassles to check updated `Public IPv4 DNS` every time when we start an EC2 instance.
    ```bash
    # ~/.ssh/config
    Host aws-ec2-96
        Hostname ec2-xx-yyy-zz-www.compute-1.amazonaws.com
        User ubuntu
        IdentityFile /Users/username/.ssh/aws.pem
    ```
### When instance state == running
- Tracks estimated price from the starting time.
- Tracks instance state.
- Stops corresponding instance with one button click.

## How to run it
1. Create `.env` under `EC2Automator` directory.
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
2. This is the sample `.env` contents. Do not change environment variable names, e.g., `EC2_INSTANCE_ID`. Change their values only, e.g., `i-0123456789abcdef0`.
```bash
# EC2Automator/.env
EC2_INSTANCE_ID=i-0123456789abcdef0
AWS_PROFILE=your-sso-profile
AWS_REGION=us-east-1
SSH_CONFIG=~/.ssh/config
SSH_HOST=aws-ec2-test
```

3. Run `python3 EC2Automator/gui/main_gui.py`

## TODO
- [ ] Add environment setup information.
- [ ] Add screenshots.