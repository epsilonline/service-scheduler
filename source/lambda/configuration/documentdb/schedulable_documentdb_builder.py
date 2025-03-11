import boto3
import logging

from configuration import logging_level
from configuration.documentdb.documentdb_handler import DocumentDbHandler

logger = logging.getLogger('SchedulableDocumentDBBuilder')
logger.setLevel(logging_level)


class SchedulableDocumentDBBuilder:
    """
        Builds a list of schedulable documentDB clusters
    """

    def __init__(self, tag_name: str):
        self._docdb_client = boto3.client('docdb')
        self._tag_name = tag_name
        self._clusters = self._get_clusters()
        self._schedulable_documentdb = self._build_schedulable_documentdb_list(self._clusters)

    def _get_clusters(self):
        """
        Lists all the cluster in the current account/region
        """
        clusters = []
        documentdb_iterator = self._docdb_client.get_paginator('describe_db_clusters').paginate()

        for page in documentdb_iterator:
            docDbClusters = list(filter(lambda x: x['Engine'] == "docdb", page['DBClusters']))
            for cluster in docDbClusters:
                clusters.append(cluster)

        return clusters

    def _build_schedulable_documentdb_list(self, clusters):

        """
            Among the cluster passed as arguments, identifies the ones which
            have a schedule tag, and so are meant to be scheduled
        """

        schedulable_clusters = []

        for cluster in clusters:
            cluster_arn = cluster['DBClusterArn']
            schedule = self._get_resource_schedule(cluster_arn)
            if schedule is not None:
                ecs_cluster = DocumentDbHandler(cluster_arn, cluster["Status"],schedule)
                schedulable_clusters.append(ecs_cluster)
                logger.debug(f"${cluster_arn} is schedulable")

        return schedulable_clusters

    def _get_resource_schedule(self, resource_arn):

        """
            For a specific cluster passed as arguments, identifies the schedule
            applied to it
        """

        schedule = None

        tags = self._docdb_client.list_tags_for_resource(ResourceName=resource_arn)['TagList']

        logger.debug(f"{tags}")

        if not tags:
            return None

        for tag in tags:
            if tag['Key'] == self._tag_name:
                schedule = tag['Value']

        return schedule

    @property
    def schedulable_documentdb(self):
        return self._schedulable_documentdb
