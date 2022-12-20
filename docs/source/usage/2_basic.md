# 2 - Usage

## Prerequisites

You need to create API credentials as described in [the documentation](https://docs.opnsense.org/development/how-tos/api.html#creating-keys).

**Menu**: System - Access - Users - Edit {admin user} - Add api key

### SSL Certificate

If you use your firewall for non-testing purposes - you should **ALWAYS USE SSL VERIFICATION** for your connections!

```yaml
ssl_verify: true
```

To make a connection trusted you need either:

- a valid public certificate for the DNS-Name your firewall has (_LetsEncrypt/ACME_)
- an internal certificate authority that is used to create signed certificates
  - you could create such internal certificates using OPNSense. See [documentation](https://docs.opnsense.org/manual/how-tos/self-signed-chain.html).
  - if you do so - it is important that the IP-address and/or DNS-Name of your firewall is included in the 'Subject Alternative Name' (_SAN_) for it to be valid

After you got a valid certificate - you need to import and activate it:
- Import: 'System - Trust - Certificates - Import'
- Make sure your DNS-Names are allowed: 'System - Settings - Administration - Alternate Hostnames'
- Activate: 'System - Settings - Administration - SSL Certificate'

If you are using an internal CA for your certificates - you have to provide its public key to the modules:

```yaml
ssl_ca_file: '/path/to/ca.pem'
```

----

## Basics

### Defaults

If some parameters will be the same every time - use 'module_defaults':

```yaml
- hosts: localhost
  gather_facts: no
  module_defaults:
    ansibleguy.opnsense.alias:
        firewall: 'opnsense.template.ansibleguy.net'
        api_credential_file: '/home/guy/.secret/opn.key'
        # if you use an internal certificate:
        #   ssl_ca_file: '/etc/ssl/certs/custom/ca.crt'
        # else you COULD (but SHOULD NOT) use:
        #   ssl_verify: false

  tasks:
    - name: Example
      ansibleguy.opnsense.alias:
        name: 'ANSIBLE_TEST1'
        content: ['1.1.1.1']
```

### Inventory

If you are running the modules over hosts in your inventory - you would do it like that:

```yaml
- hosts: firewalls
  connection: local  # execute modules on controller
  gather_facts: no
  tasks:
    - name: Example
      ansibleguy.opnsense.alias:
        firewall: "{{ ansible_host }}"  # or use a per-host variable to store the FQDN..
```

### Vault

You may want to use '**ansible-vault**' to **encrypt** your 'api_credential_file' or 'api_secret'

```bash
ansible-vault encrypt /path/to/credential/file
# or
ansible-vault encrypt_string 'api_secret'

# run playbook:
ansible-playbook -D opnsense.yml --ask-vault-pass
```

### Running

These modules support check-mode and can show you the difference between existing and configured items:

```bash
# show difference
ansible-playbook opnsense.yml -D

# run in check-mode (no changes are made)
ansible-playbook opnsense.yml --check
```