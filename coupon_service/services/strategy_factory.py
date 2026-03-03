from abc import ABC, abstractmethod
from coupon_service.models import Coupon
from coupon_service.utils.constants import CouponType, MetadataKeys, CartKeys


class DiscountStrategy(ABC):
    """Abstract base class for all discount strategies."""

    @abstractmethod
    def is_applicable(self, cart: dict, coupon: Coupon) -> bool:
        """Determines if the coupon is applicable to the given cart."""
        pass

    @abstractmethod
    def calculate_discount(self, cart: dict, coupon: Coupon) -> float:
        """Calculates the discount amount for the given cart and coupon."""
        pass


class CartWiseStrategy(DiscountStrategy):
    """Strategy for cart-wise coupons."""

    def is_applicable(self, cart: dict, coupon: Coupon) -> bool:
        # Example: Check if cart total meets minimum threshold
        min_cart_total = coupon.metadata.get(MetadataKeys.MIN_CART_TOTAL)
        if min_cart_total is None:
            return False  # Or raise an error, depending on expected metadata

        current_cart_total = sum(item[CartKeys.PRICE] * item[CartKeys.QUANTITY] for item in cart.get(CartKeys.ITEMS, []))
        return current_cart_total >= min_cart_total

    def calculate_discount(self, cart: dict, coupon: Coupon) -> float:
        # Example: Apply percentage discount to total
        if not self.is_applicable(cart, coupon):
            return 0.0

        discount_percentage = coupon.metadata.get(MetadataKeys.DISCOUNT_PERCENTAGE)
        if discount_percentage is None:
            return 0.0

        current_cart_total = sum(item[CartKeys.PRICE] * item[CartKeys.QUANTITY] for item in cart.get(CartKeys.ITEMS, []))
        return current_cart_total * (discount_percentage / 100.0)


class ProductWiseStrategy(DiscountStrategy):
    """Strategy for product-wise coupons."""

    def is_applicable(self, cart: dict, coupon: Coupon) -> bool:
        # Example: Check if specific product is in cart
        target_product_id = coupon.metadata.get(MetadataKeys.PRODUCT_ID)
        if target_product_id is None:
            return False

        for item in cart.get(CartKeys.ITEMS, []):
            if item.get(CartKeys.PRODUCT_ID) == target_product_id:
                return True
        return False

    def calculate_discount(self, cart: dict, coupon: Coupon) -> float:
        # Example: Apply percentage discount to target product's total
        if not self.is_applicable(cart, coupon):
            return 0.0

        target_product_id = coupon.metadata.get(MetadataKeys.PRODUCT_ID)
        discount_percentage = coupon.metadata.get(MetadataKeys.DISCOUNT_PERCENTAGE)
        if target_product_id is None or discount_percentage is None:
            return 0.0

        product_total = 0.0
        for item in cart.get(CartKeys.ITEMS, []):
            if item.get(CartKeys.PRODUCT_ID) == target_product_id:
                product_total += item[CartKeys.PRICE] * item[CartKeys.QUANTITY]

        return product_total * (discount_percentage / 100.0)


class BxGyStrategy(DiscountStrategy):
    """Strategy for Buy X Get Y coupons."""

    def is_applicable(self, cart: dict, coupon: Coupon) -> bool:
        # This is a complex strategy, simplified for initial implementation.
        # Full implementation would involve checking quantities of 'buy_products'
        # and ensuring 'get_products' can be applied.
        # For now, let's just check if any 'buy_products' are in the cart.
        buy_products_config = coupon.metadata.get(MetadataKeys.BUY_PRODUCTS)
        if not buy_products_config:
            return False

        cart_product_ids = {item[CartKeys.PRODUCT_ID] for item in cart.get(CartKeys.ITEMS, [])}

        for buy_item in buy_products_config:
            if buy_item[CartKeys.PRODUCT_ID] in cart_product_ids:
                return True
        return False

    def calculate_discount(self, cart: dict, coupon: Coupon) -> float:
        # This is a complex strategy, simplified for initial implementation.
        # Full implementation would involve calculating how many times the BxGy
        # deal can be applied and the value of the 'get' products.
        # For now, return a fixed discount if applicable.
        if not self.is_applicable(cart, coupon):
            return 0.0

        # Placeholder: Assume a fixed discount amount for simplicity
        # In a real scenario, this would calculate the value of the 'get' items
        # based on the cart contents and repetition limit.
        return coupon.metadata.get(MetadataKeys.FIXED_DISCOUNT_AMOUNT, 0.0)


class StrategyFactory:
    """Factory to get the appropriate discount strategy based on coupon type."""

    def get_strategy(self, coupon_type: str) -> DiscountStrategy:
        if coupon_type == CouponType.CART_WISE:
            return CartWiseStrategy()
        elif coupon_type == CouponType.PRODUCT_WISE:
            return ProductWiseStrategy()
        elif coupon_type == CouponType.BXGY:
            return BxGyStrategy()
        else:
            raise ValueError(f"Unknown coupon type: {coupon_type}")
