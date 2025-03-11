import boto3

import logging

# from configuration.ecs_service import ECSService

from configuration import logging_level
logger = logging.getLogger('DocumentDbHandler')
logger.setLevel(logging_level)

class DocumentDbHandler:
    """
        Handles start/stop of eECS clusters
    """
    def __init__(self, cluster_arn, cluster_status,schedule_tag_value):
        self._docdb_client = boto3.client('docdb')
        self._cluster_status = cluster_status
        self._cluster_arn = cluster_arn
        self._schedule_tag_value = schedule_tag_value

    def start(self, **kwargs):

        clusterRunning = self.is_running()

        if clusterRunning is True:
            logger.debug(f"{self._cluster_arn} is already in running state. Nothing to do")
            return

        self._docdb_client.start_db_cluster(
            DBClusterIdentifier=self._cluster_arn
        )

        logger.info(f"starting asg {self._cluster_arn}")


    def shutdown(self, **kwargs):

        clusterRunning = self.is_running()

        if clusterRunning is False:
            logger.debug(f"{self._cluster_arn} is already in shutdown state. Nothing to do")
            return

        logger.info(f"shutting down {self._cluster_arn}")

        self._docdb_client.stop_db_cluster(
            DBClusterIdentifier=self._cluster_arn
        )



    def is_running(self):
        return self._cluster_status != "stopped"

    @property
    def schedule_tag_value(self):
        return self._schedule_tag_value

    def __str__(self):
        return f'{self._cluster_arn}'
