# Copyright (C) 2015-2016 Regents of the University of California
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import absolute_import
import datetime
import os

from bd2k.util import parse_iso_utc, less_strict_bool


class BaseAWSProvisioner(object):
    @staticmethod
    def _remainingBillingInterval(instance):
        return 1.0 - BaseAWSProvisioner._partialBillingInterval(instance)

    @classmethod
    def _filterImpairedNodes(cls, nodes, ec2):
        # if TOIL_AWS_NODE_DEBUG is set don't terminate nodes with
        # failing status checks so they can be debugged
        nodeDebug = less_strict_bool(os.environ.get('TOIL_AWS_NODE_DEBUG'))
        if not nodeDebug:
            return nodes
        nodeIDs = [node.id for node in nodes]
        statuses = ec2.get_all_instance_status(instance_ids=nodeIDs)
        statusMap = {status.id: status.instance_status for status in statuses}
        return [node for node in nodes if statusMap.get(node.id, None) != 'impaired']

    @staticmethod
    def _partialBillingInterval(instance):
        """
        Returns a floating point value between 0 and 1.0 representing how far we are into the
        current billing cycle for the given instance. If the return value is .25, we are one
        quarter into the billing cycle, with three quarters remaining before we will be charged
        again for that instance.
        """
        launch_time = parse_iso_utc(instance.launch_time)
        now = datetime.datetime.utcnow()
        delta = now - launch_time
        return delta.total_seconds() / 3600.0 % 1.0
