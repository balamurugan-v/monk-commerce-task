from coupon_service.services.coupon_service import CouponService
from coupon_service.utils.constants import (
    CouponStatus, 
    CouponFields, 
    MetadataKeys, 
    MongoOperators, 
    CouponType
)
from coupon_service.utils.errors import CouponNotFound, CouponInactive
from coupon_service.tests.test_services import TestBase


class TestUpdateCoupon(TestBase):
    def setUp(self):
        self.coupon_service = CouponService(database=self.db)

    # ============================================================================
    # 1. STATUS TRANSITION TESTS
    # ============================================================================

    def test_update_status_active_to_inactive(self):
        """Positive: Transition ACTIVE -> INACTIVE via service."""
        code = "CART10OFF"
        # Update
        self.coupon_service.update_coupon(code, {CouponFields.STATUS: CouponStatus.INACTIVE})
        # Verify via DB
        raw = self.coupons_collection.find_one({CouponFields.COUPON_CODE: code})
        self.assertEqual(raw[CouponFields.STATUS], CouponStatus.INACTIVE)

    def test_update_status_inactive_to_active(self):
        """Positive: Transition INACTIVE -> ACTIVE (Reactivation)."""
        code = "CART100OFF10"
        # Setup: Deactivate in DB
        self.coupons_collection.update_one(
            {CouponFields.COUPON_CODE: code}, 
            {MongoOperators.SET: {CouponFields.STATUS: CouponStatus.INACTIVE}}
        )
        # Update via service
        updated = self.coupon_service.update_coupon(code, {CouponFields.STATUS: CouponStatus.ACTIVE})
        self.assertEqual(updated.status, CouponStatus.ACTIVE)
        # Verify retrievable
        res = self.coupon_service.get_coupon_by_code(code)
        self.assertEqual(res.status, CouponStatus.ACTIVE)

    # ============================================================================
    # 2. METADATA UPDATE TESTS (Exhaustive for all types)
    # ============================================================================

    def test_update_metadata_cart_wise(self):
        """Positive: Update Cart-wise metadata fields."""
        code = "CART10OFF"
        new_meta = {
            MetadataKeys.MIN_CART_TOTAL: 888.0,
            MetadataKeys.DISCOUNT_PERCENTAGE: 40
        }
        self.coupon_service.update_coupon(code, {CouponFields.METADATA: new_meta})
        updated = self.coupon_service.get_coupon_by_code(code)
        self.assertEqual(updated.metadata[MetadataKeys.MIN_CART_TOTAL], 888.0)
        self.assertEqual(updated.metadata[MetadataKeys.DISCOUNT_PERCENTAGE], 40)

    def test_update_metadata_product_wise(self):
        """Positive: Update Product-wise metadata fields."""
        code = "PROD5OFF"
        self.coupon_service.update_coupon(code, {CouponFields.STATUS: CouponStatus.ACTIVE})
        new_meta = {
            MetadataKeys.PRODUCT_ID: "NEW_PROD_ID",
            MetadataKeys.DISCOUNT_PERCENTAGE: 15
        }
        self.coupon_service.update_coupon(code, {CouponFields.METADATA: new_meta})
        updated = self.coupon_service.get_coupon_by_code(code)
        self.assertEqual(updated.metadata[MetadataKeys.PRODUCT_ID], "NEW_PROD_ID")
        self.assertEqual(updated.metadata[MetadataKeys.DISCOUNT_PERCENTAGE], 15)

    def test_update_metadata_bxgy(self):
        """Positive: Update BxGy pool and quantity fields."""
        code = "BUYBGETC"
        new_meta = {
            MetadataKeys.BUY_PRODUCTS: [{"product_id": "X"}, {"product_id": "Y"}],
            MetadataKeys.BUY_QUANTITY: 5,
            MetadataKeys.GET_PRODUCTS: [{"product_id": "Z"}],
            MetadataKeys.GET_QUANTITY: 2,
            MetadataKeys.REPETITION_LIMIT: 3
        }
        self.coupon_service.update_coupon(code, {CouponFields.METADATA: new_meta})
        updated = self.coupon_service.get_coupon_by_code(code)
        self.assertEqual(updated.metadata[MetadataKeys.BUY_QUANTITY], 5)
        self.assertEqual(len(updated.metadata[MetadataKeys.BUY_PRODUCTS]), 2)
        self.assertEqual(updated.metadata[MetadataKeys.REPETITION_LIMIT], 3)

    # ============================================================================
    # 3. TYPE SWITCHING TESTS
    # ============================================================================

    def test_update_switch_type_cart_to_product_wise(self):
        """Positive: Change coupon type from cart-wise to product-wise."""
        code = "CART10OFF"
        self.coupon_service.update_coupon(code, {CouponFields.STATUS: CouponStatus.ACTIVE})
        payload = {
            CouponFields.TYPE: CouponType.PRODUCT_WISE,
            CouponFields.METADATA: {
                MetadataKeys.PRODUCT_ID: "switched_prod",
                MetadataKeys.DISCOUNT_PERCENTAGE: 5
            }
        }
        self.coupon_service.update_coupon(code, payload)
        updated = self.coupon_service.get_coupon_by_code(code)
        self.assertEqual(updated.type, CouponType.PRODUCT_WISE)
        self.assertEqual(updated.metadata[MetadataKeys.PRODUCT_ID], "switched_prod")

    # ============================================================================
    # 4. NEGATIVE & GATEKEEPER TESTS
    # ============================================================================

    def test_update_gatekeeper_failure_on_inactive(self):
        """Negative: Gatekeeper must block metadata updates on inactive coupons."""
        code = "PROD5OFF"
        # Deactivate
        self.coupon_service.update_coupon(code, {CouponFields.STATUS: CouponStatus.INACTIVE})
        # Attempt update without activation
        with self.assertRaises(CouponInactive):
            self.coupon_service.update_coupon(code, {CouponFields.DESCRIPTION: "Fail"})

    def test_update_negative_not_found(self):
        """Negative: Update non-existent code raises CouponNotFound."""
        with self.assertRaises(CouponNotFound):
            self.coupon_service.update_coupon("DOES_NOT_EXIST", {CouponFields.DESCRIPTION: "fail"})
