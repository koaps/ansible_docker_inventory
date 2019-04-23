# Ansible Docker-compose Inventory

This script can be used for getting inventory from docker for docker-compose based containers

Docker-compose will create host names based on the directory name, this script assumes dev_XXXX is the directory name,
so the first instance of haproxy service would have a hostname like: dev_test_haproxy_1

It will generate custom hostnames like: haproxy-1

This script also looks for bridged networks, containers on those networks will use IP addresses instead of docker connection type,
so ssh is assumed to be running.

(See: `Systemd integration` for Centos https://hub.docker.com/_/centos/ as an example)
