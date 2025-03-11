from boto3 import client, resource
import os
from utils.logger import get_logger

logger = get_logger('FixRDSCluster')

rds_client = client("rds")
sts_client = client("sts")
dynamodb_resource = resource("dynamodb")
resource_group = client('resourcegroupstaggingapi')


def fix_rds_status_in_dynamo_table(status_table_name):
    account_id = sts_client.get_caller_identity()['Account']
    region = os.getenv('AWS_REGION', 'eu-west-1')

    if not status_table_name:
        raise Exception("Missing value for environment variable: STATUS_TABLE_NAME")

    logger.info(f"Start check status of RDS for align status table {status_table_name}")
    status_table = dynamodb_resource.Table(status_table_name)

    clusters = resource_group.get_resources(ResourceTypeFilters=["rds"])['ResourceTagMappingList']

    logger.info(f"Found {len(clusters)} RDS resources")
    key = {'service': 'rds', 'account-region': f"{account_id}:{region}"}

    current_status_in_table = status_table.get_item(Key=key).get('Item')
    if not current_status_in_table:
        logger.info("No RDS managed by scheduler, skip execution")
        exit
    for cluster in clusters:
        try:
            resource_arn = cluster["ResourceARN"]
            resource_arn_arr = resource_arn.split(":")
            resource_name = resource_arn_arr[-1]
            resource_type = resource_arn_arr[-2]

            if resource_type == "cluster":
                status = rds_client.describe_db_clusters(DBClusterIdentifier=resource_arn)["DBClusters"][0]['Status']
            elif resource_type == "db":
                rds_instance_info = rds_client.describe_db_instances(DBInstanceIdentifier=resource_arn)["DBInstances"][0]
                db_cluster_identifier = rds_instance_info.get('DBClusterIdentifier', None)
                if db_cluster_identifier:
                    # Instance is in cluster and scheduler work on it
                    logger.debug(f"DB instance {resource_name} is in cluster {db_cluster_identifier}")
                    continue
                else:
                    status = rds_instance_info['DBInstanceStatus']
            else:
                logger.debug(f"Invalid type for {resource_name}: {resource_type}")
                continue
            status_in_status_table = current_status_in_table.get(resource_name, None)
            logger.info(f"[{resource_name}]Resource status is: {status}")
            logger.info(f"[{resource_name}]Status in table is: {status_in_status_table}")
            if status.lower() == "available" and status_in_status_table != "running":
                logger.info(f"Restore correct status {resource_name} in status tables")
                # Andrebbe aggiunta la partion key nel caso di deploy multi account e regione
                r = status_table.update_item(Key=key,
                                             AttributeUpdates={resource_name: {'Value': 'running', 'Action': 'PUT'}})
                logger.debug(r)
        except rds_client.exceptions.DBClusterNotFoundFault:
            logger.debug(f"Cluster {resource_name} not found")
        except Exception as e:
            logger.error(e)
            pass


if __name__ == "__main__":
    fix_rds_status_in_dynamo_table("nhp-prod-scheduler-stack-StateTable-315AVHTA22NQ")
