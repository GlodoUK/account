from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"
    quarter = fields.Char(
        compute="_compute_quarter", store=True, string="Fiscal Quarter"
    )
    fiscal_year = fields.Integer(
        compute="_compute_quarter", store=True, string="Fiscal Year (Start Year)"
    )

    @api.depends("invoice_date")
    def _compute_quarter(self):
        for record in self:
            if record.invoice_date:
                # Get the  fiscalyear_last_month
                fiscalyear_last_month = record.company_id.fiscalyear_last_month
                fiscalyear_last_day = record.company_id.fiscalyear_last_day

                invoice_date_year = record.invoice_date.year
                if record.invoice_date.month > int(fiscalyear_last_month):
                    invoice_date_year = invoice_date_year + 1

                invoice_date = record.invoice_date

                # Create a date from the fiscalyear_last_day
                # and fiscalyear_last_month abd today_year
                end_date = invoice_date.replace(
                    month=int(fiscalyear_last_month),
                    day=fiscalyear_last_day,
                    year=invoice_date_year,
                )
                # subtract one year from date
                start_date = end_date + relativedelta(years=-1, days=1)

                q1 = [start_date + relativedelta(months=+i) for i in range(3)]
                q2 = [start_date + relativedelta(months=+i) for i in range(3, 6)]
                q3 = [start_date + relativedelta(months=+i) for i in range(6, 9)]
                q4 = [start_date + relativedelta(months=+i) for i in range(9, 12)]

                # Check if date_order falls within the start and end date and set label
                if start_date <= invoice_date <= end_date:
                    if start_date.year == end_date.year:
                        quarter_year = "{}".format(end_date.year)
                    else:
                        quarter_year = "{}/{}".format(start_date.year, end_date.year)
                else:
                    if start_date.year == end_date.year:
                        quarter_year = "{}".format(end_date.year)
                    else:
                        quarter_year = "{}/{}".format(end_date.year, end_date.year + 1)

                # Check the month when the date_order falls

                if record.invoice_date.month in [i.month for i in q1]:
                    record.quarter = "{} Q1".format(quarter_year)
                elif record.invoice_date.month in [i.month for i in q2]:
                    record.quarter = "{} Q2".format(quarter_year)
                elif record.invoice_date.month in [i.month for i in q3]:
                    record.quarter = "{} Q3".format(quarter_year)
                elif record.invoice_date.month in [i.month for i in q4]:
                    record.quarter = "{} Q4".format(quarter_year)
                else:
                    record.quarter = False
                record.fiscal_year = start_date.year
            else:
                record.quarter = False
                record.fiscal_year = False
