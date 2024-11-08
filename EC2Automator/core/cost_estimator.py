import boto3
from botocore.exceptions import ClientError
from .logger import logger
from datetime import datetime, timezone
import math
import json


class EC2CostEstimator:
    """
    Estimates the cost of running an EC2 instance based on its start time and instance type.
    """

    def __init__(self, profile_name, region):
        """
        Initializes the EC2CostEstimator with the necessary AWS profile and region.

        :param profile_name: str. The AWS CLI profile name.
        :param region: str. AWS region where the instance is located.
        """
        self.session = boto3.Session(profile_name=profile_name, region_name=region)
        self.ec2_client = self.session.client("ec2")
        self.pricing_client = self.session.client(
            "pricing", region_name="us-east-1"
        )  # Pricing API is available in us-east-1
        self.cache = {}  # Cache to store pricing information to minimize API calls
        logger.info(
            f"Initialized EC2CostEstimator for profile '{profile_name}' in region '{region}'."
        )

    def get_instance_type(self, instance_id):
        """
        Retrieves the instance type of the specified EC2 instance.

        :param instance_id: str. The ID of the EC2 instance.
        :return: str or None. The instance type (e.g., 't2.micro'), or None if not found.
        """
        try:
            logger.info(f"Fetching instance type for {instance_id}.")
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            instance_type = instance["InstanceType"]
            logger.info(f"Instance {instance_id} is of type: {instance_type}")
            return instance_type
        except ClientError as e:
            logger.error(f"Error fetching instance type for {instance_id}: {e}")
            return None

    def get_launch_time(self, instance_id):
        """
        Retrieves the launch time of the specified EC2 instance.

        :param instance_id: str. The ID of the EC2 instance.
        :return: datetime or None. The launch time in UTC, or None if not found.
        """
        try:
            logger.info(f"Fetching launch time for {instance_id}.")
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response["Reservations"][0]["Instances"][0]
            launch_time = instance["LaunchTime"]
            logger.info(f"Instance {instance_id} launch time: {launch_time}")
            return launch_time
        except ClientError as e:
            logger.error(f"Error fetching launch time for {instance_id}: {e}")
            return None

    def calculate_running_hours(self, launch_time):
        """
        Calculates the running hours of the instance based on the launch time.

        :param launch_time: datetime. The UTC launch time of the instance.
        :return: float. The elapsed time in hours, rounded up.
        """
        current_time = datetime.now(timezone.utc)
        elapsed_time = current_time - launch_time
        # elapsed_hours = math.ceil(elapsed_time.total_seconds() / 3600)
        elapsed_hours = elapsed_time.total_seconds() / 3600
        logger.info(f"Instance has been running for {elapsed_hours} hours.")
        return elapsed_hours

    def get_hourly_rate(self, instance_type):
        """
        Retrieves the current hourly rate for the specified instance type using the AWS Pricing API.

        :param instance_type: str. The instance type (e.g., 't2.micro').
        :return: float or None. The hourly rate in USD, or None if not found.
        """
        # Check if the rate is already cached
        if instance_type in self.cache:
            logger.info(
                f"Using cached hourly rate for {instance_type}: ${self.cache[instance_type]:.4f}"
            )
            return self.cache[instance_type]

        try:
            logger.info(f"Fetching hourly rate for instance type: {instance_type}")
            # The AWS Pricing API requires specific filters to retrieve accurate pricing information
            response = self.pricing_client.get_products(
                ServiceCode="AmazonEC2",
                Filters=[
                    {
                        "Type": "TERM_MATCH",
                        "Field": "instanceType",
                        "Value": instance_type,
                    },
                    {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
                    {
                        "Type": "TERM_MATCH",
                        "Field": "operatingSystem",
                        "Value": "Linux",
                    },
                    {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                    {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
                ],
                FormatVersion="aws_v1",
                MaxResults=1,
            )

            if not response["PriceList"]:
                logger.warning(
                    f"No pricing information found for instance type: {instance_type}"
                )
                return None

            price_item = json.loads(response["PriceList"][0])

            # Navigate the JSON structure to find the On-Demand price
            on_demand = price_item["terms"]["OnDemand"]
            for key in on_demand:
                price_dimensions = on_demand[key]["priceDimensions"]
                for pd_key in price_dimensions:
                    pd = price_dimensions[pd_key]
                    description = pd.get("description", "")
                    unit = pd.get("unit", "")
                    price_per_unit = pd["pricePerUnit"]["USD"]
                    logger.info(
                        f"Price Dimension: {description}, Unit: {unit}, Price per Unit: ${price_per_unit}"
                    )
                    hourly_rate = float(price_per_unit)
                    self.cache[instance_type] = hourly_rate  # Cache the rate
                    return hourly_rate

            logger.warning(f"Unable to parse pricing information for {instance_type}")
            return None

        except ClientError as e:
            logger.error(f"Error fetching hourly rate for {instance_type}: {e}")
            return None

    def estimate_cost(self, instance_id):
        """
        Estimates the current cost of the running instance based on its type and launch time.

        :param instance_id: str. The ID of the EC2 instance.
        :return: float or None. The estimated cost in USD, or None if estimation failed.
        """
        try:
            logger.info(f"Estimating cost for instance {instance_id}.")
            # Get instance type and launch time
            instance_type = self.get_instance_type(instance_id)
            if not instance_type:
                logger.error("Cannot estimate cost without instance type.")
                return None

            launch_time = self.get_launch_time(instance_id)
            if not launch_time:
                logger.error("Cannot estimate cost without launch time.")
                return None

            # Calculate running hours
            running_hours = self.calculate_running_hours(launch_time)

            # Get hourly rate
            hourly_rate = self.get_hourly_rate(instance_type)
            if hourly_rate is None:
                logger.error("Cannot estimate cost without hourly rate.")
                return None

            # Calculate estimated cost
            estimated_cost = running_hours * hourly_rate
            logger.info(
                f"Estimated cost for instance {instance_id} is ${estimated_cost:.2f}"
            )
            return estimated_cost

        except Exception as e:
            logger.error(f"Error during cost estimation for {instance_id}: {e}")
            return None
