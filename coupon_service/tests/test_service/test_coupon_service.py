from datetime import datetime, timezone
from unittest.mock import patch

from coupon_service.services.coupon_service import CouponService
from coupon_service.tests import TestBase
from coupon_service.tests.mock.mock_data import (
    MOCK_CART_WISE_COUPON_DATA,
    MOCK_PRODUCT_WISE_COUPON_DATA,
    MOCK_BXGY_COUPON_DATA,
)
from coupon_service.utils.constants import CouponType, CouponStatus, MetadataKeys, DefaultValues, SystemFields, CartKeys
from coupon_service.utils.errors import CouponNotFound, CouponAlreadyExists  # Import errors


class TestCouponService(TestBase):

    def setUp(self):

        self.mock_short_id_patch = patch("coupon_service.utils.id_generator.short_id", return_value="test_id_123")
        self.mock_short_id = self.mock_short_id_patch.start()

        self.coupon_service = CouponService(database=self.db)

        self.addCleanup(self.mock_short_id_patch.stop)

    def tearDown(self):
        pass

    # --- Test get_all_coupons ---
    def test_001_get_all_coupons_populated(self):
        coupons = self.coupon_service.get_all_coupons()
        self.assertEqual(len(coupons), 5)
        self.assertEqual(coupons[0].coupon_code, MOCK_CART_WISE_COUPON_DATA["coupon_code"])
        self.assertEqual(coupons[0].type, MOCK_CART_WISE_COUPON_DATA["type"])
        self.assertEqual(coupons[1].type, MOCK_PRODUCT_WISE_COUPON_DATA["type"])
        self.assertEqual(coupons[4].type, MOCK_BXGY_COUPON_DATA["type"])

    # --- Test get_coupon_by_code ---
    def test_002_get_coupon_by_code_success(self):
        coupon = self.coupon_service.get_coupon_by_code(MOCK_CART_WISE_COUPON_DATA["coupon_code"])
        self.assertEqual(coupon.coupon_code, MOCK_CART_WISE_COUPON_DATA["coupon_code"])

    def test_003_get_coupon_by_code_not_found(self):
        with self.assertRaises(CouponNotFound):
            self.coupon_service.get_coupon_by_code("NONEXISTENT")

    # --- Test get_coupon_by_id ---
    def test_004_get_coupon_by_id_success(self):
        coupon = self.coupon_service.get_coupon_by_id("test_id_1")
        self.assertEqual(coupon._id, "test_id_1")

    def test_005_get_coupon_by_id_not_found(self):
        with self.assertRaises(CouponNotFound):
            self.coupon_service.get_coupon_by_id("NONEXISTENT_ID")

    # --- Test create_coupon ---
    def test_006_create_coupon_success(self):
        new_coupon_data = {
            "coupon_code": "NEWTESTSERVICE",
            "type": CouponType.CART_WISE,
            "description": "New test coupon from service",
            "metadata": {MetadataKeys.MIN_CART_TOTAL: 75.0, MetadataKeys.DISCOUNT_PERCENTAGE: 15},
            "status": CouponStatus.ACTIVE,
        }
        coupon = self.coupon_service.create_coupon(new_coupon_data)
        self.assertIsNotNone(coupon._id)
        self.assertEqual(coupon.coupon_code, new_coupon_data["coupon_code"])
        # Verify it's in the DB
        found_coupon = self.coupons_collection.find_one({SystemFields.ID: coupon._id})
        self.assertIsNotNone(found_coupon)
        self.assertEqual(found_coupon["coupon_code"], new_coupon_data["coupon_code"])

    def test_007_create_coupon_already_exists(self):
        with self.assertRaises(CouponAlreadyExists):
            self.coupon_service.create_coupon(MOCK_CART_WISE_COUPON_DATA)  # Use existing coupon code

    # --- Test update_coupon ---
    def test_008_update_coupon_success(self):
        update_data = {"description": "New Description from Service"}
        updated_coupon = self.coupon_service.update_coupon(MOCK_CART_WISE_COUPON_DATA["coupon_code"], update_data)
        self.assertIsNotNone(updated_coupon)
        self.assertEqual(updated_coupon.description, "New Description from Service")
        # Verify it's updated in the DB
        found_coupon = self.coupons_collection.find_one({"coupon_code": MOCK_CART_WISE_COUPON_DATA["coupon_code"]})
        self.assertIsNotNone(found_coupon)
        self.assertEqual(found_coupon["description"], "New Description from Service")

    def test_009_update_coupon_not_found(self):
        update_data = {"description": "New Description"}
        with self.assertRaises(CouponNotFound):
            self.coupon_service.update_coupon("NONEXISTENT_CODE", update_data)

    # --- Test delete_coupon ---
    def test_010_delete_coupon_success(self):
        # Insert a temporary coupon to delete
        temp_coupon_data = {
            SystemFields.ID: "temp_delete_service_id",
            SystemFields.CREATED_AT: datetime.now(timezone.utc),
            SystemFields.MODIFIED_AT: datetime.now(timezone.utc),  # Renamed from updated_at
            SystemFields.CREATED_BY: DefaultValues.FLOBOT,  # Added
            SystemFields.MODIFIED_BY: DefaultValues.FLOBOT,  # Added
            "coupon_code": "TEMPDELETESERVICE",
            "type": CouponType.CART_WISE,
            "description": "Temporary coupon for service deletion test",
            "metadata": {},
            "status": CouponStatus.ACTIVE,
        }
        self.coupons_collection.insert_one(temp_coupon_data)

        self.coupon_service.delete_coupon("temp_delete_service_id")
        # Verify it's deleted from the DB
        found_coupon = self.coupons_collection.find_one({SystemFields.ID: "temp_delete_service_id"})
        self.assertIsNone(found_coupon)

    def test_011_delete_coupon_not_found(self):
        with self.assertRaises(CouponNotFound):
            self.coupon_service.delete_coupon("NONEXISTENT_ID")

    def test_012_update_coupon_to_inactive_and_retrieve(self):
        coupon_code = MOCK_CART_WISE_COUPON_DATA["coupon_code"]
        update_data = {"status": CouponStatus.INACTIVE}

        # Update coupon to inactive
        updated_coupon = self.coupon_service.update_coupon(coupon_code, update_data)
        self.assertIsNone(updated_coupon)
        self.assertRaises(CouponNotFound, self.coupon_service.get_coupon_by_code, coupon_code)

    # --- Test get_applicable_coupons ---
    def test_014_get_applicable_coupons_cart_wise_success(self):
        cart = {
            "items": [
                {"product_id": "prod_A", "quantity": 1, "price": 60.0},
                {"product_id": "prod_B", "quantity": 1, "price": 50.0},
            ]
        }  # Total 110.0

        applicable_coupons = self.coupon_service.get_applicable_coupons(cart)
        # Sort for consistent testing
        applicable_coupons.sort(key=lambda x: x["coupon_code"])

        # Expected applicable coupons:
        # CART10OFF (total 110 > 100) -> 11.0
        # CART100OFF10 (total 110 > 100) -> 11.0
        # PRODA20OFF (prod_A in cart) -> 12.0 (20% of 60)
        # BUYBGETC (prod_B in cart) -> 5.0
        self.assertEqual(len(applicable_coupons), 4)

        self.assertEqual(applicable_coupons[0]["coupon_code"], "BUYBGETC")
        self.assertEqual(round(applicable_coupons[0]["discount_amount"], 2), 5.0)

        # # Check CART100OFF10 (index 0 after sort)
        self.assertEqual(applicable_coupons[1]["coupon_code"], "CART100OFF10")
        self.assertEqual(round(applicable_coupons[1]["discount_amount"], 2), 11.0)

        # Check CART10OFF (index 1 after sort)
        self.assertEqual(applicable_coupons[2]["coupon_code"], "NEWTESTSERVICE")
        self.assertEqual(round(applicable_coupons[2]["discount_amount"], 2), 16.5)

        #
        # # Check PRODA20OFF (index 3 after sort)
        self.assertEqual(applicable_coupons[3]["coupon_code"], "PRODA20OFF")
        self.assertEqual(round(applicable_coupons[3]["discount_amount"], 2), 12.0)

    def test_015_get_applicable_coupons_product_wise_success(self):
        cart = {
            "items": [
                {"product_id": "prod_A", "quantity": 2, "price": 25.0},  # Total 50.0
                {"product_id": "prod_X", "quantity": 1, "price": 100.0},  # Total 100.0
            ]
        }  # Contains prod_X for PROD5OFF

        applicable_coupons = self.coupon_service.get_applicable_coupons(cart)
        # Sort for consistent testing
        applicable_coupons.sort(key=lambda x: x["coupon_code"])

        # Expected applicable coupons:
        # CART10OFF (total 150 > 100) -> 15.0
        # CART100OFF10 (total 150 > 100) -> 15.0
        # PROD5OFF (prod_X in cart) -> 5.0
        # PRODA20OFF (prod_A in cart) -> 10.0 (20% of 50)
        self.assertEqual(len(applicable_coupons), 4)

        # Check PROD5OFF (index 2 after sort)
        self.assertEqual(applicable_coupons[2]["coupon_code"], "PROD5OFF")
        self.assertEqual(round(applicable_coupons[2]["discount_amount"], 2), 5.0)

        # Check CART100OFF10 (index 0 after sort)
        self.assertEqual(applicable_coupons[0]["coupon_code"], "CART100OFF10")
        self.assertEqual(round(applicable_coupons[0]["discount_amount"], 2), 15.0)

        # Check PRODA20OFF (index 3 after sort)
        self.assertEqual(applicable_coupons[3]["coupon_code"], "PRODA20OFF")
        self.assertEqual(round(applicable_coupons[3]["discount_amount"], 2), 10.0)

        # Check CART10OFF (index 1 after sort)
        self.assertEqual(applicable_coupons[1]["coupon_code"], "NEWTESTSERVICE")
        self.assertEqual(round(applicable_coupons[1]["discount_amount"], 2), 22.5)

    def test_016_get_applicable_coupons_no_applicable(self):
        cart = {
            "items": [
                {"product_id": "prod_C", "quantity": 1, "price": 10.0},
            ]
        }

        applicable_coupons = self.coupon_service.get_applicable_coupons(cart)
        self.assertEqual(len(applicable_coupons), 0)

    def test_017_get_applicable_coupons_empty_cart(self):
        cart = {"items": []}
        applicable_coupons = self.coupon_service.get_applicable_coupons(cart)
        self.assertEqual(len(applicable_coupons), 0)

    def test_018_get_applicable_coupons_bxgy_success(self):
        cart = {
            "items": [
                {"product_id": "prod_B", "quantity": 1, "price": 20.0},
                {"product_id": "prod_C", "quantity": 1, "price": 10.0},
            ]
        }

        applicable_coupons = self.coupon_service.get_applicable_coupons(cart)
        # Sort for consistent testing
        applicable_coupons.sort(key=lambda x: x["coupon_code"])

        # Expected applicable coupons:
        # BUYBGETC (prod_B in cart) -> 5.0
        self.assertEqual(len(applicable_coupons), 1)

        # Check BUYBGETC (index 0 after sort)
        self.assertEqual(applicable_coupons[0]["coupon_code"], "BUYBGETC")
        self.assertEqual(applicable_coupons[0]["type"], CouponType.BXGY)
        self.assertEqual(applicable_coupons[0]["description"], "Buy Product B get Product C free")
        self.assertEqual(round(applicable_coupons[0]["discount_amount"], 2), 5.0)

    # --- Test apply_coupon_to_cart ---
    def test_019_apply_coupon_to_cart_cart_wise_success(self):
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "prod_A", CartKeys.QUANTITY: 1, CartKeys.PRICE: 60.0},
                {CartKeys.PRODUCT_ID: "prod_B", CartKeys.QUANTITY: 1, CartKeys.PRICE: 50.0},
            ]
        }  # Total 110.0
        coupon_id = "test_id_3"  # CART100OFF10

        updated_cart = self.coupon_service.apply_coupon_to_cart(coupon_id, cart)
        self.assertIsNotNone(updated_cart)
        self.assertIn(CartKeys.TOTAL_DISCOUNT, updated_cart)
        self.assertIn(CartKeys.FINAL_PRICE, updated_cart)
        self.assertIn(CartKeys.APPLIED_COUPON, updated_cart)
        self.assertAlmostEqual(updated_cart[CartKeys.TOTAL_DISCOUNT], 11.0)
        self.assertAlmostEqual(updated_cart[CartKeys.FINAL_PRICE], 99.0)
        self.assertEqual(updated_cart[CartKeys.APPLIED_COUPON]["coupon_id"], coupon_id)

    def test_020_apply_coupon_to_cart_product_wise_success(self):
        cart = {
            CartKeys.ITEMS: [
                {CartKeys.PRODUCT_ID: "prod_A", CartKeys.QUANTITY: 2, CartKeys.PRICE: 25.0},  # Total 50.0
                {CartKeys.PRODUCT_ID: "prod_X", CartKeys.QUANTITY: 1, CartKeys.PRICE: 100.0},  # Total 100.0
            ]
        }
        coupon_id = "test_id_2"  # PROD5OFF

        updated_cart = self.coupon_service.apply_coupon_to_cart(coupon_id, cart)
        self.assertIsNotNone(updated_cart)
        self.assertAlmostEqual(updated_cart[CartKeys.TOTAL_DISCOUNT], 5.0)
        self.assertAlmostEqual(updated_cart[CartKeys.FINAL_PRICE], 145.0)  # 150 - 5

    def test_021_apply_coupon_to_cart_non_existent_coupon(self):
        cart = {"items": [{"product_id": "prod_A", "quantity": 1, "price": 10.0}]}
        coupon_id = "NONEXISTENT_ID"

        with self.assertRaises(CouponNotFound):
            self.coupon_service.apply_coupon_to_cart(coupon_id, cart)

    def test_022_apply_coupon_to_cart_inactive_coupon(self):
        # Create an inactive coupon for testing
        inactive_coupon_data = {
            SystemFields.ID: "inactive_id",
            SystemFields.CREATED_AT: datetime.now(timezone.utc),
            SystemFields.MODIFIED_AT: datetime.now(timezone.utc),
            "coupon_code": "INACTIVE10",
            "type": CouponType.CART_WISE,
            "description": "Inactive coupon",
            "metadata": {MetadataKeys.MIN_CART_TOTAL: 10.0, MetadataKeys.DISCOUNT_PERCENTAGE: 10},
            "status": CouponStatus.INACTIVE,
        }
        self.coupons_collection.insert_one(inactive_coupon_data)

        cart = {"items": [{"product_id": "prod_A", "quantity": 1, "price": 20.0}]}
        coupon_id = "inactive_id"

        with self.assertRaises(CouponNotFound):  # CouponNotFound is raised if not active
            self.coupon_service.apply_coupon_to_cart(coupon_id, cart)

        # Clean up
        self.coupons_collection.delete_one({SystemFields.ID: "inactive_id"})

    def test_023_apply_coupon_to_cart_not_applicable(self):
        cart = {"items": [{"product_id": "prod_C", "quantity": 1, "price": 10.0}]}  # Total 10.0
        coupon_id = "test_id_3"  # CART100OFF10 (requires total > 100)

        with self.assertRaises(ValueError) as cm:
            self.coupon_service.apply_coupon_to_cart(coupon_id, cart)
        self.assertIn("not applicable", str(cm.exception))
