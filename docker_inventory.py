#!/usr/bin/env python
"""An Ansible dynamic inventory script for docker containers. This script
assumes you already have docker running on your system.

Assumes hostname pattern is: dev_<SVC>_<PRE>_<ID>

Python packages required:
- ansible>=2.1
- docker>=2.2.1

Run:
./docker_inventory.py --list
./docker_inventory.py --host my_host

Sample output:
{
    "all": {
        "hosts": ["1234"]
    },
     "_meta": {
        "hostvars": {
            "1234": {"ansible_connection": "docker"}
        }
    }
}
"""

from argparse import ArgumentParser
from copy import deepcopy
from json import dumps

import re
import docker

class DockerInventory(object):
    """Docker inventory class.

    This class will generate the data structure needed by ansible inventory
    host for either all containers on your system or the one you declare. The
    data structure generated is in JSON format.
    """

    _data_structure = {'all': {'children': ['ungrouped']}, 'ungrouped': {'hosts': []}, '_meta': {'hostvars': {}}}

    def __init__(self, option):
        """Constructor.

        When the docker inventory class is instanticated, it performs the
        following tasks:
            * Instantiate the docker client class to create a docker object.
            * Generate the JSON data structure.
            * Print the JSON data structure for ansible to use.
        """
        self.client = docker.from_env()

        if option.list:
            data = self.containers()
        elif option.host:
            data = self.containers_by_host(option.host)
        else:
            data = self._data_structure
        print(dumps(data))

    def get_containers(self):
        """Return all docker containers on the system.

        :return: Collection of containers.
        """
        return self.client.containers.list(all=False)

    def add_host(self, container):
        """Returns formatted JSON structure for a container

        :return: Ansible JSON structure.
        """
        try:
            m = re.search('^dev_([A-Za-z0-9]+)_([A-Za-z0-9]+)_?([0-9]?)$', container.name)
            container.name in m.group(0)
        except AttributeError as e:
            self.resdata['ungrouped']['hosts'].append(container.name)
        else:
            self.resdata.setdefault(m.group(1), {'children': []})
            self.resdata.setdefault(m.group(2), {'hosts': []})
            if m.group(1) not in self.resdata['all']['children']: self.resdata['all']['children'].append(m.group(1))
            if m.group(2) not in self.resdata[m.group(1)]['children']: self.resdata[m.group(1)]['children'].append(m.group(2))
            if 'Networks' in container.attrs['NetworkSettings']:
                _net = container.attrs['NetworkSettings']['Networks'].keys()[0]
                _ip = container.attrs['NetworkSettings']['Networks'][_net]['IPAddress']
                if m.group(3).isdigit():
                    _name = m.group(2) + '-' + m.group(3)
                else:
                    _name = m.group(2)
                self.resdata[m.group(2)]['hosts'].append(_name)
                self.resdata['_meta']['hostvars'][_name] = \
                    {
                        'ansible_fqdn': _name + '.local',
                        'ansible_host': _ip,
                        'ansible_hostname': _name
                    }
            else: self.resdata['_meta']['hostvars'][container.name] = {'ansible_connection': 'docker','ansible_hostname': container.name}

    def containers(self):
        """Return all docker containers to be used by ansible inventory host.

        :return: Ansible required JSON data structure with containers.
        """
        self.resdata = deepcopy(self._data_structure)
        for container in self.get_containers():
            self.add_host(container)
        return self.resdata

    def containers_by_host(self, host=None):
        """Return the docker container requested to be used by ansible
        inventory host.

        :param host: Host name to search for.
        :return: Ansible required JSON data structure with containers.
        """
        self.resdata = deepcopy(self._data_structure)
        for container in self.get_containers():
            if str(container.name) == host:
                self.add_host(container)
                break
        return self.resdata


if __name__ == "__main__":
    dynamic_parser = ArgumentParser()
    dynamic_parser.add_argument('--list', action='store_true')
    dynamic_parser.add_argument('--host')

    DockerInventory(dynamic_parser.parse_args())
