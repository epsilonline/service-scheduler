import boto3

from utils.logger import get_logger
from configuration.rds.rds_cluster_service import RDSClusterService


logger = get_logger('RDSClusterHandler')

class RDSClusterHandler:
    """
        Handles start/stop of eECS clusters
    """
    def __init__(self, cluster_id, schedule_tag_value):
        self._rds_client = boto3.client("rds")
        self._cluster_id = cluster_id
        self._schedule_tag_value = schedule_tag_value
        self._cluster_service = RDSClusterService(cluster_id)

    def start(self, **kwargs):
        """
        Set autoscaling configuration with start_min_capacity and start_max_capacity
        :return:
        """
        logger.debug(f"[Start] - Prepare to set autoscaling configuration for {self._cluster_id}")
        self._cluster_service.scale_cluster(min_capacity=kwargs['min_capacity'], max_capacity=kwargs['max_capacity'])

    def shutdown(self, **kwargs):
        """
        Set autoscaling configuration with stop_min_capacity and stop_max_capacity
        :return:
        """
        logger.debug(f"[Stop] - Prepare to set autoscaling configuration for {self._cluster_id}")
        self._cluster_service.scale_cluster(min_capacity=kwargs['min_capacity'], max_capacity=kwargs['max_capacity'])

    @property
    def schedule_tag_value(self):
        return self._schedule_tag_value

    def __repr__(self):
        return f"Cluster: '{self._cluster_id}', schedule tag Value: '{self._schedule_tag_value}'"
