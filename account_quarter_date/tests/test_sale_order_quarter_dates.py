from datetime import datetime

from odoo.tests import tagged

from .common import TestCommon


@tagged("post_install", "-at_install")
class TestSaleOrderQuarterDates(TestCommon):
    previous_year = datetime.now().year - 1

    def test_quarter_date_q1(self):
        self.company_id = self.env.ref("base.main_company")
        self.company_id.write(
            {
                "fiscalyear_last_month": "12",
                "fiscalyear_last_day": 31,
                "fiscalyear_lock_date": "2019-12-31",
            }
        )
        sale_order_id = self.model_sale_order.create(
            {
                "partner_id": self.partner_id.id,
                "partner_invoice_id": self.partner_id.id,
                "date_order": "2019-01-01",
                "partner_shipping_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product1.name,
                            "product_id": self.product1.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product1.uom_id.id,
                            "price_unit": 100,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )
        self.assertEqual(sale_order_id.quarter, "Q1 2019/2019")

    def test_quarter_date_q3(self):
        self.company_id = self.env.ref("base.main_company")
        # get current year
        self.company_id.write(
            {
                "fiscalyear_last_month": "4",
                "fiscalyear_last_day": 30,
                "fiscalyear_lock_date": "{}-04-30".format(self.previous_year),
            }
        )

        sale_order_id = self.model_sale_order.create(
            {
                "partner_id": self.partner_id.id,
                "partner_invoice_id": self.partner_id.id,
                "date_order": "{}-01-01".format(self.previous_year),
                "partner_shipping_id": self.partner_id.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": self.product1.name,
                            "product_id": self.product1.id,
                            "product_uom_qty": 1,
                            "product_uom": self.product1.uom_id.id,
                            "price_unit": 100,
                            "tax_id": False,
                        },
                    )
                ],
            }
        )
        self.assertEqual(
            sale_order_id.quarter,
            "Q3 {}{}{}".format(self.previous_year - 1, "/", self.previous_year),
        )
