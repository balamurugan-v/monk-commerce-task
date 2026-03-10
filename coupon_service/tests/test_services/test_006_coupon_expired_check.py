import unittest
from datetime import datetime, timedelta, timezone
from coupon_service.services.coupon_service import CouponService
from coupon_service.utils.constants import (
    CouponType,
    CouponFields,
    MetadataKeys,
    CartKeys,
    ResponseKeys
)
from coupon_service.utils.errors import CouponExpired
from coupon_service.tests.test_services import TestBase

class TestCouponExpiredCheck(TestBase):
    """
    Combined test suite for coupon expiration logic and PDF-style BxGy metadata format.
    """
    def setUp(self):
        self.coupon_service = CouponService(database=self.db)
        self.default_cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "P1", CartKeys.QUANTITY: 1, CartKeys.PRICE: 100.0}
            ]
        }

    # ============================================================================
    # 1. EXPIRATION - POSITIVE CASES
    # ============================================================================

    def test_no_expiration_date(self):
        """Positive: Coupon with expires_at=None should never expire."""
        code = "PERMANENT_COUPON"
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: code,
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "No expiry",
            CouponFields.EXPIRES_AT: None,
            CouponFields.METADATA: {
                MetadataKeys.MIN_CART_TOTAL: 10,
                MetadataKeys.DISCOUNT_PERCENTAGE: 10
            }
        })
        applicable = self.coupon_service.get_applicable_coupons(self.default_cart)
        self.assertIn(code, [c[CouponFields.COUPON_CODE] for c in applicable])

    def test_future_expiration(self):
        """Positive: Coupon with future expires_at is applicable."""
        code = "FUTURE_COUPON"
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: code,
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "Future expiry",
            CouponFields.EXPIRES_AT: future_date.isoformat(),
            CouponFields.METADATA: {
                MetadataKeys.MIN_CART_TOTAL: 10,
                MetadataKeys.DISCOUNT_PERCENTAGE: 10
            }
        })
        applicable = self.coupon_service.get_applicable_coupons(self.default_cart)
        self.assertIn(code, [c[CouponFields.COUPON_CODE] for c in applicable])

    # ============================================================================
    # 2. EXPIRATION - NEGATIVE CASES
    # ============================================================================

    def test_past_expiration(self):
        """Negative: Coupon with past expires_at is not applicable and cannot be applied."""
        code = "PAST_COUPON"
        past_date = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: code,
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "Past expiry",
            CouponFields.EXPIRES_AT: past_date.isoformat(),
            CouponFields.METADATA: {
                MetadataKeys.MIN_CART_TOTAL: 10,
                MetadataKeys.DISCOUNT_PERCENTAGE: 10
            }
        })
        
        # Should not be in applicable list
        applicable = self.coupon_service.get_applicable_coupons(self.default_cart)
        self.assertNotIn(code, [c[CouponFields.COUPON_CODE] for c in applicable])
        
        # Should raise CouponExpired when applied directly
        with self.assertRaises(CouponExpired):
            self.coupon_service.apply_coupon_to_cart(code, self.default_cart)

    # ============================================================================
    # 3. EXPIRATION - EDGE CASES
    # ============================================================================

    def test_re_enabling_expired_coupon(self):
        """Edge: Updating an expired coupon to a future date makes it applicable again."""
        code = "EXPIRED_TO_ACTIVE"
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: code,
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "Initially expired",
            CouponFields.EXPIRES_AT: past_date.isoformat(),
            CouponFields.METADATA: {
                MetadataKeys.MIN_CART_TOTAL: 10,
                MetadataKeys.DISCOUNT_PERCENTAGE: 10
            }
        })

        # Verify it's expired
        with self.assertRaises(CouponExpired):
            self.coupon_service.apply_coupon_to_cart(code, self.default_cart)

        # Update to future date
        future_date = datetime.now(timezone.utc) + timedelta(days=1)
        self.coupon_service.update_coupon(code, {CouponFields.EXPIRES_AT: future_date.isoformat()})

        # Verify it's now applicable
        applicable = self.coupon_service.get_applicable_coupons(self.default_cart)
        self.assertIn(code, [c[CouponFields.COUPON_CODE] for c in applicable])
        
        # Verify it can be applied
        response = self.coupon_service.apply_coupon_to_cart(code, self.default_cart)
        self.assertIsNotNone(response)

    def test_removing_expiration_limit(self):
        """Edge: Setting expires_at to None on an expired coupon makes it permanent."""
        code = "EXPIRED_TO_PERMANENT"
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: code,
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "Initially expired",
            CouponFields.EXPIRES_AT: past_date.isoformat(),
            CouponFields.METADATA: {
                MetadataKeys.MIN_CART_TOTAL: 10,
                MetadataKeys.DISCOUNT_PERCENTAGE: 10
            }
        })

        # Update expires_at to None (removing expiration)
        self.coupon_service.update_coupon(code, {CouponFields.EXPIRES_AT: None})

        # Verify it's now applicable
        applicable = self.coupon_service.get_applicable_coupons(self.default_cart)
        self.assertIn(code, [c[CouponFields.COUPON_CODE] for c in applicable])

    def test_exact_boundary_condition(self):
        """Edge: Coupon expiring right now (microsecond before) should be expired."""
        code = "BOUNDARY_COUPON"
        now_minus_tiny = datetime.now(timezone.utc) - timedelta(microseconds=1)
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: code,
            CouponFields.TYPE: CouponType.CART_WISE,
            CouponFields.DESCRIPTION: "Boundary expiry",
            CouponFields.EXPIRES_AT: now_minus_tiny.isoformat(),
            CouponFields.METADATA: {
                MetadataKeys.MIN_CART_TOTAL: 10,
                MetadataKeys.DISCOUNT_PERCENTAGE: 10
            }
        })
        
        with self.assertRaises(CouponExpired):
            self.coupon_service.apply_coupon_to_cart(code, self.default_cart)

    # ============================================================================
    # 4. MISSED CASES - BXGY PDF FORMAT
    # ============================================================================

    def test_bxgy_pdf_metadata_format(self):
        """Verify BxGy logic with quantity inside the product list (PDF style)."""
        code = "BXGY_PDF_STYLE"
        self.coupon_service.create_coupon({
            CouponFields.COUPON_CODE: code,
            CouponFields.TYPE: CouponType.BXGY,
            CouponFields.DESCRIPTION: "Buy 3 P1, Get 1 P2 Free",
            CouponFields.METADATA: {
                MetadataKeys.BUY_PRODUCTS: [{CartKeys.PRODUCT_ID: "P1", MetadataKeys.QUANTITY: 3}],
                MetadataKeys.GET_PRODUCTS: [{CartKeys.PRODUCT_ID: "P2", MetadataKeys.QUANTITY: 1}],
                MetadataKeys.REPETITION_LIMIT: 1
            }
        })

        # Cart with 3 P1 and 1 P2
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "P1", CartKeys.QUANTITY: 3, CartKeys.PRICE: 10.0},
                {CartKeys.PRODUCT_ID: "P2", CartKeys.QUANTITY: 1, CartKeys.PRICE: 20.0}
            ]
        }

        response = self.coupon_service.apply_coupon_to_cart(code, cart)
        updated_cart = response[ResponseKeys.UPDATED_CART]
        
        # P2 should be free (discount = 20.0)
        self.assertEqual(updated_cart[CartKeys.TOTAL_DISCOUNT], 20.0)
        
        # Check item breakdown
        p2_item = next(item for item in updated_cart[CartKeys.ITEMS] if item[CartKeys.PRODUCT_ID] == "P2")
        self.assertEqual(p2_item[CartKeys.TOTAL_DISCOUNT], 20.0)
