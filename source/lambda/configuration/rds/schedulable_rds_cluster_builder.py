import boto3

from utils.logger import get_logger
from configuration.rds.rds_cluster_handler import RDSClusterHandler

logger = get_logger('SchedulableRDSClustersBuilder')


class SchedulableRDSClustersBuilder:
    """
        Builds a list of schedulable RDS Clusters
    """

    def __init__(self, tag_name: str):
        self._rds_client = boto3.client('rds')
        self._tag_name = tag_name
        self._schedulable_rds_clusters = self._build_schedulable_rds_clusters_list()

    def _build_schedulable_rds_clusters_list(self):

        """
            Identifies the RDS Clusters which have a schedule tag, and so are meant to be scheduled
        """

        schedulable_rds_clusters = []

        rds_clusters_iterator = self._rds_client.get_paginator('describe_db_clusters').paginate()

        for page in rds_clusters_iterator:
            for rds_cluster in page['DBClusters']:
                tags = rds_cluster['TagList']
                filtered_tags = list(filter(lambda x: x['Key'] == self._tag_name, tags))

                if len(filtered_tags) > 0:
                    schedulable_rds_clusters.append(RDSClusterHandler(rds_cluster['DBClusterIdentifier'],
                                                                      filtered_tags[0]['Value']))

        return schedulable_rds_clusters

    @property
    def schedulable_rds_clusters(self):
        return self._schedulable_rds_clusters
