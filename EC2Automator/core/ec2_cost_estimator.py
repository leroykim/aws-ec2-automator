# core/ec2_cost_estimator.py

import json
from botocore.exceptions import ClientError
from .logger import logger
from datetime import datetime, timezone


class EC2CostEstimator:
    """
    Estimates the cost of running an EC2 instance based on its start time and instance type.
    """

    def __init__(self, ec2_manager):
        """
        Initializes the EC2CostEstimator with the EC2Manager instance.

        :param ec2_manager: EC2Manager. An instance of EC2Manager to manage EC2 operations.
        """
        self.ec2_manager = ec2_manager
        self.pricing_client = self.ec2_manager.session.client(
            "pricing", region_name="us-east-1"
        )  # Pricing API is available in us-east-1
        self.cache = {}  # Cache to store pricing information to minimize API calls
        logger.info(
            f"Initialized EC2CostEstimator using EC2Manager for profile '{self.ec2_manager.session.profile_name}' in region '{self.ec2_manager.session.region_name}'."
        )

    def calculate_running_hours(self, launch_time):
        """
        Calculates the running hours of the instance based on the launch time.

        :param launch_time: datetime. The UTC launch time of the instance.
        :return: float. The elapsed time in hours.
        """
        current_time = datetime.now(timezone.utc)
        elapsed_time = current_time - launch_time
        elapsed_hours = elapsed_time.total_seconds() / 3600
        logger.info(f"Instance has been running for {elapsed_hours:.2f} hours.")
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

            # Get instance state using EC2Manager
            state = self.ec2_manager.get_instance_state(instance_id)
            if state != "running":
                logger.info(
                    f"Instance {instance_id} is not running (state: {state}). Estimated cost: $0.00"
                )
                return 0.0

            # Get instance type and launch time using EC2Manager
            instance_type = self.ec2_manager.get_instance_type(instance_id)
            if not instance_type:
                logger.error("Cannot estimate cost without instance type.")
                return None

            launch_time = self.ec2_manager.get_launch_time(instance_id)
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
