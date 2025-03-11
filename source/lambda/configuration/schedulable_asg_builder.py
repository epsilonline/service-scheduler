import boto3
from utils.logger import get_logger

from configuration.asg_handler import AsgHandler

from utils.logger import get_logger

class SchedulableAsgBuilder:
    """
        Builds a list of schedulable Autoscaling Groups
    """

    def __init__(self, tag_name: str):
        self._asg_client = boto3.client('autoscaling')
        self._tag_name = tag_name
        self._schedulable_asgs = self._build_schedulable_asg_list()

    def _build_schedulable_asg_list(self):

        """
            Identifies the ASGs which have a schedule tag, and so are meant to be scheduled
        """

        schedulable_asgs = []

        asgIterator = self._asg_client.get_paginator('describe_auto_scaling_groups').paginate(
            Filters=[
                {
                    'Name': 'tag-key',
                    'Values': [
                        self._tag_name
                    ]
                }
            ]
        )

        for page in asgIterator:
            for asg in page['AutoScalingGroups']:
                schedulable_asgs.append(AsgHandler(self._tag_name, asg))

        return schedulable_asgs

    @property
    def schedulable_asgs(self):
        return self._schedulable_asgs
