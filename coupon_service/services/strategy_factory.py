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
        """Calculates the total discount amount for the given cart and coupon."""
        pass

    @abstractmethod
    def get_discount_breakdown(self, cart: dict, coupon: Coupon) -> dict[str, float]:
        """
        Returns a mapping of product_id to the total discount applied to that product.
        Note: This doesn't handle multiple items of same product_id separately in the mapping,
        but can be adapted if needed.
        """
        pass


class CartWiseStrategy(DiscountStrategy):
    """Strategy for cart-wise coupons."""

    def is_applicable(self, cart: dict, coupon: Coupon) -> bool:
        min_cart_total = coupon.metadata.get(MetadataKeys.MIN_CART_TOTAL)
        if min_cart_total is None:
            return False

        current_cart_total = sum(item[CartKeys.PRICE] * item[CartKeys.QUANTITY] for item in cart.get(CartKeys.ITEMS, []))
        return current_cart_total >= min_cart_total

    def calculate_discount(self, cart: dict, coupon: Coupon) -> float:
        if not self.is_applicable(cart, coupon):
            return 0.0

        discount_percentage = coupon.metadata.get(MetadataKeys.DISCOUNT_PERCENTAGE)
        if discount_percentage is None:
            return 0.0

        current_cart_total = sum(item[CartKeys.PRICE] * item[CartKeys.QUANTITY] for item in cart.get(CartKeys.ITEMS, []))
        return current_cart_total * (discount_percentage / 100.0)

    def get_discount_breakdown(self, cart: dict, coupon: Coupon) -> dict[str, float]:
        # For cart-wise, we distribute the total discount across all items proportionally by their value
        total_discount = self.calculate_discount(cart, coupon)
        if total_discount <= 0:
            return {}

        current_cart_total = sum(item[CartKeys.PRICE] * item[CartKeys.QUANTITY] for item in cart.get(CartKeys.ITEMS, []))
        breakdown = {}
        for item in cart.get(CartKeys.ITEMS, []):
            item_total = item[CartKeys.PRICE] * item[CartKeys.QUANTITY]
            item_discount = (item_total / current_cart_total) * total_discount
            product_id = item[CartKeys.PRODUCT_ID]
            breakdown[product_id] = breakdown.get(product_id, 0.0) + item_discount
        return breakdown


class ProductWiseStrategy(DiscountStrategy):
    """Strategy for product-wise coupons."""

    def is_applicable(self, cart: dict, coupon: Coupon) -> bool:
        target_product_id = coupon.metadata.get(MetadataKeys.PRODUCT_ID)
        if target_product_id is None:
            return False

        for item in cart.get(CartKeys.ITEMS, []):
            if item.get(CartKeys.PRODUCT_ID) == target_product_id:
                return True
        return False

    def calculate_discount(self, cart: dict, coupon: Coupon) -> float:
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

    def get_discount_breakdown(self, cart: dict, coupon: Coupon) -> dict[str, float]:
        target_product_id = coupon.metadata.get(MetadataKeys.PRODUCT_ID)
        discount_percentage = coupon.metadata.get(MetadataKeys.DISCOUNT_PERCENTAGE)
        if not target_product_id or not discount_percentage:
            return {}

        breakdown = {}
        for item in cart.get(CartKeys.ITEMS, []):
            if item.get(CartKeys.PRODUCT_ID) == target_product_id:
                item_total = item[CartKeys.PRICE] * item[CartKeys.QUANTITY]
                item_discount = item_total * (discount_percentage / 100.0)
                breakdown[target_product_id] = breakdown.get(target_product_id, 0.0) + item_discount
        return breakdown


class BxGyStrategy(DiscountStrategy):
    """Strategy for Buy X Get Y coupons using Pool Logic."""

    def is_applicable(self, cart: dict, coupon: Coupon) -> bool:
        buy_products_config = coupon.metadata.get(MetadataKeys.BUY_PRODUCTS, [])
        buy_req_quantity = coupon.metadata.get(MetadataKeys.BUY_QUANTITY)
        
        if not buy_products_config or buy_req_quantity is None:
            return False

        buy_pool_ids = {p[CartKeys.PRODUCT_ID] for p in buy_products_config}
        
        # Calculate total quantity of items in the 'buy' pool
        total_buy_qty = 0
        for item in cart.get(CartKeys.ITEMS, []):
            if item[CartKeys.PRODUCT_ID] in buy_pool_ids:
                total_buy_qty += item[CartKeys.QUANTITY]
        
        # Must have at least one set of buy products
        if total_buy_qty < buy_req_quantity:
            return False

        # Also check if there are any 'get' products in the cart to discount
        get_products_config = coupon.metadata.get(MetadataKeys.GET_PRODUCTS, [])
        get_pool_ids = {p[CartKeys.PRODUCT_ID] for p in get_products_config}
        
        has_get_product = False
        for item in cart.get(CartKeys.ITEMS, []):
            if item[CartKeys.PRODUCT_ID] in get_pool_ids:
                has_get_product = True
                break
        
        return has_get_product

    def calculate_discount(self, cart: dict, coupon: Coupon) -> float:
        breakdown = self.get_discount_breakdown(cart, coupon)
        return sum(breakdown.values())

    def get_discount_breakdown(self, cart: dict, coupon: Coupon) -> dict[str, float]:
        if not self.is_applicable(cart, coupon):
            return {}

        # 1. Calculate Repetitions
        buy_products_config = coupon.metadata.get(MetadataKeys.BUY_PRODUCTS, [])
        buy_req_quantity = coupon.metadata.get(MetadataKeys.BUY_QUANTITY)
        buy_pool_ids = {p[CartKeys.PRODUCT_ID] for p in buy_products_config}
        
        total_buy_qty = 0
        for item in cart.get(CartKeys.ITEMS, []):
            if item[CartKeys.PRODUCT_ID] in buy_pool_ids:
                total_buy_qty += item[CartKeys.QUANTITY]
        
        repetitions = total_buy_qty // buy_req_quantity
        
        # 2. Apply Repetition Limit
        limit = coupon.metadata.get(MetadataKeys.REPETITION_LIMIT)
        if limit is not None:
            repetitions = min(repetitions, limit)
            
        if repetitions <= 0:
            return {}

        # 3. Identify 'Get' Pool and sort by price (cheapest first)
        get_products_config = coupon.metadata.get(MetadataKeys.GET_PRODUCTS, [])
        get_pool_ids = {p[CartKeys.PRODUCT_ID] for p in get_products_config}
        get_req_quantity_per_rep = coupon.metadata.get(MetadataKeys.GET_QUANTITY, 1)
        
        total_get_to_discount = repetitions * get_req_quantity_per_rep
        
        # Collect all eligible 'get' items as individual units to handle sorting
        eligible_items = []
        for item in cart.get(CartKeys.ITEMS, []):
            if item[CartKeys.PRODUCT_ID] in get_pool_ids:
                # Add each unit individually
                for _ in range(item[CartKeys.QUANTITY]):
                    eligible_items.append({
                        CartKeys.PRODUCT_ID: item[CartKeys.PRODUCT_ID],
                        CartKeys.PRICE: item[CartKeys.PRICE]
                    })
        
        # Sort by price ascending
        eligible_items.sort(key=lambda x: x[CartKeys.PRICE])
        
        # 4. Calculate Discount
        breakdown = {}
        for i in range(min(len(eligible_items), total_get_to_discount)):
            item = eligible_items[i]
            pid = item[CartKeys.PRODUCT_ID]
            price = item[CartKeys.PRICE]
            breakdown[pid] = breakdown.get(pid, 0.0) + price
            
        return breakdown


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
