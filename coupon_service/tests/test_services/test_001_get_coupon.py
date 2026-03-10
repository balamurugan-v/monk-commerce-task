from coupon_service.services.coupon_service import CouponService
from coupon_service.utils.constants import CouponStatus, CouponFields, MetadataKeys, MongoOperators
from coupon_service.utils.errors import CouponNotFound, CouponInactive
from coupon_service.tests.test_services import TestBase


class TestGetCoupon(TestBase):
    def setUp(self):
        self.coupon_service = CouponService(database=self.db)

    # --- 1. Filtering Logic ---
    def test_get_all_active_coupons_positive_check_filtering(self):
        """Positive: Ensure only ACTIVE coupons are returned in the global list."""
        # Initial 5 active in mock data
        initial = self.coupon_service.get_all_active_coupons()
        self.assertEqual(len(initial), 5)

        # Deactivate one directly in DB
        self.coupons_collection.update_one(
            {CouponFields.COUPON_CODE: "CART10OFF"},
            {MongoOperators.SET: {CouponFields.STATUS: CouponStatus.INACTIVE}}
        )

        # Should only return 4 now
        current = self.coupon_service.get_all_active_coupons()
        self.assertEqual(len(current), 4)
        for cp in current:
            self.assertEqual(cp.status, CouponStatus.ACTIVE)

    # --- 2. Specific Retrieval & Error States ---
    def test_get_coupon_by_code_positive(self):
        """Positive: Retrieve existing active coupon."""
        coupon = self.coupon_service.get_coupon_by_code("CART100OFF10")
        self.assertEqual(coupon.coupon_code, "CART100OFF10")
        self.assertEqual(coupon.status, CouponStatus.ACTIVE)

    def test_get_coupon_by_code_negative_inactive_error(self):
        """Negative: Fetching an INACTIVE coupon by code raises CouponInactive."""
        code = "PROD5OFF"
        self.coupons_collection.update_one(
            {CouponFields.COUPON_CODE: code},
            {MongoOperators.SET: {CouponFields.STATUS: CouponStatus.INACTIVE}}
        )

        with self.assertRaises(CouponInactive) as cm:
            self.coupon_service.get_coupon_by_code(code)
        self.assertIn("currently inactive", str(cm.exception))

    def test_get_coupon_by_code_negative_not_found(self):
        """Negative: Non-existent code raises CouponNotFound."""
        with self.assertRaises(CouponNotFound):
            self.coupon_service.get_coupon_by_code("MISSING_CODE_999")
