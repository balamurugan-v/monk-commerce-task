import unittest
from pymongo import MongoClient
from datetime import datetime, timezone
from coupon_service.tests.mock.mock_data import (
    MOCK_CART_WISE_COUPON_DATA,
    MOCK_PRODUCT_WISE_COUPON_DATA,
    MOCK_CART_WISE_COUPON_THRESHOLD,
    MOCK_PRODUCT_WISE_COUPON_PRODA,
    MOCK_BXGY_COUPON,
)
from coupon_service.utils.constants import SystemFields, DefaultValues, CouponFields, CouponStatus


class TestBase(unittest.TestCase):
    """
    Base class for tests, providing common setup and teardown for MongoDB.
    """

    @classmethod
    def setUpClass(cls):
        # Establish actual MongoDB connection
        cls.mongo_client = MongoClient("mongodb://localhost:27017/")
        cls.db = cls.mongo_client.get_database("test_coupon_db")

        # Explicitly drop the database to ensure a clean slate
        cls.mongo_client.drop_database(cls.db.name)

        # Get references to collections
        cls.coupons_collection = cls.db.coupons
        cls.user_coupon_purchases_collection = cls.db.user_coupon_purchases

        # Insert initial mock coupon data into cls.coupons_collection
        now = datetime.now(timezone.utc)
        
        def prepare_mock(data, _id):
            return {
                SystemFields.ID: _id,
                SystemFields.CREATED_AT: now,
                SystemFields.MODIFIED_AT: now,
                SystemFields.CREATED_BY: DefaultValues.FLOBOT,
                SystemFields.MODIFIED_BY: DefaultValues.FLOBOT,
                **data
            }

        mock_coupon_data_1 = prepare_mock(MOCK_CART_WISE_COUPON_DATA, "test_id_1")
        mock_coupon_data_2 = prepare_mock(MOCK_PRODUCT_WISE_COUPON_DATA, "test_id_2")
        mock_coupon_data_3 = prepare_mock(MOCK_CART_WISE_COUPON_THRESHOLD, "test_id_3")
        mock_coupon_data_4 = prepare_mock(MOCK_PRODUCT_WISE_COUPON_PRODA, "test_id_4")
        mock_coupon_data_5 = prepare_mock(MOCK_BXGY_COUPON, "test_id_5")

        cls.coupons_collection.insert_many(
            [
                mock_coupon_data_1,
                mock_coupon_data_2,
                mock_coupon_data_3,
                mock_coupon_data_4,
                mock_coupon_data_5,
            ]
        )

    @classmethod
    def tearDownClass(cls):
        # Explicitly drop the database
        cls.mongo_client.drop_database(cls.db.name)

        # Close MongoDB connection
        cls.mongo_client.close()

