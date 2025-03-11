import datetime
import os
from utils.logger import get_logger
from utils.fix_rds_cluster import fix_rds_status_in_dynamo_table

from configuration.config_dynamodb_adapter import ConfigDynamodbAdapter
from configuration.schedulable_ecs_clusters_builder import SchedulableEcsClustersBuilder
from configuration.schedulable_asg_builder import SchedulableAsgBuilder
from configuration.rds.schedulable_rds_cluster_builder import SchedulableRDSClustersBuilder
from configuration.documentdb.schedulable_documentdb_builder import SchedulableDocumentDBBuilder
from configuration.rds.rds_cluster_handler import RDSClusterHandler
from configuration.period import Period

from configuration import main_table_name

logger = get_logger('Main')
status_table_name = os.getenv("STATUS_TABLE_NAME")


def lambda_handler(event, context):
    event_time = datetime.datetime.fromisoformat(
        event['time'].replace('Z', '+00:00'))

    logger.debug(f'Event time is: {event_time}')

    scheduler_configuration = ConfigDynamodbAdapter(main_table_name)


    schedulable_resources = []
    ecsBuilder = SchedulableEcsClustersBuilder(scheduler_configuration.config['tagname'])
    schedulable_resources += ecsBuilder.schedulable_clusters

    asgBuilder = SchedulableAsgBuilder(scheduler_configuration.config['tagname'])
    schedulable_resources += asgBuilder.schedulable_asgs

    rdsClustersBuilder = SchedulableRDSClustersBuilder(scheduler_configuration.config['tagname'])
    schedulable_resources += rdsClustersBuilder.schedulable_rds_clusters

    documentdbBuilder = SchedulableDocumentDBBuilder(scheduler_configuration.config['tagname'])
    schedulable_resources += documentdbBuilder._schedulable_documentdb

    for schedulable_resource in schedulable_resources:

        schedule_conf_name = schedulable_resource.schedule_tag_value

        if schedule_conf_name is None:
            logger.info(f'Skip resource {schedulable_resource} for empty schedule tag')
            continue

        schedule_conf = scheduler_configuration.get_schedule_by_name(schedule_conf_name)

        if schedule_conf is None:
            logger.error(f'No schedule config with name {schedule_conf_name}')
            continue

        # if the applied schedule contains an override_status, don't evaluate
        # schedule periods
        if schedule_conf.get('override_status'):
            override_status = schedule_conf['override_status']
            logger.debug(f'schedule defines a {override_status} override_status')
            schedule_on_override(schedulable_resource, override_status)
        # else evaluate applied schedule periods
        else:
            schedule_periods = schedule_conf['periods']
            schedule_on_periods(schedulable_resource, event_time, scheduler_configuration, schedule_periods, schedule_conf)

    fix_rds_status_in_dynamo_table(status_table_name=status_table_name)


def schedule_on_override(schedulable_resource, override_status):

    if isinstance(schedulable_resource, RDSClusterHandler):
        logger.info(f"schedule on override status is not supported for RDS clusters")
        return

    if override_status == 'stopped':
        schedulable_resource.shutdown()
    elif override_status == 'running':
        schedulable_resource.start()


def schedule_on_periods(schedulable_resource, event_time, scheduler_configuration, schedule_periods, schedule_conf):
    # every schedule can have more periods
    for schedule_period_name in schedule_periods:

        schedule_period = scheduler_configuration.get_config_by_name(schedule_period_name)

        period = Period(name=schedule_period['name'],
                        begintime=schedule_period['begintime'],
                        endtime=schedule_period['endtime'],
                        weekdays=schedule_period['weekdays'])

        event_time_is_in_period = period.time_is_in_period(event_time, schedule_conf['timezone'])

        #Manage rds scheduling
        kwarags = {}
        if isinstance(schedulable_resource, RDSClusterHandler):
            if {'start_minCapacity', 'start_maxCapacity', 'stop_minCapacity', 'stop_maxCapacity'} <= \
                    schedule_period.keys():
                logger.debug(f"{schedule_period['name']} is a valid period for rds'")

                if event_time_is_in_period:
                    kwarags['min_capacity'] = float(schedule_period['start_minCapacity'])
                    kwarags['max_capacity'] = float(schedule_period['start_maxCapacity'])
                else:
                    kwarags['min_capacity'] = float(schedule_period['stop_minCapacity'])
                    kwarags['max_capacity'] = float(schedule_period['stop_maxCapacity'])
            else:
                logger.debug(f"{schedule_period['name']} isn't a valid period for rds, skip to next period'")
                continue

        logger.debug(f'event in period? {event_time_is_in_period}')

        if event_time_is_in_period is True:
            schedulable_resource.start(**kwarags)
        else:
            schedulable_resource.shutdown(**kwarags)

# Run lambda_handler locally without sam
if __name__ == "__main__":
    import json
    from pathlib import Path
    event_file = open(Path("../../events/cwevent.json"))
    event = json.loads(event_file.read())
    lambda_handler(event, None)
