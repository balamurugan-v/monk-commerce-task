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


class CouponFields:
    COUPON_CODE = "coupon_code"
    DESCRIPTION = "description"
    TYPE = "type"
    STATUS = "status"
    METADATA = "metadata"
    EXPIRES_AT = "expires_at"


class MetadataKeys:
    MIN_CART_TOTAL = "min_cart_total"
    DISCOUNT_PERCENTAGE = "discount_percentage"
    PRODUCT_ID = "product_id"
    BUY_PRODUCTS = "buy_products"
    GET_PRODUCTS = "get_products"
    BUY_QUANTITY = "buy_quantity"
    GET_QUANTITY = "get_quantity"
    FIXED_DISCOUNT_AMOUNT = "fixed_discount_amount"
    REPETITION_LIMIT = "repetition_limit"
    QUANTITY = "quantity"


class CartKeys:
    ITEMS = "items"
    PRODUCT_ID = "product_id"
    QUANTITY = "quantity"
    PRICE = "price"
    TOTAL_DISCOUNT = "total_discount"
    FINAL_PRICE = "final_price"
    APPLIED_COUPON = "applied_coupon"
    TOTAL_PRICE = "total_price"
    CART = "cart"


class ResponseKeys:
    DISCOUNT = "discount"
    MESSAGE = "message"
    ERROR = "error"
    UPDATED_CART = "updated_cart"
    APPLICABLE_COUPONS = "applicable_coupons"
    COUPON_ID = "coupon_id"
    DISCOUNT_APPLIED = "discount_applied"


class MongoOperators:
    SET = "$set"


class HttpMethods:
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class HttpStatusCodes:
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    INTERNAL_SERVER_ERROR = 500


class DefaultValues:
    FLOBOT = "flobot"


class BlueprintNames:
    COUPON_API = "coupon_api"
