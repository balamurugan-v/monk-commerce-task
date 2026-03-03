from unittest.mock import MagicMock
from models import Coupon
from utils.errors import CouponNotFound, CouponAlreadyExists
from tests.mock.mock_data import MOCK_CART_WISE_COUPON_OBJ, MOCK_PRODUCT_WISE_COUPON_OBJ


class MockCouponServer:
    """
    A mock implementation of the CouponServer for testing purposes.
    Simulates database operations on an in-memory list of coupons.
    """

    def __init__(self, initial_coupons: list[Coupon] = None):
        self.coupons = {c._id: c for c in (initial_coupons if initial_coupons is not None else [])}
        self.coupons_by_code = {c.coupon_code: c for c in (initial_coupons if initial_coupons is not None else [])}
        self.insert = MagicMock(side_effect=self._mock_insert)
        self.find_by_code = MagicMock(side_effect=self._mock_find_by_code)
        self.find_by_id = MagicMock(side_effect=self._mock_find_by_id)
        self.find_all = MagicMock(side_effect=self._mock_find_all)
        self.update = MagicMock(side_effect=self._mock_update)
        self.delete = MagicMock(side_effect=self._mock_delete)

    def _mock_insert(self, coupon: Coupon) -> Coupon:
        if coupon.coupon_code in self.coupons_by_code:
            raise CouponAlreadyExists(coupon.coupon_code)
        coupon._id = f"mock_id_{len(self.coupons) + 1}"  # Simulate ID generation
        self.coupons[coupon._id] = coupon
        self.coupons_by_code[coupon.coupon_code] = coupon
        return coupon

    def _mock_find_by_code(self, coupon_code: str) -> Coupon | None:
        return self.coupons_by_code.get(coupon_code)

    def _mock_find_by_id(self, _id: str) -> Coupon | None:
        return self.coupons.get(_id)

    def _mock_find_all(self) -> list[Coupon]:
        return list(self.coupons.values())

    def _mock_update(self, _id: str, update_data: dict) -> Coupon:
        coupon = self.coupons.get(_id)
        if not coupon:
            raise CouponNotFound(_id)

        # Simulate update
        for key, value in update_data.items():
            setattr(coupon, key, value)
        self.coupons[_id] = coupon  # Update in dict
        self.coupons_by_code[coupon.coupon_code] = coupon  # Update in dict by code
        return coupon

    def _mock_delete(self, _id: str):
        if _id not in self.coupons:
            raise CouponNotFound(_id)
        coupon_code = self.coupons[_id].coupon_code
        del self.coupons[_id]
        del self.coupons_by_code[coupon_code]
