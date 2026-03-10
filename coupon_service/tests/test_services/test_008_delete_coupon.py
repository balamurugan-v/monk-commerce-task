from coupon_service.services.coupon_service import CouponService
from coupon_service.utils.errors import CouponNotFound
from tests.test_services import TestBase


class TestDeleteCoupon(TestBase):
    def setUp(self):
        self.coupon_service = CouponService(database=self.db)

    def test_delete_coupon_positive(self):
        """Positive: Delete existing coupon."""
        code = "BUYBGETC"
        # First, ensure it exists
        coupon = self.coupon_service.get_coupon_by_code(code)
        self.assertIsNotNone(coupon)

        # Delete
        self.coupon_service.delete_coupon(code)

        # Verify it's gone
        with self.assertRaises(CouponNotFound):
            self.coupon_service.get_coupon_by_code(code)

    def test_delete_coupon_negative_not_found(self):
        """Negative: Deleting non-existent code raises CouponNotFound."""
        with self.assertRaises(CouponNotFound):
            self.coupon_service.delete_coupon("DOES_NOT_EXIST")
