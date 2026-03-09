from coupon_service.models import Coupon
from coupon_service.server.coupon_server import CouponServer, UserCouponPurchaseServer
from coupon_service.utils.errors import CouponNotFound, CouponInactive
from coupon_service.services.strategy_factory import StrategyFactory
from coupon_service.utils.constants import CouponStatus, CartKeys, CouponFields


class CouponService:
    """
    This service contains the core business logic for coupon operations.
    Refactored to use coupon_code as the primary identifier for API consumers.
    """

    def __init__(self, database=None):
        self._database = database
        self._coupon_server = None
        self._user_coupon_purchase_server = None
        self.strategy_factory = StrategyFactory()

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

    def get_all_active_coupons(self) -> list[Coupon]:
        """
        Retrieves ONLY ACTIVE coupons from the database.
        """
        return self.coupon_server.find_all_active()

    def get_coupon_by_code(self, coupon_code: str) -> Coupon:
        """
        Retrieves a single coupon by its user-facing code.
        If found but inactive, raises CouponInactive.
        """
        coupon = self.coupon_server.find_by_code(coupon_code, include_inactive=True)
        if not coupon:
            raise CouponNotFound(coupon_code)
        
        if coupon.status != CouponStatus.ACTIVE:
            raise CouponInactive(coupon_code)
            
        return coupon

    def create_coupon(self, data: dict) -> Coupon:
        """
        Creates a new coupon. 
        Ensures status defaults to ACTIVE if not provided.
        """
        status = data.get(CouponFields.STATUS, CouponStatus.ACTIVE)
        
        new_coupon = Coupon(
            coupon_code=data[CouponFields.COUPON_CODE],
            type=data[CouponFields.TYPE],
            description=data[CouponFields.DESCRIPTION],
            metadata=data[CouponFields.METADATA],
            status=status,
        )
        return self.coupon_server.insert(new_coupon)

    def update_coupon(self, coupon_code: str, update_data: dict) -> Coupon:
        """
        Updates an existing coupon by its coupon_code.
        Gatekeeper Logic:
        1. If coupon is inactive, only allow update if status is being set to ACTIVE.
        """
        coupon = self.coupon_server.find_by_code(coupon_code, include_inactive=True)
        if not coupon:
            raise CouponNotFound(coupon_code)
            
        if coupon.status != CouponStatus.ACTIVE:
            is_activating = update_data.get(CouponFields.STATUS) == CouponStatus.ACTIVE
            if not is_activating:
                raise CouponInactive(coupon_code)
                
        return self.coupon_server.update_by_code(coupon_code, update_data)

    def delete_coupon(self, coupon_code: str):
        """
        Deletes a coupon by its coupon_code.
        """
        self.coupon_server.delete_by_code(coupon_code)

    def get_applicable_coupons(self, cart: dict) -> list[dict]:
        """
        Fetches all active coupons and determines which ones are applicable.
        """
        all_coupons = self.coupon_server.find_all_active()
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
                                "discount": discount_amount,
                            }
                        )
            except ValueError:
                continue
        return applicable_coupons_info

    def apply_coupon_to_cart(self, coupon_code: str, cart: dict) -> dict:
        """
        Applies a specific coupon (by code) to the cart.
        """
        coupon = self.coupon_server.find_by_code(coupon_code, include_inactive=True)
        if not coupon:
            raise CouponNotFound(coupon_code)
            
        if coupon.status != CouponStatus.ACTIVE:
            raise CouponInactive(coupon_code)

        strategy = self.strategy_factory.get_strategy(coupon.type)
        if not strategy.is_applicable(cart, coupon):
            raise ValueError(f"Coupon {coupon_code} is not applicable to the given cart.")

        discount_breakdown = strategy.get_discount_breakdown(cart, coupon)
        total_discount = sum(discount_breakdown.values())

        updated_items = []
        current_total_price = 0
        for item in cart.get(CartKeys.ITEMS, []):
            product_id = item[CartKeys.PRODUCT_ID]
            price = item[CartKeys.PRICE]
            qty = item[CartKeys.QUANTITY]
            
            item_total = price * qty
            current_total_price += item_total
            
            item_discount = discount_breakdown.get(product_id, 0.0)
            
            updated_item = item.copy()
            updated_item[CartKeys.TOTAL_DISCOUNT] = item_discount
            updated_items.append(updated_item)

        final_total = current_total_price - total_discount

        updated_cart = {
            CartKeys.ITEMS: updated_items,
            "total_price": current_total_price,
            CartKeys.TOTAL_DISCOUNT: total_discount,
            CartKeys.FINAL_PRICE: final_total
        }

        self.user_coupon_purchase_server.insert_purchase_record({
            "coupon_id": coupon._id,
            "coupon_code": coupon.coupon_code,
            "cart": cart,
            "discount_applied": total_discount,
            "final_price": final_total
        })

        return {"updated_cart": updated_cart}
