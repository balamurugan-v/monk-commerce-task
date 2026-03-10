from marshmallow import Schema, fields, validate, INCLUDE
from coupon_service.utils.constants import CouponType, CouponStatus


# --- Base Schemas ---


class CouponMetadataSchema(Schema):
    """
    A generic metadata schema. Specific coupon types will have their own
    metadata structures, so we allow unknown fields for flexibility.
    """

    class Meta:
        unknown = INCLUDE  # Allow unknown fields for flexibility


class CartItemSchema(Schema):
    """Schema for a single item within a shopping cart."""

    product_id = fields.Str(required=True)
    quantity = fields.Int(required=True, validate=validate.Range(min=1))
    price = fields.Float(required=True, validate=validate.Range(min=0))


class CartSchema(Schema):
    """Schema for the entire shopping cart."""

    items = fields.List(fields.Nested(CartItemSchema), required=True)


# --- API Payload Schemas ---


class CouponCreateSchema(Schema):
    """Schema for validating the payload when creating a new coupon."""

    coupon_code = fields.Str(required=True, validate=validate.Length(min=1))
    description = fields.Str(required=True, validate=validate.Length(min=1))
    type = fields.Str(
        required=True, validate=validate.OneOf([CouponType.CART_WISE, CouponType.PRODUCT_WISE, CouponType.BXGY])
    )
    status = fields.Str(
        required=False,
        load_default=CouponStatus.ACTIVE,
        validate=validate.OneOf([CouponStatus.ACTIVE, CouponStatus.INACTIVE]),
    )
    metadata = fields.Nested(CouponMetadataSchema, required=True)
    expires_at = fields.DateTime(required=False, format='iso')
    # usage_limit is future enhancement, so not required for now
    # usage_limit = fields.Int(required=False, validate=validate.Range(min=1))


class CouponUpdateSchema(Schema):
    """Schema for validating the payload when updating an existing coupon."""

    # All fields are optional for update, but at least one must be provided
    description = fields.Str(required=False, validate=validate.Length(min=1))
    type = fields.Str(
        required=False, validate=validate.OneOf([CouponType.CART_WISE, CouponType.PRODUCT_WISE, CouponType.BXGY])
    )
    status = fields.Str(
        required=False, validate=validate.OneOf([CouponStatus.ACTIVE, CouponStatus.INACTIVE, CouponStatus.ARCHIVED])
    )
    metadata = fields.Nested(CouponMetadataSchema, required=False)
    expires_at = fields.DateTime(required=False, format='iso')
    # usage_limit = fields.Int(required=False, validate=validate.Range(min=1))


class CouponResponseSchema(Schema):
    """Schema for serializing a Coupon object for API responses."""

    coupon_code = fields.Str(required=True)
    description = fields.Str(required=True)
    type = fields.Str(required=True)
    status = fields.Str(required=True)
    metadata = fields.Dict(required=True)
    expires_at = fields.DateTime(required=False, format='iso')


class ApplyCouponRequestSchema(Schema):
    """Schema for validating the payload for the apply and applicable endpoints."""

    cart = fields.Nested(CartSchema, required=True)
    # coupon_code is passed in the URL for apply, but can be in body for applicable
    coupon_code = fields.Str(required=False)  # Optional for /applicable-coupons
