

from coupon_service.services.coupon_service import CouponService

from coupon_service.utils.constants import CouponStatus, CouponFields, CartKeys, ResponseKeys, MongoOperators
from coupon_service.utils.errors import CouponInactive
from tests.test_services import TestBase


class TestApplyCoupon(TestBase):
    def setUp(self):
        self.coupon_service = CouponService(database=self.db)

    # --- 1. Item-Level Breakdown Logic ---
    def test_apply_cart_wise_breakdown_proportional(self):
        """Positive: Verify proportional item-level breakdown for cart-wise."""
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "A", CartKeys.QUANTITY: 1, CartKeys.PRICE: 80.0},
                {CartKeys.PRODUCT_ID: "B", CartKeys.QUANTITY: 1, CartKeys.PRICE: 20.0}
            ]
        }
        # CART100OFF10 -> 10% of 100 = 10.0 discount
        res = self.coupon_service.apply_coupon_to_cart("CART100OFF10", cart)
        items = res[ResponseKeys.UPDATED_CART][CartKeys.ITEMS]
        
        # A(80% value) gets 8.0, B(20% value) gets 2.0
        self.assertEqual(items[0][CartKeys.TOTAL_DISCOUNT], 8.0)

        self.assertEqual(items[1][CartKeys.TOTAL_DISCOUNT], 2.0)

    # --- 2. Advanced BxGy Logic ---
    def test_apply_bxgy_cheapest_item_logic(self):
        """Positive: BxGy must discount the cheapest units of the 'Get' items."""
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "prod_B", CartKeys.QUANTITY: 1, CartKeys.PRICE: 100.0},
                {CartKeys.PRODUCT_ID: "prod_C", CartKeys.QUANTITY: 1, CartKeys.PRICE: 50.0},
                {CartKeys.PRODUCT_ID: "prod_C", CartKeys.QUANTITY: 1, CartKeys.PRICE: 10.0} # Cheapest unit
            ]
        }
        # BUYBGETC: Buy 1 B, Get 1 C. Total discount should be the price of the cheapest unit (10.0).
        res = self.coupon_service.apply_coupon_to_cart("BUYBGETC", cart)
        self.assertEqual(res[ResponseKeys.UPDATED_CART][CartKeys.TOTAL_DISCOUNT], 10.0)

    def test_apply_bxgy_repetition_limit_and_pool(self):
        """Positive: Test pool summation and repetition limit."""
        # BUYBGETC: Buy 1 B, Get 1 C. Limit 2.
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "prod_B", CartKeys.QUANTITY: 10, CartKeys.PRICE: 50.0}, # triggers 10 times
                {CartKeys.PRODUCT_ID: "prod_C", CartKeys.QUANTITY: 10, CartKeys.PRICE: 5.0}
            ]
        }
        res = self.coupon_service.apply_coupon_to_cart("BUYBGETC", cart)
        # Limit is 2. So only 2 units of C become free. Total discount = 10.0.
        self.assertEqual(res[ResponseKeys.UPDATED_CART][CartKeys.TOTAL_DISCOUNT], 10.0)

    # --- 3. Error States ---
    def test_apply_negative_inactive_error(self):
        """Negative: Raise CouponInactive when attempting to apply a disabled coupon."""
        code = "CART10OFF"
        self.coupons_collection.update_one(
            {CouponFields.COUPON_CODE: code}, 
            {MongoOperators.SET: {CouponFields.STATUS: CouponStatus.INACTIVE}}
        )
        with self.assertRaises(CouponInactive):
            self.coupon_service.apply_coupon_to_cart(code, {"items": []})

    def test_apply_negative_conditions_not_met(self):
        """Negative: Raise ValueError if coupon logic (e.g. threshold) is not met."""
        cart = {CartKeys.ITEMS: [{CartKeys.PRODUCT_ID: "A", CartKeys.QUANTITY: 1, CartKeys.PRICE: 10.0}]}
        with self.assertRaises(ValueError):
            self.coupon_service.apply_coupon_to_cart("CART100OFF10", cart)
