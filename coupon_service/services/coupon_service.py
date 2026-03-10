from datetime import datetime, timezone
from coupon_service.models import Coupon
from coupon_service.server.coupon_server import CouponServer, UserCouponPurchaseServer
from coupon_service.utils.errors import CouponNotFound, CouponInactive, CouponLimitReachedError, CouponExpired
from coupon_service.services.strategy_factory import StrategyFactory
from coupon_service.utils.constants import CouponStatus, CartKeys, CouponFields, ResponseKeys, MetadataKeys


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
        If found but inactive or expired, raises CouponInactive or ValueError.
        """
        coupon = self.coupon_server.find_by_code(coupon_code, include_inactive=True)
        if not coupon:
            raise CouponNotFound(coupon_code)
        
        if coupon.status != CouponStatus.ACTIVE:
            raise CouponInactive(coupon_code)

        if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
            raise CouponExpired(coupon_code)
            
        return coupon

    def create_coupon(self, data: dict) -> Coupon:
        """
        Creates a new coupon. 
        Ensures status defaults to ACTIVE if not provided.
        """
        status = data.get(CouponFields.STATUS, CouponStatus.ACTIVE)
        expires_at = data.get(CouponFields.EXPIRES_AT)
        if expires_at and isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        new_coupon = Coupon(
            coupon_code=data[CouponFields.COUPON_CODE],
            type=data[CouponFields.TYPE],
            description=data[CouponFields.DESCRIPTION],
            metadata=data[CouponFields.METADATA],
            status=status,
            expires_at=expires_at
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

        if update_data.get(CouponFields.EXPIRES_AT) and isinstance(update_data[CouponFields.EXPIRES_AT], str):
            update_data[CouponFields.EXPIRES_AT] = datetime.fromisoformat(update_data[CouponFields.EXPIRES_AT])
                
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
        now = datetime.now(timezone.utc)

        for coupon in all_coupons:
            # Skip expired coupons
            if coupon.expires_at and coupon.expires_at < now:
                continue

            try:
                strategy = self.strategy_factory.get_strategy(coupon.type)
                if strategy.is_applicable(cart, coupon):
                    discount_amount = strategy.calculate_discount(cart, coupon)
                    if discount_amount > 0:
                        applicable_coupons_info.append(
                            {
                                ResponseKeys.COUPON_ID: coupon._id,
                                CouponFields.COUPON_CODE: coupon.coupon_code,
                                CouponFields.TYPE: coupon.type,
                                CouponFields.DESCRIPTION: coupon.description,
                                ResponseKeys.DISCOUNT: discount_amount,
                            }
                        )
            except (ValueError, CouponLimitReachedError):
                continue
        return applicable_coupons_info

    def apply_coupon_to_cart(self, coupon_code: str, cart: dict) -> dict:
        """
        Applies a specific coupon (by code) to the cart.
        """
        # Use get_coupon_by_code to ensure ACTIVE and NOT EXPIRED
        coupon = self.get_coupon_by_code(coupon_code)

        # Check repetition limit explicitly to raise specific error
        if coupon.metadata.get(MetadataKeys.REPETITION_LIMIT) == 0:
            raise CouponLimitReachedError(coupon_code)

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
            CartKeys.TOTAL_PRICE: current_total_price,
            CartKeys.TOTAL_DISCOUNT: total_discount,
            CartKeys.FINAL_PRICE: final_total
        }

        self.user_coupon_purchase_server.insert_purchase_record({
            ResponseKeys.COUPON_ID: coupon._id,
            CouponFields.COUPON_CODE: coupon.coupon_code,
            CartKeys.CART: cart,
            ResponseKeys.DISCOUNT_APPLIED: total_discount,
            CartKeys.FINAL_PRICE: final_total
        })

        return {ResponseKeys.UPDATED_CART: updated_cart}
