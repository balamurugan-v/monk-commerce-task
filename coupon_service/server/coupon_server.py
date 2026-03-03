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
        self.database = database

    def _get_collection(self) -> Collection:
        """Helper method to get the 'coupons' collection."""
        if self.database is not None:
            return getattr(self.database, CollectionNames.COUPONS)
        return getattr(g.db, CollectionNames.COUPONS)

    @staticmethod
    def _generate_id() -> str:
        """Generates a custom prefixed Snowflake ID."""
        return short_id()

    def find_by_code(self, coupon_code: str) -> Coupon | None:
        """
        Finds a single active coupon in the database by its user-facing code.
        Returns a Coupon object or None if not found or not active.
        """
        coupon_data = self._get_collection().find_one({"coupon_code": coupon_code, "status": CouponStatus.ACTIVE})
        if coupon_data:
            return Coupon.from_dict(coupon_data)
        return None

    def find_by_id(self, _id: str) -> Coupon | None:
        """
        Finds a single active coupon in the database by its internal _id.
        Returns a Coupon object or None if not found or not active.
        """
        coupon_data = self._get_collection().find_one({SystemFields.ID: _id, "status": CouponStatus.ACTIVE})
        if coupon_data:
            return Coupon.from_dict(coupon_data)
        return None

    def find_all(self) -> list[Coupon]:
        """
        Finds all coupons in the database.
        Returns a list of Coupon objects.
        """
        coupons_data = self._get_collection().find()
        return [Coupon.from_dict(data) for data in coupons_data]

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
        Generates _id and system fields.
        Raises CouponAlreadyExists if a coupon with the same code already exists.
        """
        if self.find_by_code(coupon.coupon_code):
            raise CouponAlreadyExists(coupon.coupon_code)

        now = datetime.now(timezone.utc)
        coupon._id = self._generate_id()
        coupon._created_at = now
        coupon._modified_at = now
        coupon._created_by = DefaultValues.FLOBOT
        coupon._modified_by = DefaultValues.FLOBOT

        coupon_dict = coupon.to_dict()
        # Remove any user-provided system fields for security
        system_fields = [
            SystemFields.ID,
            SystemFields.CREATED_AT,
            SystemFields.MODIFIED_AT,
            SystemFields.CREATED_BY,
            SystemFields.MODIFIED_BY,
        ]
        for key in system_fields:
            if key in coupon_dict:
                del coupon_dict[key]

        self._get_collection().insert_one(coupon.to_dict())
        return coupon

    def update(self, _id: str, update_data: dict) -> Coupon:
        """
        Updates an existing coupon in the database.
        Raises CouponNotFound if the coupon does not exist.
        """
        if not self.find_by_id(_id):
            raise CouponNotFound(_id)

        # Remove system fields from user payload to prevent tampering
        system_fields = [
            SystemFields.ID,
            SystemFields.CREATED_AT,
            SystemFields.MODIFIED_AT,
            SystemFields.CREATED_BY,
            SystemFields.MODIFIED_BY,
        ]
        for key in system_fields:
            if key in update_data:
                del update_data[key]

        # Set system fields
        update_data[SystemFields.MODIFIED_AT] = datetime.now(timezone.utc)
        update_data[SystemFields.MODIFIED_BY] = DefaultValues.FLOBOT

        self._get_collection().update_one({SystemFields.ID: _id}, {"$set": update_data})

        # Fetch the updated coupon to return the latest state
        return self.find_by_id(_id)

    def delete(self, _id: str):
        """
        Deletes a coupon from the database by its _id.
        Raises CouponNotFound if the coupon does not exist.
        """
        result = self._get_collection().delete_one({SystemFields.ID: _id})
        if result.deleted_count == 0:
            raise CouponNotFound(_id)


class UserCouponPurchaseServer:
    """
    Data Access Layer for User Coupon Purchase records.
    Handles interactions with the 'user_coupon_purchases' collection.
    """

    def __init__(self, database=None):
        self.database = database

    def _get_collection(self) -> Collection:
        """Helper method to get the 'user_coupon_purchases' collection."""
        if self.database is not None:
            return getattr(self.database, CollectionNames.USER_COUPON_PURCHASES)
        return getattr(g.db, CollectionNames.USER_COUPON_PURCHASES)

    def _generate_id(self) -> str:
        """Generates a custom prefixed Snowflake ID for purchase records."""
        return short_id()

    def insert_purchase_record(self, purchase_data: dict) -> dict:
        """
        Inserts a new user coupon purchase record into the database.
        Generates _id and applied_at timestamp.
        """
        now = datetime.now(timezone.utc)
        purchase_data[SystemFields.ID] = self._generate_id()
        purchase_data["applied_at"] = now

        self._get_collection().insert_one(purchase_data)
        return purchase_data
