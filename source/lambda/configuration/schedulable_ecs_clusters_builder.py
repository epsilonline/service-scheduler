import boto3
from utils.logger import get_logger

from configuration.ecs_cluster_handler import EcsClusterHandler


logger = get_logger('SchedulableEcsClustersBuilder')
class SchedulableEcsClustersBuilder:
    """
        Holds the informations about a list of schedulable ECS cluster
    """

    def __init__(self, tag_name: str):
        self._ecs_client = boto3.client("ecs")
        self._tag_name = tag_name
        self._cluster_arns = self._get_clusters_arn()
        self._schedulable_clusters = self._build_schedulable_clusters_list(self._cluster_arns)

    def _get_clusters_arn(self):
        """
        Lists all the cluster in the current account/region
        """
        clusters_arn = []
        clusters_iterator = self._ecs_client.get_paginator('list_clusters').paginate()

        for cluster in clusters_iterator:
            clusters_arn += cluster['clusterArns']

        return clusters_arn

    def _build_schedulable_clusters_list(self, cluster_arns):

        """
            Among the cluster passed as arguments, identifies the ones which
            have a schedule tag, and so are meant to be scheduled
        """

        schedulable_clusters = []

        for cluster_arn in cluster_arns:
            schedule = self._get_resource_schedule(cluster_arn)
            if schedule is not None:
                ecs_cluster = EcsClusterHandler(cluster_arn, schedule)
                schedulable_clusters.append(ecs_cluster)
                logger.debug(f"${cluster_arn} is schedulable")

        return schedulable_clusters

    def _get_resource_schedule(self, resource_arn):

        """
            For a specific cluster passed as arguments, identifies the schedule
            applied to it
        """

        schedule = None

        tags = self._ecs_client.list_tags_for_resource(resourceArn=resource_arn)['tags']

        if not tags:
            return None

        for tag in tags:
            if tag['key'] == self._tag_name:
                schedule = tag['value']

        return schedule

    @property
    def schedulable_clusters(self):
        return self._schedulable_clusters
