# OPNSense - Service module

**STATE**: unstable

**TESTS**: [Playbook](https://github.com/ansibleguy/collection_opnsense/blob/stable/tests/service.yml)

## Info

This module can interact with a specified service running on the OPNSense system.

## Definition

| Parameter | Type    | Required | Default value | Aliases | Comment                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
|:----------|:--------|:---------|:--------------|:--------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| name      | string  | true     | -             | target  | Pretty name of the service to interact with. One of: 'acme_client', 'apcupsd', 'bind', 'captive_portal', 'chrony', 'cicap', 'clamav', 'collectd', 'cron', 'crowdsec', 'dns_crypt_proxy', 'dyndns', 'fetchmail', 'freeradius', 'frr', 'ftp_proxy', 'haproxy', 'hwprobe', 'ids', 'iperf', 'ipsec', 'lldpd', 'maltrail', 'mdns_repeater', 'monit', 'munin_node', 'netdata', 'netsnmp', 'nginx', 'node_exporter', 'nrpe', 'ntopng', 'nut', 'openconnect', 'postfix', 'proxy', 'proxysso', 'puppet_agent', 'qemu_guest_agent', 'radsec_proxy', 'redis', 'relayd', 'rspamd', 'shadowsocks', 'shaper', 'siproxd', 'softether', 'sslh', 'stunnel', 'syslog', 'tayga', 'telegraf', 'tftp', 'tinc', 'tor', 'udp_broadcast_relay', 'unbound', 'vnstat', 'wireguard', 'zabbix_agent', 'zabbix_proxy' |
| action    | string  | true     | -             | -       | What action to execute. Some services may not support all of these actions (_the module will inform you in that case_). One of: 'status', 'start', 'reload', 'restart', 'stop'                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

## Examples

```yaml
- hosts: localhost
  gather_facts: no
  module_defaults:
    ansibleguy.opnsense.service:
      firewall: 'opnsense.template.ansibleguy.net'
      api_credential_file: '/home/guy/.secret/opn.key'

  tasks:
    - name: Restarting IPSec service
      ansibleguy.opnsense.service:
        name: 'ipsec'
        action: 'restart'

    - name: Get status of FRR service
      ansibleguy.opnsense.service:
        name: 'frr'
        action: 'status'
      register: frr_svc

    - name: Printing FRR service status
      ansible.builtin.debug:
        var: frr_svc.data

    - name: Stopping Tor service
      ansibleguy.opnsense.service:
        name: 'tor'
        action: 'stop'
```