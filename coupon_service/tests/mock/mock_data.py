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
        MetadataKeys.BUY_PRODUCTS: [{"product_id": "prod_Y"}],
        MetadataKeys.BUY_QUANTITY: 2,
        MetadataKeys.GET_PRODUCTS: [{"product_id": "prod_Z"}],
        MetadataKeys.GET_QUANTITY: 1,
        MetadataKeys.REPETITION_LIMIT: 1,
    },
}

# --- Mock Cart Data ---

MOCK_CART_DATA = {
    "items": [
        {"product_id": "prod_A", "quantity": 1, "price": 50.00},
        {"product_id": "prod_B", "quantity": 2, "price": 25.00},
    ]
}

# --- Mock Coupon Objects ---
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
        MetadataKeys.BUY_PRODUCTS: [{"product_id": "prod_B"}],
        MetadataKeys.BUY_QUANTITY: 1,
        MetadataKeys.GET_PRODUCTS: [{"product_id": "prod_C"}],
        MetadataKeys.GET_QUANTITY: 1,
        MetadataKeys.REPETITION_LIMIT: 2,
    },
}
