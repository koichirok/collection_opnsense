#!/usr/bin/python3

# Copyright: (C) 2022, AnsibleGuy <guy@ansibleguy.net>
# GNU General Public License v3.0+ (see https://www.gnu.org/licenses/gpl-3.0.txt)

# see: https://docs.opnsense.org/development/api/plugins/firewall.html

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.ansibleguy.opnsense.plugins.module_utils.helper import diff_remove_empty
from ansible_collections.ansibleguy.opnsense.plugins.module_utils.defaults import OPN_MOD_ARGS
from ansible_collections.ansibleguy.opnsense.plugins.module_utils.rule_defaults import \
    RULE_MOD_ARGS, RULE_DEFAULTS, RULE_MATCH_FIELDS_ARG
from ansible_collections.ansibleguy.opnsense.plugins.module_utils.api import Session
from ansible_collections.ansibleguy.opnsense.plugins.module_utils.rule_obj import Rule
from ansible_collections.ansibleguy.opnsense.plugins.module_utils.rule_main import process_rule
from ansible_collections.ansibleguy.opnsense.plugins.module_utils.multi_helper import validate_single


DOCUMENTATION = 'https://github.com/ansibleguy/collection_opnsense/blob/stable/docs/use_rule.md'
EXAMPLES = 'https://github.com/ansibleguy/collection_opnsense/blob/stable/docs/use_rule.md'


def run_module():
    module_args = dict(
        rules=dict(type='dict', required=True),
        key_field=dict(
            type='str', required=True, choises=['sequence', 'description'],
            description='What field is used as key of the provided dictionary'
        ),
        fail_verification=dict(
            type='bool', required=False, default=True,
            description='Fail module if single rule fails the verification.'
        ),
        state=dict(type='str', default='unset', required=False, choices=['present', 'absent', 'unset']),
        enabled=dict(type='bool', required=False, default=None),
        **RULE_MATCH_FIELDS_ARG,
        **OPN_MOD_ARGS,
    )

    result = dict(
        changed=False,
        diff={
            'before': {},
            'after': {},
        },
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    session = Session(module=module)
    existing_rules = Rule(module=module, session=session, result={}).search_call()

    if isinstance(module.params['key_field'], list):
        # edge case
        module.params['key_field'] = module.params['key_field'][0]

    overrides = {'match_fields': module.params['match_fields']}

    if module.params['state'] != 'unset':
        overrides['state'] = module.params['state']

    if module.params['enabled'] is not None:
        overrides['enabled'] = module.params['enabled']

    # build list of valid rules or fail if invalid config is not permitted
    valid_rules = {}
    for rule_key, rule_config in module.params['rules'].items():
        # build config and validate it the same way the module initialization would do

        if rule_config is None:
            rule_config = {}

        real_cnf = {
            **RULE_DEFAULTS,
            **rule_config,
            **{
                module.params['key_field']: rule_key,
                'firewall': module.params['firewall'],
            },
            **overrides,
        }
        if validate_single(
                module=module, module_args=RULE_MOD_ARGS, log_mod='rule',
                key=rule_key, cnf=real_cnf,
        ):
            valid_rules[rule_key] = real_cnf

    # manage rules
    for rule_key, rule_config in valid_rules.items():
        # process single rule like in the 'rule' module
        rule_result = dict(
            changed=False,
            diff={
                'before': {},
                'after': {},
            }
        )
        module.params['debug'] = rule_config['debug']  # per rule switch
        rule = Rule(
            module=module,
            result=rule_result,
            cnf=rule_config,
            session=session,
            fail=module.params['fail_verification'],
        )
        # save on requests
        rule.existing_rules = existing_rules

        rule.check()
        process_rule(rule=rule)

        if rule_result['changed']:
            result['changed'] = True
            rule_result['diff'] = diff_remove_empty(rule_result['diff'])

            if 'before' in rule_result['diff']:
                result['diff']['before'][rule_key] = rule_result['diff']['before']

            if 'after' in rule_result['diff']:
                result['diff']['after'][rule_key] = rule_result['diff']['after']

    # todo: add purging option => or create additional module for it

    session.close()
    result['diff'] = diff_remove_empty(result['diff'])
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()