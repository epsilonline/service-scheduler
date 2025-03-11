import boto3

from utils.logger import get_logger

logger = get_logger('RDSService')

rds = boto3.client("rds")


class RDSClusterService:
    """
    Handles starting/stopping/change desired capacity of an RDS Cluster
    """
    resource_id = ""
    db_cluster_id = ""
    resource_arn = ""
    is_serverless = False

    def __init__(self, db_cluster_id: str, resource_id: str = None, resource_arn: str = None):
        try:
            cluster = rds.describe_db_clusters(DBClusterIdentifier=db_cluster_id)['DBClusters'][0]
            self.db_cluster_id = db_cluster_id
            self.resource_id = resource_id or cluster['DbClusterResourceId']
            self.resource_arn = resource_arn or cluster['DBClusterArn']
            self._is_serverless = 'aurora' in cluster['Engine']
            # if cluster is serverless not have key ScalingConfiguration is v2
            self._is_serverless_v2 = cluster['EngineMode'] != 'serverless' if self._is_serverless else False
        except rds.Client.exceptions.DBClusterNotFoundFault:
            logger.error(f"No cluster found for id: {db_cluster_id}")
            self._is_serverless = False
            self._is_serverless_v2 = False
        finally:
            self.db_cluster_id = db_cluster_id

    def scale_cluster(self, min_capacity: int, max_capacity: int, auto_pause: bool = None):
        """
            Update MinCapacity and MaxCapacity of RDS Cluster
        """
        current_scaling_configuration = self._get_scaling_configuration()
        self._save_parameters(current_scaling_configuration)
        if current_scaling_configuration['MinCapacity'] == min_capacity and \
                current_scaling_configuration['MaxCapacity'] == max_capacity:
            logger.info(f"Skip scaling for {self.db_cluster_id} action because new configuration is equal to current")
        else:
            # Set scaling configuration
            logger.info("Scale RDS")
            self._set_scaling_configuration(min_capacity=min_capacity, max_capacity=max_capacity, auto_pause=auto_pause)
        pass

    def _set_scaling_configuration(self, min_capacity: int, max_capacity: int, auto_pause: bool = None):
        scaling_configuration = {
                'MinCapacity': min_capacity,
                'MaxCapacity': max_capacity
        }

        kwargs = {}
        response = None
        try:
            if self._is_serverless_v2:
                kwargs['ServerlessV2ScalingConfiguration'] = scaling_configuration
            else:
                if auto_pause:
                    scaling_configuration['AutoPause'] = auto_pause
                kwargs['ScalingConfiguration'] = scaling_configuration
            response = rds.modify_db_cluster(DBClusterIdentifier=self.db_cluster_id, ApplyImmediately=True, **kwargs)
        except Exception as e:
            logger.error("Failed to scale RDS")
            logger.error(e)
        return response

    def _get_scaling_configuration(self):
        scaling_configuration = {}

        clusters = rds.describe_db_clusters(DBClusterIdentifier=self.db_cluster_id)

        if self._is_serverless_v2:
            current_scaling_configuration = clusters['DBClusters'][0]['ServerlessV2ScalingConfiguration']
        else:
            current_scaling_configuration = clusters['DBClusters'][0]['ScalingConfigurationInfo']

        scaling_configuration['MinCapacity'] = current_scaling_configuration['MinCapacity']
        scaling_configuration['MaxCapacity'] = current_scaling_configuration['MaxCapacity']

        return scaling_configuration

    def _save_parameters(self, params: dict):
        """ Saves given parameters as an
        """
        pass

    def _get_parameters(self, params: dict):
        """ Retrieve the autoscaling parameters
        """
        pass