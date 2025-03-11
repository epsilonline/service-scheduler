import boto3

from utils.logger import get_logger

from configuration.ecs_service import ECSService

from configuration import logging_level
logger = get_logger('EcsClusterHandler')
logger.setLevel(logging_level)

class EcsClusterHandler:
    """
        Handles start/stop of eECS clusters
    """
    def __init__(self, cluster_arn, schedule_tag_value):
        self._ecs_client = boto3.client("ecs")
        self._cluster_arn = cluster_arn
        self._schedule_tag_value = schedule_tag_value
        self.cluster_services_arn = self._get_cluster_services_arn(self._cluster_arn)

    def _get_cluster_services_arn(self, cluster_arn):

        """
            For the cluster passed as arguments, lists all of its services
        """
        service_arns = []

        service_iterator = self._ecs_client.get_paginator('list_services').paginate(
            cluster=cluster_arn
        )

        for page in service_iterator:
            service_arns += page['serviceArns']

        return service_arns

    def start(self, **kwargs):
        """
        Starts a cluster by starting all of its services
        :return:
        """

        logger.debug(f"starting cluster {self._cluster_arn}")
        for service_arn in self.cluster_services_arn:
            service = ECSService(self._cluster_arn, service_arn)

            is_service_running = service.is_running()

            logger.debug(f'service arn: {service_arn}')
            logger.debug(f'service running? {is_service_running}')

            try:
                self._update_service_status(service, is_service_running, True)
            except boto3.client("ssm").exceptions.ParameterNotFound as e:
                logger.error(f"{e}")
                continue

    def shutdown(self, **kwargs):
        """
        Shuts down an ECS cluster by shutting down all of its services
        :return:
        """
        logger.debug(f"shutting down cluster {self._cluster_arn}")
        for service_arn in self.cluster_services_arn:
            service = ECSService(self._cluster_arn, service_arn)

            is_service_running = service.is_running()

            logger.debug(f'service arn: {service_arn}')
            logger.debug(f'service running? {is_service_running}')

            try:
                self._update_service_status(service, is_service_running, False)
            except boto3.client("ssm").exceptions.ParameterNotFound as e:
                logger.error(f"{e}")
                continue

    def _update_service_status(self, service: ECSService, is_service_running: bool, service_should_be_running: bool):

        if is_service_running is False and service_should_be_running is False:
            logger.debug('nothing to do')
        elif is_service_running is False and service_should_be_running is True:
            logger.info(f'starting service {service.service_arn}')
            service.start()
        elif is_service_running is True and service_should_be_running is False:
            logger.info(f'stopping service {service.service_arn}')
            service.shutdown()
        elif is_service_running is True and service_should_be_running is True:
            logger.debug('nothing to do')

    @property
    def schedule_tag_value(self):
        return self._schedule_tag_value
