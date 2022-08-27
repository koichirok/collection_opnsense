#!/bin/bash

set -e

echo ''

DEBUG=false

if [ -z "$1" ] || [ -z "$2" ]
then
  echo 'Arguments:'
  echo '  1: firewall'
  echo '  2: api key file'
  echo '  3: path to virtual environment (optional)'
  echo ''
  exit 1
else
  export TEST_FIREWALL="$1"
  export TEST_API_KEY="$2"
fi

if [ -n "$3" ]
then
  source "$3/bin/activate"
fi

if [[ "$DEBUG" == true ]]
then
  VERBOSITY='-D -vvv'
else
  VERBOSITY=''
fi

cd "$(dirname "$0")/.."
rm -rf "~/.ansible/collections/ansible_collections/ansibleguy/opnsense"
ansible-galaxy collection install git+https://github.com/ansibleguy/collection_opnsense.git

echo ''
echo 'RUNNING TESTS for module ALIAS'
echo ''

ansible-playbook tests/alias.yml --extra-vars="ansible_python_interpreter=$(which python)" $VERBOSITY
ansible-playbook tests/alias.yml --check --extra-vars="ansible_python_interpreter=$(which python)" $VERBOSITY

echo ''
echo 'RUNNING TESTS for module MULTI_ALIAS'
echo ''

ansible-playbook tests/multi_alias.yml --extra-vars="ansible_python_interpreter=$(which python)" $VERBOSITY
ansible-playbook tests/multi_alias.yml --check --extra-vars="ansible_python_interpreter=$(which python)" $VERBOSITY


echo ''
echo 'FINISHED TESTS!'
echo ''
