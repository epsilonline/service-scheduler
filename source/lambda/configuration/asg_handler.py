import boto3
import json
from utils.logger import get_logger

logger = get_logger('AsgHandler')

class AsgHandler:
    def __init__(self, tag_name, describeAsgResult):
        tag_object = next(filter(lambda tag: tag['Key'] == tag_name, describeAsgResult["Tags"]), None)
        self._schedule_tag_value = tag_object["Value"]
        self._asg_name = describeAsgResult['AutoScalingGroupName']
        self._arn = describeAsgResult['AutoScalingGroupARN']
        self._min_capacity = describeAsgResult['MinSize']
        self._max_capacity = describeAsgResult['MaxSize']
        self._desired_capacity = describeAsgResult['DesiredCapacity']
        self.ssm = boto3.client("ssm")
        self._asg_client = boto3.client('autoscaling')

    def start(self, **kwargs):

        asgRunning = self.is_running()

        if asgRunning is True:
            logger.debug(f"{self._arn} is already in running state. Nothing to do")
            return

        logger.info(f"starting asg {self._arn}")
        try:
            parameters = self.ssm.get_parameter(Name=f"/asg-shutdown-scheduler/{self._asg_name}")
            parsedParams = json.loads(parameters["Parameter"]["Value"])
            logger.debug(f"restoring capacities to {parsedParams}")

            self._asg_client.update_auto_scaling_group(
                AutoScalingGroupName=self._asg_name,
                MinSize=parsedParams['Minimum'],
                MaxSize=parsedParams['Maximum'],
                DesiredCapacity=parsedParams['Desired']
            )

        except self.ssm.exceptions.ParameterNotFound:
            logger.error(f"Cannot restore configuration for ASG, missing parameter '/asg-shutdown-scheduler/{self._asg_name}'")


    def shutdown(self, **kwargs):

        asgRunning = self.is_running()

        if asgRunning is False:
            logger.debug(f"{self._arn} is already in shutdown state. Nothing to do")
            return

        logger.info(f"shutting down {self._arn}")

        self._save_parameters({
            "Minimum": self._min_capacity,
            "Desired": self._desired_capacity,
            "Maximum": self._max_capacity,
        })

        self._asg_client.update_auto_scaling_group(
            AutoScalingGroupName=self._asg_name,
            MinSize=0,
            MaxSize=0,
            DesiredCapacity=0
        )

    def _save_parameters(self, params: dict):
        """ Saves given parameters as an ssm parameter
        """
        self.ssm.put_parameter(
            Name=f"/asg-shutdown-scheduler/{self._asg_name}",
            Description=f"Original parameter for {self._asg_name}",
            Value=json.dumps(params),
            Type="StringList",
            Overwrite=True,
        )

    def is_running(self):
        return self._desired_capacity > 0

    @property
    def schedule_tag_value(self):
        return self._schedule_tag_value
