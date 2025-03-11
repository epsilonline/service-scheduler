import re
import json
import boto3
from utils.logger import get_logger

logger = get_logger('ECSService')

ssm = boto3.client("ssm")
aas = boto3.client("application-autoscaling")
ecs = boto3.client("ecs")

class ECSService:
    """
    Handles starting/stopping of an ECS service
    """
    cluster_arn = ""
    ecs_cluster_id = ""
    service_arn = ""
    ecs_service_name = ""
    has_autoscaling = False

    def __init__(self, cluster_arn: str, service_arn: str):
        self.cluster_arn = cluster_arn
        self.ecs_cluster_id = re.match(r"arn:aws:ecs:.+:cluster\/(.+)", cluster_arn).group(1)
        self.service_arn = service_arn
        self.ecs_service_name = re.match(r"arn:aws:ecs:.+:service\/(.+)", service_arn).group(1)

        # try to get the scalable target
        aas = boto3.client("application-autoscaling")
        target = aas.describe_scalable_targets(
            ServiceNamespace="ecs",
            ResourceIds=[f"service/{self.ecs_cluster_id}/{self.ecs_service_name}"],
            ScalableDimension="ecs:service:DesiredCount",
        )

        if target["ScalableTargets"]:
            logger.debug(f"Autoscaling configuration detected for service {self.ecs_service_name}.")
            self.target = target
            self.has_autoscaling = True
        else:
            logger.debug(f"No autoscaling configured for service {self.ecs_service_name}")
            self.has_autoscaling = False

    def start(self):
        """ Start the service based on the original parameters from the SSM Parameter Store
        """
        try:
            param = ssm.get_parameter(Name=f"/ecs-shutdown-scheduler/{self.ecs_cluster_id}-{self.ecs_service_name}")
            param = json.loads(param["Parameter"]["Value"])

            if self.has_autoscaling:
                # set min & max ecs tasks back to saved parameter
                aas.register_scalable_target(
                    ServiceNamespace="ecs",
                    ResourceId=f"service/{self.ecs_cluster_id}/{self.ecs_service_name}",
                    ScalableDimension="ecs:service:DesiredCount",
                    MinCapacity=param["Minimum"],
                    MaxCapacity=param["Maximum"],
                )

            # set desired back as well
            self._set_desired_count(param["Desired"])

            logger.info(
                f"'{self.ecs_cluster_id}/{self.ecs_service_name}' Configuration from parameter store was restored: "
                f"{param}"
            )
        except ssm.exceptions.ParameterNotFound:
            logger.error(f"Cannot restore configuration for ASG, missing parameter '/ecs-shutdown-scheduler/{self.ecs_cluster_id}-{self.ecs_service_name}'")

    def shutdown(self):
        """ Shutdown the service and save the original parameters in the SSM Parameter Store
        """
        service_status = ecs.describe_services(cluster=self.cluster_arn, services=[self.ecs_service_name])
        desired_count = service_status["services"][0]["desiredCount"]

        if not desired_count:
            logger.info(f"Service {self.ecs_service_name} is already shutdown. Nothing to do. Skipping...")
            return

        if self.has_autoscaling:
            self._shutdown_with_autoscaling(desired_count)
        else:
            self._shutdown_without_autoscaling(desired_count)

    def _shutdown_without_autoscaling(self, desired_count: int):
        original_params = {
            "Desired": desired_count,
        }

        self._save_parameters(original_params)
        self._set_desired_count(0)

    def _shutdown_with_autoscaling(self, desired_count: int):
        minimum_tasks = self.target["ScalableTargets"][0]["MinCapacity"]
        maximum_tasks = self.target["ScalableTargets"][0]["MaxCapacity"]

        # set min & max ecs tasks to 0 when outside of working hours
        aas.register_scalable_target(
            ServiceNamespace="ecs",
            ResourceId=f"service/{self.ecs_cluster_id}/{self.ecs_service_name}",
            ScalableDimension="ecs:service:DesiredCount",
            MinCapacity=0,
            MaxCapacity=0,
        )

        original_params = {
            "Minimum": minimum_tasks,
            "Desired": desired_count,
            "Maximum": maximum_tasks,
        }

        self._save_parameters(original_params)
        self._set_desired_count(0)

    def is_running(self):
        return self._get_desired_count() > 0

    def _get_desired_count(self):
        service_description = ecs.describe_services(cluster=self.cluster_arn, services=[self.ecs_service_name])
        desired_count = service_description['services'][0]['desiredCount']
        return desired_count

    def _set_desired_count(self, desired_count: int):
        """ Update the desired count of a given service
        """
        ecs.update_service(cluster=self.cluster_arn, service=self.ecs_service_name, desiredCount=desired_count)
        logger.info(f"'{self.ecs_cluster_id}/{self.ecs_service_name}' was set to {desired_count}")

    def _save_parameters(self, params: dict):
        """ Saves given parameters as an ssm parameter
        """
        ssm.put_parameter(
            Name=f"/ecs-shutdown-scheduler/{self.ecs_cluster_id}-{self.ecs_service_name}",
            Description=f"Original parameter for {self.ecs_cluster_id}/{self.ecs_service_name}",
            Value=json.dumps(params),
            Type="StringList",
            Overwrite=True,
        )
        logger.info("Saved configuration to parameter store")
