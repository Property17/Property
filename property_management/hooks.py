# -*- coding: utf-8 -*-
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# Same domain as security/rules_property_management.xml (analytic.analytic_comp_rule override).
ANALYTIC_COMP_RULE_DOMAIN = (
    "['|', '|', ('company_id', '=', False), "
    "('company_id', 'in', user.company_ids.ids), "
    "('company_id', 'parent_of', company_ids)]"
)


def fix_analytic_multi_company_rule(env):
    """Force analytic multi-company rule to be group-based (not global) and use a sane domain.

    The stock rule is noupdate=1 and global; XML overrides from other modules are often not
    written to the database, so record-rule evaluation stays AND(global, OR(groups)) and
    admin bypass rules never win. This hook/migration applies the override in SQL/API reliably.
    """
    try:
        rule = env.ref('analytic.analytic_comp_rule')
    except ValueError:
        _logger.warning('property_management: analytic.analytic_comp_rule xmlid missing, skip patch')
        return
    group_multi = env.ref('base.group_multi_company', raise_if_not_found=False)
    if not group_multi:
        return
    rule_sudo = rule.sudo()
    rule_sudo.write({
        'groups': [(6, 0, group_multi.ids)],
        'domain_force': ANALYTIC_COMP_RULE_DOMAIN,
    })
    env.registry.clear_cache()
    _logger.info(
        'property_management: patched ir.rule %s (Analytic multi company): non-global + domain',
        rule_sudo.id,
    )


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    fix_analytic_multi_company_rule(env)
