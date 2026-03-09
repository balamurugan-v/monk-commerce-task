
from unittest.mock import patch
from coupon_service.services.coupon_service import CouponService

from coupon_service.utils.constants import CouponType, CouponStatus, MetadataKeys, CouponFields
from coupon_service.utils.errors import CouponAlreadyExists
from tests.test_services import TestBase


class TestCreateCoupon(TestBase):
    def setUp(self):
        self.mock_short_id_patch = patch("coupon_service.utils.id_generator.short_id", return_value="create_test_id")
        self.mock_short_id = self.mock_short_id_patch.start()
        self.coupon_service = CouponService(database=self.db)
        self.addCleanup(self.mock_short_id_patch.stop)

    # --- 1. Basic Creation & Defaults ---
    def test_create_coupon_default_status_active(self):
        """Positive: Status must be ACTIVE by default if not provided in payload."""
        data = {
            CouponFields.COUPON_CODE: "DEFAULT_ACTIVE_TEST",
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "Default status check",
            CouponFields.METADATA: {MetadataKeys.MIN_CART_TOTAL: 100, MetadataKeys.DISCOUNT_PERCENTAGE: 10}
        }
        coupon = self.coupon_service.create_coupon(data)
        self.assertEqual(coupon.status, CouponStatus.ACTIVE)

    # --- 2. Cart & Product Wise Combinations ---
    def test_create_cart_wise_positive(self):
        """Positive: Create standard Cart-wise coupon."""
        data = {
            CouponFields.COUPON_CODE: "CART_10_TEST",
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "10% off",
            CouponFields.METADATA: {MetadataKeys.MIN_CART_TOTAL: 200, MetadataKeys.DISCOUNT_PERCENTAGE: 10}
        }
        cp = self.coupon_service.create_coupon(data)
        self.assertEqual(cp.coupon_code, "CART_10_TEST")
        self.assertEqual(cp.metadata[MetadataKeys.MIN_CART_TOTAL], 200)

    def test_create_product_wise_positive(self):
        """Positive: Create standard Product-wise coupon."""
        data = {
            CouponFields.COUPON_CODE: "PROD_20_TEST",
            CouponFields.TYPE: CouponType.PRODUCT_WISE,
            CouponFields.DESCRIPTION: "20% off Prod X",
            CouponFields.METADATA: {MetadataKeys.PRODUCT_ID: "X", MetadataKeys.DISCOUNT_PERCENTAGE: 20}
        }
        cp = self.coupon_service.create_coupon(data)
        self.assertEqual(cp.metadata[MetadataKeys.PRODUCT_ID], "X")

    # --- 3. BxGy Exhaustive Combinations ---

    def test_create_bxgy_buy1_get1(self):
        """Positive: Standard Buy 1 Get 1."""
        data = {
            CouponFields.COUPON_CODE: "B1G1_CODE", CouponFields.TYPE: CouponType.BXGY,
            CouponFields.DESCRIPTION: "B1G1",
            CouponFields.METADATA: {
                MetadataKeys.BUY_PRODUCTS: [{"product_id": "A"}], MetadataKeys.BUY_QUANTITY: 1,
                MetadataKeys.GET_PRODUCTS: [{"product_id": "B"}], MetadataKeys.GET_QUANTITY: 1
            }
        }
        cp = self.coupon_service.create_coupon(data)
        self.assertEqual(cp.metadata[MetadataKeys.BUY_QUANTITY], 1)
        self.assertEqual(cp.metadata[MetadataKeys.GET_QUANTITY], 1)

    def test_create_bxgy_buy3_get1(self):
        """Positive: Buy Multiple (3) Get 1."""
        data = {
            CouponFields.COUPON_CODE: "B3G1_CODE", CouponFields.TYPE: CouponType.BXGY,
            CouponFields.DESCRIPTION: "B3G1",
            CouponFields.METADATA: {
                MetadataKeys.BUY_PRODUCTS: [{"product_id": "A"}], MetadataKeys.BUY_QUANTITY: 3,
                MetadataKeys.GET_PRODUCTS: [{"product_id": "B"}], MetadataKeys.GET_QUANTITY: 1
            }
        }
        cp = self.coupon_service.create_coupon(data)
        self.assertEqual(cp.metadata[MetadataKeys.BUY_QUANTITY], 3)

    def test_create_bxgy_buy1_get2(self):
        """Positive: Buy 1 Get Multiple (2)."""
        data = {
            CouponFields.COUPON_CODE: "B1G2_CODE", CouponFields.TYPE: CouponType.BXGY,
            CouponFields.DESCRIPTION: "B1G2",
            CouponFields.METADATA: {
                MetadataKeys.BUY_PRODUCTS: [{"product_id": "A"}], MetadataKeys.BUY_QUANTITY: 1,
                MetadataKeys.GET_PRODUCTS: [{"product_id": "B"}], MetadataKeys.GET_QUANTITY: 2
            }
        }
        cp = self.coupon_service.create_coupon(data)
        self.assertEqual(cp.metadata[MetadataKeys.GET_QUANTITY], 2)

    def test_create_bxgy_pool_logic(self):
        """Positive: Buy from Pool (A/B) Get from Pool (C/D)."""
        data = {
            CouponFields.COUPON_CODE: "POOL_BXGY_CODE", CouponFields.TYPE: CouponType.BXGY,
            CouponFields.DESCRIPTION: "Pool test",
            CouponFields.METADATA: {
                MetadataKeys.BUY_PRODUCTS: [{"product_id": "A"}, {"product_id": "B"}],
                MetadataKeys.BUY_QUANTITY: 3,
                MetadataKeys.GET_PRODUCTS: [{"product_id": "C"}, {"product_id": "D"}],
                MetadataKeys.GET_QUANTITY: 1,
                MetadataKeys.REPETITION_LIMIT: 5
            }
        }
        cp = self.coupon_service.create_coupon(data)
        self.assertEqual(len(cp.metadata[MetadataKeys.BUY_PRODUCTS]), 2)
        self.assertEqual(len(cp.metadata[MetadataKeys.GET_PRODUCTS]), 2)
        self.assertEqual(cp.metadata[MetadataKeys.BUY_QUANTITY], 3)
        self.assertEqual(cp.metadata[MetadataKeys.REPETITION_LIMIT], 5)

    # --- 4. Negative Scenarios ---

    def test_create_coupon_negative_duplicate(self):
        """Negative: Raise error if code already exists (even if inactive)."""
        # 'CART10OFF' is in mock data
        data = {
            CouponFields.COUPON_CODE: "CART10OFF",
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "Duplicate test",
            CouponFields.METADATA: {}
        }
        with self.assertRaises(CouponAlreadyExists):
            self.coupon_service.create_coupon(data)
