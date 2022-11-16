from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"
    quarter = fields.Char(compute="_compute_quarter", store=True)

    @api.depends("date_order")
    def _compute_quarter(self):

        for record in self:
            if record.date_order:
                # Get the  fiscalyear_last_month
                fiscalyear_last_month = record.company_id.fiscalyear_last_month
                fiscalyear_last_day = record.company_id.fiscalyear_last_day
                # get today yyear

                date_order_year = record.date_order.year

                date_order = record.date_order.date()

                # Create a date from the fiscalyear_last_day
                # and fiscalyear_last_month abd today_year
                end_date = date_order.replace(
                    month=int(fiscalyear_last_month),
                    day=fiscalyear_last_day,
                    year=date_order_year,
                )
                # subtract one year from date
                start_date = end_date + relativedelta(years=-1, days=1)

                q1 = [start_date + relativedelta(months=+i) for i in range(3)]
                q2 = [start_date + relativedelta(months=+i) for i in range(3, 6)]
                q3 = [start_date + relativedelta(months=+i) for i in range(6, 9)]
                q4 = [start_date + relativedelta(months=+i) for i in range(9, 12)]

                # Check if date_order is  falls within the start and end date
                if start_date <= date_order <= end_date:
                    quarter_year = "{}/{}".format(start_date.year, end_date.year)
                else:
                    quarter_year = "{}/{}".format(end_date.year, end_date.year + 1)

                # Check the month when the date_order falls

                if record.date_order.month in [i.month for i in q1]:
                    record.quarter = "{} Q1".format(quarter_year)
                elif record.date_order.month in [i.month for i in q2]:
                    record.quarter = "{} Q2".format(quarter_year)
                elif record.date_order.month in [i.month for i in q3]:
                    record.quarter = "{} Q3".format(quarter_year)
                elif record.date_order.month in [i.month for i in q4]:
                    record.quarter = "{} Q4".format(quarter_year)
                else:
                    record.quarter = False
            else:
                record.quarter = False
