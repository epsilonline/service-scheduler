import boto3
from utils.logger import get_logger

from boto3.dynamodb.conditions import Key

from configuration import logging_level

logger = get_logger('ConfigDynamodbAdapter')
logger.setLevel(logging_level)


class ConfigDynamodbAdapter:
    """
    Adapter to load scheduler configuration from a DynamoDB storage type.
    """
    def __init__(self, tablename):
        self._tablename = tablename
        self._config = self._get_config()

    @property
    def config(self):
        """
        Returns and cached the configuration data
        :return:
        """
        if self._config is None:
            self._config = self._get_config()
        return self._config

    def _get_config(self):

        dynamodb = boto3.resource("dynamodb")
        dynamodb_table = dynamodb.Table(self._tablename)

        logger.debug(f'config table is {self._tablename}')

        resp = dynamodb_table.get_item(Key={"name": "scheduler", "type": "config"}, ConsistentRead=True)
        config = resp.get("Item", {})
        resp = dynamodb_table.query(KeyConditionExpression=Key("type").eq('period'))
        config['periods'] = resp.get("Items")
        resp = dynamodb_table.query(KeyConditionExpression=Key("type").eq('schedule'))
        config['schedules'] = resp.get("Items")

        return config

    def get_config_by_name(self, name):
        periods = self._config['periods']
        return next(filter(lambda period: period['name'] == name, periods), None)

    def get_schedule_by_name(self, name):
        schedules = self._config['schedules']
        return next(filter(lambda schedule: schedule['name'] == name, schedules), None)
