from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    env["sale.order"].search([])._compute_quarter()
