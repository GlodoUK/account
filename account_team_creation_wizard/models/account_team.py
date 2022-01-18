from odoo import fields, models


class AccountTeam(models.TransientModel):
    _name = "account.team.wizard"
    _description = "Accounting Team Creation Wizard"

    name = fields.Char(required=True)
    journal_ids = fields.Many2many(
        "account.journal", required=True, string="Journals to Allow Access to"
    )
    user_ids = fields.Many2many("res.users", string="Apply to Users")
    extra_menu_ids = fields.Many2many("ir.ui.menu", string="Extra Menus")
    comment = fields.Text(string="Note")

    def _get_account_journal_domain_force(self):
        self.ensure_one()

        return [
            ("id", "in", self.journal_ids.ids),
        ]

    def _get_account_move_domain_force(self):
        self.ensure_one()

        return [
            ("journal_id", "in", self.journal_ids.ids),
        ]

    def _get_group_vals(self):
        self.ensure_one()

        copy_from_id = self.env.ref("account.group_account_invoice")

        menu_ids = copy_from_id.mapped("menu_access")
        menu_ids |= self.extra_menu_ids

        access_rules = [
            (
                0,
                0,
                {
                    "name": "Accounting Team: {}".format(access_id.name),
                    "model_id": access_id.model_id.id,
                    "perm_read": access_id.perm_read,
                    "perm_write": access_id.perm_write,
                    "perm_create": access_id.perm_create,
                    "perm_unlink": access_id.perm_unlink,
                },
            )
            for access_id in copy_from_id.mapped("model_access")
        ]

        excluded_rule_models = [
            self.env.ref("account.model_account_journal").id,
            self.env.ref("account.model_account_move").id,
            self.env.ref("account.model_account_move_line").id,
        ]

        to_copy_rule_ids = copy_from_id.mapped("rule_groups").filtered(
            lambda r: r.model_id.id not in excluded_rule_models
        )

        rule_groups = [
            (
                0,
                0,
                {
                    "name": "Accounting Team: {}".format(rule_group_id.name),
                    "model_id": rule_group_id.model_id.id,
                    "domain_force": rule_group_id.domain_force,
                    "perm_read": rule_group_id.perm_read,
                    "perm_write": rule_group_id.perm_write,
                    "perm_create": rule_group_id.perm_create,
                    "perm_unlink": rule_group_id.perm_unlink,
                },
            )
            for rule_group_id in to_copy_rule_ids
        ]

        rule_groups += [
            (
                0,
                0,
                {
                    "name": "Accounting Team: {} Account Journal".format(self.name),
                    "domain_force": self._get_account_journal_domain_force(),
                    "model_id": self.env.ref("account.model_account_journal").id,
                    "perm_read": True,
                    "perm_write": False,
                    "perm_create": False,
                    "perm_unlink": False,
                },
            ),
            (
                0,
                0,
                {
                    "name": "Accounting Team: {} Account Moves".format(self.name),
                    "domain_force": self._get_account_move_domain_force(),
                    "model_id": self.env.ref("account.model_account_move").id,
                    "perm_read": True,
                    "perm_write": False,
                    "perm_create": False,
                    "perm_unlink": False,
                },
            ),
            (
                0,
                0,
                {
                    "name": "Accounting Team: {} Account Move Lines".format(self.name),
                    "domain_force": self._get_account_move_domain_force(),
                    "model_id": self.env.ref("account.model_account_move_line").id,
                    "perm_read": True,
                    "perm_write": False,
                    "perm_create": False,
                    "perm_unlink": False,
                },
            ),
        ]

        return {
            "name": "{} (Accounting Team)".format(self.name),
            "category_id": self.env.ref(
                "base.module_category_accounting_accounting"
            ).id,
            "model_access": access_rules,
            "menu_access": [(4, g.id, False) for g in menu_ids],
            "rule_groups": rule_groups,
        }

    def action_apply(self):
        self.ensure_one()

        group_id = self.env["res.groups"].create(self._get_group_vals())

        for user_id in self.user_ids:
            to_move = user_id.mapped("groups_id").filtered(
                lambda g: g.category_id == group_id.category_id
            )

            user_id.write(
                {
                    "groups_id": [(3, g.id, False) for g in to_move],
                }
            )

            user_id.write(
                {
                    "groups_id": [(4, group_id.id)],
                }
            )

        return {
            "type": "ir.actions.act_window_close",
        }
