from coupon_service.models import Coupon
from coupon_service.server.coupon_server import CouponServer, UserCouponPurchaseServer
from coupon_service.utils.errors import CouponNotFound
from coupon_service.services.strategy_factory import StrategyFactory  # Import StrategyFactory
from coupon_service.utils.constants import CouponStatus, CartKeys


class CouponService:
    """
    This service contains the core business logic for coupon operations.
    It orchestrates interactions with the CouponServer (data layer).
    """

    def __init__(self, database=None):
        self._database = database
        self._coupon_server = None
        self._user_coupon_purchase_server = None
        self.strategy_factory = StrategyFactory()  # Will be implemented later

    @property
    def coupon_server(self):
        if self._coupon_server is None:
            self._coupon_server = CouponServer(database=self._database)
        return self._coupon_server

    @property
    def user_coupon_purchase_server(self):
        if self._user_coupon_purchase_server is None:
            self._user_coupon_purchase_server = UserCouponPurchaseServer(database=self._database)
        return self._user_coupon_purchase_server

    def get_all_coupons(self) -> list[Coupon]:
        """
        Retrieves all coupons from the database.
        """
        return self.coupon_server.find_all()

    def get_coupon_by_code(self, coupon_code: str) -> Coupon:
        """
        Retrieves a single coupon by its user-facing code.
        Raises CouponNotFound if the coupon does not exist.
        """
        coupon = self.coupon_server.find_by_code(coupon_code)
        if not coupon:
            raise CouponNotFound(coupon_code)
        return coupon

    def get_coupon_by_id(self, _id: str) -> Coupon:
        """
        Retrieves a single coupon by its internal _id.
        Raises CouponNotFound if the coupon does not exist.
        """
        coupon = self.coupon_server.find_by_id(_id)
        if not coupon:
            raise CouponNotFound(_id)
        return coupon

    def create_coupon(self, data: dict) -> Coupon:
        """
        Creates a new coupon.
        """
        new_coupon = Coupon(
            coupon_code=data["coupon_code"],
            type=data["type"],
            description=data["description"],
            metadata=data["metadata"],
            status=data["status"],
        )
        return self.coupon_server.insert(new_coupon)

    def update_coupon(self, coupon_code: str, update_data: dict) -> Coupon:
        """
        Updates an existing coupon.
        """
        coupon = self.coupon_server.find_by_code(coupon_code)
        if not coupon:
            raise CouponNotFound(coupon_code)
        return self.coupon_server.update(coupon._id, update_data)

    def delete_coupon(self, _id: str):
        """
        Deletes a coupon.
        """
        self.coupon_server.delete(_id)

    def get_applicable_coupons(self, cart: dict) -> list[dict]:
        """
        Fetches all active coupons and determines which ones are applicable to the given cart.
        Calculates the potential discount for each applicable coupon.
        """
        all_coupons = self.coupon_server.find_all_active()  # Assuming find_all_active exists or needs to be added
        applicable_coupons_info = []

        for coupon in all_coupons:
            try:
                strategy = self.strategy_factory.get_strategy(coupon.type)
                if strategy.is_applicable(cart, coupon):
                    discount_amount = strategy.calculate_discount(cart, coupon)
                    if discount_amount > 0:
                        applicable_coupons_info.append(
                            {
                                "coupon_id": coupon._id,
                                "coupon_code": coupon.coupon_code,
                                "type": coupon.type,
                                "description": coupon.description,
                                "discount_amount": discount_amount,
                            }
                        )
            except ValueError:
                # Log unknown coupon type, or handle as appropriate
                continue
        return applicable_coupons_info

    def apply_coupon_to_cart(self, coupon_id: str, cart: dict) -> dict:
        """
        Applies a specific coupon to the cart, calculates the final prices,
        and returns the updated cart.
        """
        coupon = self.coupon_server.find_by_id(coupon_id)
        if not coupon or coupon.status != CouponStatus.ACTIVE:
            raise CouponNotFound(coupon_id)

        strategy = self.strategy_factory.get_strategy(coupon.type)
        if not strategy.is_applicable(cart, coupon):
            raise ValueError(f"Coupon {coupon_id} is not applicable to the given cart.")

        discount_amount = strategy.calculate_discount(cart, coupon)

        updated_cart = cart.copy()
        current_total = sum(item[CartKeys.PRICE] * item[CartKeys.QUANTITY] for item in cart.get(CartKeys.ITEMS, []))
        final_total = current_total - discount_amount

        updated_cart[CartKeys.TOTAL_DISCOUNT] = discount_amount
        updated_cart[CartKeys.FINAL_PRICE] = final_total
        updated_cart[CartKeys.APPLIED_COUPON] = {
            "coupon_id": coupon._id,
            "coupon_code": coupon.coupon_code,
            "type": coupon.type,
            "discount_amount": discount_amount,
        }
        # In a more complex scenario, item-level discounts would be applied here.
        # For now, we're applying a total discount.

        return updated_cart

    # --- Future Implementations (Strategy Pattern) ---
    # def is_coupon_applicable(self, coupon: Coupon, cart: dict) -> bool:
    #     """
    #     Determines if a coupon is applicable to a given cart.
    #     Uses the Strategy pattern.
    #     """
    #     strategy = self.strategy_factory.get_strategy(coupon.type)
    #     return strategy.is_applicable(cart, coupon)

    # def calculate_discount(self, coupon: Coupon, cart: dict) -> float:
    #     """
    #     Calculates the discount amount for a given coupon and cart.
    #     Uses the Strategy pattern.
    #     """
    #     strategy = self.strategy_factory.get_strategy(coupon.type)
    #     return strategy.calculate_discount(cart, coupon)
