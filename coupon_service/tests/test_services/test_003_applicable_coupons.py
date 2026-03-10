from coupon_service.services.coupon_service import CouponService
from coupon_service.utils.constants import (
    CouponStatus,
    CartKeys,
    ResponseKeys, 
    CouponFields,
    MetadataKeys,
    CouponType
)
from coupon_service.tests.test_services import TestBase


class TestApplicableCoupons(TestBase):
    def setUp(self):
        self.coupon_service = CouponService(database=self.db)

    # ============================================================================
    # 1. POSITIVE SCENARIOS
    # ============================================================================

    def test_001_get_applicable_positive_full_mix(self):
        """Positive: Cart qualifies for a mix of all strategy types."""
        # Cart Total: 60 (A) + 40 (B) + 10 (C) = 110.0
        # 1. CART10OFF (Threshold 100) -> 11.0
        # 2. PRODA20OFF (20% of 60) -> 12.0
        # 3. BUYBGETC (B triggers, C free) -> 10.0
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "prod_A", CartKeys.QUANTITY: 1, CartKeys.PRICE: 60.0},
                {CartKeys.PRODUCT_ID: "prod_B", CartKeys.QUANTITY: 1, CartKeys.PRICE: 40.0},
                {CartKeys.PRODUCT_ID: "prod_C", CartKeys.QUANTITY: 1, CartKeys.PRICE: 10.0}
            ]
        }
        results = self.coupon_service.get_applicable_coupons(cart)
        results.sort(key=lambda x: x[CouponFields.COUPON_CODE])
        
        # We expect 4 (CART10OFF, CART100OFF10, PRODA20OFF, BUYBGETC)
        self.assertEqual(len(results), 4)
        
        # Precise index checks
        self.assertEqual(results[0][CouponFields.COUPON_CODE], "BUYBGETC")
        self.assertEqual(results[0][ResponseKeys.DISCOUNT], 10.0)
        
        self.assertEqual(results[2][CouponFields.COUPON_CODE], "CART10OFF")
        self.assertEqual(results[2][ResponseKeys.DISCOUNT], 11.0)

    def test_002_get_applicable_product_wise_multiple_qty(self):
        """Positive: Product-wise discount scales with quantity."""
        # PRODA20OFF (20% off). Have 10 units @ 10.0 = 100.0 total.
        cart = {CartKeys.ITEMS: [{CartKeys.PRODUCT_ID: "prod_A", CartKeys.QUANTITY: 10, CartKeys.PRICE: 10.0}]}
        results = self.coupon_service.get_applicable_coupons(cart)
        
        # Check specific discount value

        found = [r for r in results if r[CouponFields.COUPON_CODE] == "PRODA20OFF"][0]
        self.assertEqual(found[ResponseKeys.DISCOUNT], 20.0) # 20% of 100

    def test_003_get_applicable_bxgy_multiple_reps(self):
        """Positive: BxGy applicable discount reflects multiple repetitions."""
        # BUYBGETC: Buy 1 B, Get 1 C. Have 3 B and 3 C.
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "prod_B", CartKeys.QUANTITY: 3, CartKeys.PRICE: 50.0},
                {CartKeys.PRODUCT_ID: "prod_C", CartKeys.QUANTITY: 3, CartKeys.PRICE: 10.0}
            ]
        }
        results = self.coupon_service.get_applicable_coupons(cart)
        found = [r for r in results if r[CouponFields.COUPON_CODE] == "BUYBGETC"][0]
        # repetitions = 3. limit = 2. So discount 2*10.0 = 20.0
        self.assertEqual(found[ResponseKeys.DISCOUNT], 20.0)

    # ============================================================================
    # 2. NEGATIVE / EDGE SCENARIOS
    # ============================================================================

    def test_004_get_applicable_negative_empty_cart(self):
        """Negative: Empty cart returns no coupons."""
        results = self.coupon_service.get_applicable_coupons({CartKeys.ITEMS: []})
        self.assertEqual(len(results), 0)

    def test_005_get_applicable_negative_inactive_excluded(self):
        """Negative: Ensure inactive coupons are filtered out."""
        code = "PRODA20OFF"
        # Deactivate
        self.coupon_service.update_coupon(code, {CouponFields.STATUS: CouponStatus.INACTIVE})
        
        cart = {CartKeys.ITEMS: [{CartKeys.PRODUCT_ID: "prod_A", CartKeys.QUANTITY: 1, CartKeys.PRICE: 100.0}]}
        results = self.coupon_service.get_applicable_coupons(cart)
        
        codes = [r[CouponFields.COUPON_CODE] for r in results]
        self.assertNotIn(code, codes)

    def test_006_get_applicable_edge_bxgy_insufficient_trigger(self):
        """Edge: BxGy trigger quantity not met (need 1, have 0)."""
        cart = {CartKeys.ITEMS: [{CartKeys.PRODUCT_ID: "prod_C", CartKeys.QUANTITY: 5, CartKeys.PRICE: 10.0}]}
        results = self.coupon_service.get_applicable_coupons(cart)
        self.assertNotIn("BUYBGETC", [r[CouponFields.COUPON_CODE] for r in results])

    def test_007_get_applicable_edge_cart_wise_exact_boundary(self):
        """Edge: Total exactly equals threshold."""
        cart = {CartKeys.ITEMS: [{CartKeys.PRODUCT_ID: "X", CartKeys.QUANTITY: 1, CartKeys.PRICE: 100.0}]}
        results = self.coupon_service.get_applicable_coupons(cart)
        codes = [r[CouponFields.COUPON_CODE] for r in results]
        self.assertIn("CART10OFF", codes)

    def test_008_get_applicable_edge_repetition_limit_zero(self):
        """Edge: BxGy coupon with repetition_limit=0 should be skipped."""
        # Create a temporary coupon with limit 0
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: "LIMIT_ZERO",
            CouponFields.TYPE: CouponType.BXGY,
            CouponFields.DESCRIPTION: "d",
            CouponFields.METADATA: {
                MetadataKeys.BUY_PRODUCTS: [{"product_id": "prod_B"}],
                MetadataKeys.BUY_QUANTITY: 1,
                MetadataKeys.GET_PRODUCTS: [{"product_id": "prod_C"}],
                MetadataKeys.GET_QUANTITY: 1,
                MetadataKeys.REPETITION_LIMIT: 0
            }
        })
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "prod_B", CartKeys.QUANTITY: 1, CartKeys.PRICE: 10.0},
                {CartKeys.PRODUCT_ID: "prod_C", CartKeys.QUANTITY: 1, CartKeys.PRICE: 5.0}
            ]
        }
        results = self.coupon_service.get_applicable_coupons(cart)
        codes = [r[CouponFields.COUPON_CODE] for r in results]
        self.assertNotIn("LIMIT_ZERO", codes)
