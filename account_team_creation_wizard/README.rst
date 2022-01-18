============================
account_team_creation_wizard
============================

Assists in the creation of an accounting groups, where the group is restricted
to specific journals.

This is acheived by creating a new group, copying the original memberships and
menus from the default account invoice group, and then adding new access rules
and menu items from the menu.

It specifically does not inherit from the base accounting (billing) group as by
default users have access to ALL journal entries.

:warning: This means that any new groups added to the base accounting (billing)
group after the wizard creates this group will be copied. This is by design.

Usage
=====

#. Goto the menu *Accounting > Account Team Creation Wizard*
#. Fill in the wizard

