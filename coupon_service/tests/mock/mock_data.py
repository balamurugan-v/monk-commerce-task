from datetime import datetime, timezone
from coupon_service.utils.constants import CouponType, CouponStatus, MetadataKeys

# --- Mock Coupon Data ---

MOCK_CART_WISE_COUPON_DATA = {
    "coupon_code": "CART10OFF",
    "description": "10% off on orders over $100",
    "type": CouponType.CART_WISE,
    "status": CouponStatus.ACTIVE,
    "metadata": {MetadataKeys.MIN_CART_TOTAL: 100.00, MetadataKeys.DISCOUNT_PERCENTAGE: 10},
}

MOCK_PRODUCT_WISE_COUPON_DATA = {
    "coupon_code": "PROD5OFF",
    "description": "5% off on ProductX",
    "type": CouponType.PRODUCT_WISE,
    "status": CouponStatus.ACTIVE,
    "metadata": {MetadataKeys.PRODUCT_ID: "prod_X", MetadataKeys.DISCOUNT_PERCENTAGE: 5},
}

MOCK_BXGY_COUPON_DATA = {
    "coupon_code": "B2G1FREE",
    "description": "Buy 2 ProductY, Get 1 ProductZ Free",
    "type": CouponType.BXGY,
    "status": CouponStatus.ACTIVE,
    "metadata": {
        MetadataKeys.BUY_PRODUCTS: [{"product_id": "prod_Y", "quantity": 2}],
        "get_products": [{"product_id": "prod_Z", "quantity": 1}],
        "repetition_limit": 1,
    },
}

# --- Mock Cart Data ---

MOCK_CART_DATA = {
    "items": [
        {"product_id": "prod_A", "quantity": 1, "price": 50.00},
        {"product_id": "prod_B", "quantity": 2, "price": 25.00},
    ]
}

# --- Mock Coupon Objects (for return values) ---
# These would typically be created from the MOCK_..._COUPON_DATA by the server layer
# For testing, we can create them directly
from coupon_service.models import Coupon


def create_mock_coupon(data: dict, _id: str = "mock_id_123") -> Coupon:
    return Coupon(_id=_id, _created_at=datetime.now(timezone.utc), _modified_at=datetime.now(timezone.utc), **data)


MOCK_CART_WISE_COUPON_OBJ = create_mock_coupon(MOCK_CART_WISE_COUPON_DATA, _id="cart_wise_id")
MOCK_PRODUCT_WISE_COUPON_OBJ = create_mock_coupon(MOCK_PRODUCT_WISE_COUPON_DATA, _id="prod_wise_id")
MOCK_BXGY_COUPON_OBJ = create_mock_coupon(MOCK_BXGY_COUPON_DATA, _id="bxgy_id")


MOCK_CART_WISE_COUPON_THRESHOLD = {
    "coupon_code": "CART100OFF10",
    "description": "10% off cart total over 100",
    "type": CouponType.CART_WISE,
    "status": CouponStatus.ACTIVE,
    "metadata": {MetadataKeys.MIN_CART_TOTAL: 100.0, MetadataKeys.DISCOUNT_PERCENTAGE: 10},
}

MOCK_PRODUCT_WISE_COUPON_PRODA = {
    "coupon_code": "PRODA20OFF",
    "description": "20% off Product A",
    "type": CouponType.PRODUCT_WISE,
    "status": CouponStatus.ACTIVE,
    "metadata": {MetadataKeys.PRODUCT_ID: "prod_A", MetadataKeys.DISCOUNT_PERCENTAGE: 20},
}

MOCK_BXGY_COUPON = {
    "coupon_code": "BUYBGETC",
    "description": "Buy Product B get Product C free",
    "type": CouponType.BXGY,
    "status": CouponStatus.ACTIVE,
    "metadata": {
        MetadataKeys.BUY_PRODUCTS: [{"product_id": "prod_B", "quantity": 1}],
        "get_products": [{"product_id": "prod_C", "quantity": 1}],
        MetadataKeys.FIXED_DISCOUNT_AMOUNT: 5.0,  # Simplified for testing
    },
}
