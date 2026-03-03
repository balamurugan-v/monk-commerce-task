"""
Constants for the Coupon Service.
"""


class CouponType:
    CART_WISE = "cart-wise"
    PRODUCT_WISE = "product-wise"
    BXGY = "bxgy"


class CouponStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class CollectionNames:
    COUPONS = "coupons"
    USER_COUPON_PURCHASES = "user_coupon_purchases"


class SystemFields:
    ID = "_id"
    CREATED_AT = "_created_at"
    MODIFIED_AT = "_modified_at"
    CREATED_BY = "_created_by"
    MODIFIED_BY = "_modified_by"


class MetadataKeys:
    MIN_CART_TOTAL = "min_cart_total"
    DISCOUNT_PERCENTAGE = "discount_percentage"
    PRODUCT_ID = "product_id"
    BUY_PRODUCTS = "buy_products"
    GET_PRODUCTS = "get_products"
    FIXED_DISCOUNT_AMOUNT = "fixed_discount_amount"


class CartKeys:
    ITEMS = "items"
    PRODUCT_ID = "product_id"
    QUANTITY = "quantity"
    PRICE = "price"
    TOTAL_DISCOUNT = "total_discount"
    FINAL_PRICE = "final_price"
    APPLIED_COUPON = "applied_coupon"


class DefaultValues:
    FLOBOT = "flobot"


class BlueprintNames:
    COUPON_API = "coupon_api"
