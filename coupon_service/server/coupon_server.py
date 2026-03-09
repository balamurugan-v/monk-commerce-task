from datetime import datetime, timezone
from flask import g
from pymongo.collection import Collection
from coupon_service.utils.id_generator import short_id

from coupon_service.models import Coupon
from coupon_service.utils.errors import CouponAlreadyExists, CouponNotFound
from coupon_service.utils.constants import CollectionNames, SystemFields, CouponStatus, DefaultValues


class CouponServer:
    """
    The custom ODM/Data Access Layer for Coupon objects.
    Handles all direct interactions with MongoDB using pymongo.
    """

    def __init__(self, database=None):
        self._database = database

    def _get_collection(self) -> Collection:
        """Helper method to get the 'coupons' collection."""
        if self._database is not None:
            return getattr(self._database, CollectionNames.COUPONS)
        return getattr(g.db, CollectionNames.COUPONS)

    @staticmethod
    def _generate_id() -> str:
        """Generates a custom prefixed Snowflake ID."""
        return short_id()

    def find_by_code(self, coupon_code: str, include_inactive: bool = False) -> Coupon | None:
        """
        Finds a single coupon in the database by its user-facing code.
        Returns a Coupon object or None if not found.
        """
        query = {"coupon_code": coupon_code}
        if not include_inactive:
            query["status"] = CouponStatus.ACTIVE
            
        coupon_data = self._get_collection().find_one(query)
        if coupon_data:
            return Coupon.from_dict(coupon_data)
        return None

    def find_all_active(self) -> list[Coupon]:
        """
        Finds all active coupons in the database.
        Returns a list of Coupon objects.
        """
        coupons_data = self._get_collection().find({"status": CouponStatus.ACTIVE})
        return [Coupon.from_dict(data) for data in coupons_data]

    def insert(self, coupon: Coupon) -> Coupon:
        """
        Inserts a new coupon into the database.
        """
        if self.find_by_code(coupon.coupon_code, include_inactive=True):
            raise CouponAlreadyExists(coupon.coupon_code)

        now = datetime.now(timezone.utc)
        coupon._id = self._generate_id()
        coupon._created_at = now
        coupon._modified_at = now
        coupon._created_by = DefaultValues.FLOBOT
        coupon._modified_by = DefaultValues.FLOBOT

        self._get_collection().insert_one(coupon.to_dict())
        return coupon

    def update_by_code(self, coupon_code: str, update_data: dict) -> Coupon:
        """
        Updates an existing coupon in the database by its coupon_code.
        """
        # Set system fields
        update_data[SystemFields.MODIFIED_AT] = datetime.now(timezone.utc)
        update_data[SystemFields.MODIFIED_BY] = DefaultValues.FLOBOT

        self._get_collection().update_one({"coupon_code": coupon_code}, {"$set": update_data})

        # Fetch the updated coupon to return the latest state
        return self.find_by_code(coupon_code, include_inactive=True)

    def delete_by_code(self, coupon_code: str):
        """
        Deletes a coupon from the database by its coupon_code.
        """
        result = self._get_collection().delete_one({"coupon_code": coupon_code})
        if result.deleted_count == 0:
            raise CouponNotFound(coupon_code)


class UserCouponPurchaseServer:
    """
    Data Access Layer for User Coupon Purchase records.
    """

    def __init__(self, database=None):
        self._database = database

    def _get_collection(self) -> Collection:
        """Helper method to get the 'user_coupon_purchases' collection."""
        if self._database is not None:
            return getattr(self._database, CollectionNames.USER_COUPON_PURCHASES)
        return getattr(g.db, CollectionNames.USER_COUPON_PURCHASES)

    def _generate_id(self) -> str:
        """Generates a custom prefixed Snowflake ID for purchase records."""
        return short_id()

    def insert_purchase_record(self, purchase_data: dict) -> dict:
        """
        Inserts a new user coupon purchase record into the database.
        """
        now = datetime.now(timezone.utc)
        purchase_data[SystemFields.ID] = self._generate_id()
        purchase_data["applied_at"] = now

        self._get_collection().insert_one(purchase_data)
        return purchase_data
