"""
Custom error definitions for the Coupon Service.
"""
from flask import jsonify
from coupon_service.utils.constants import ResponseKeys, HttpStatusCodes


def handle_exception(e: Exception):
    """
    Common error handler for all API exceptions.
    Returns a tuple of (response_json, status_code).
    """
    if isinstance(e, CouponNotFound):
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.NOT_FOUND

    if isinstance(e, (CouponInactive, CouponLimitReachedError)):
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.FORBIDDEN

    if isinstance(e, CouponAlreadyExists):
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.CONFLICT

    if isinstance(e, ValueError):
        return jsonify({ResponseKeys.ERROR: str(e)}), HttpStatusCodes.BAD_REQUEST

    # Fallback for any other exceptions
    return jsonify({ResponseKeys.ERROR: str(e)}), HttpStatusCodes.INTERNAL_SERVER_ERROR


class CouponServiceError(Exception):
    """Base exception for Coupon Service errors."""

    def __init__(self, message="An unexpected error occurred in the Coupon Service."):
        self.message = message
        super().__init__(self.message)


class CouponNotFound(CouponServiceError):
    """Raised when a requested coupon is not found."""

    def __init__(self, coupon_code: str):
        self.message = f"Coupon with code '{coupon_code}' not found."
        super().__init__(self.message)


class CouponInactive(CouponServiceError):
    """Raised when a coupon is inactive but was requested."""

    def __init__(self, identifier: str):
        self.message = f"Coupon with ID/Code '{identifier}' is currently inactive."
        super().__init__(self.message)


class CouponAlreadyExists(CouponServiceError):
    """Raised when trying to create a coupon with an existing code."""

    def __init__(self, coupon_code: str):
        self.message = f"Coupon with code '{coupon_code}' already exists."
        super().__init__(self.message)


class CouponLimitReachedError(CouponServiceError):
    """Raised when a coupon's repetition limit is 0 or has been met."""

    def __init__(self, coupon_code: str):
        self.message = f"You have reached the limit for coupon '{coupon_code}'."
        super().__init__(self.message)


class InvalidCouponType(CouponServiceError):
    """Raised when an invalid coupon type is provided."""

    def __init__(self, coupon_type: str):
        self.message = f"Invalid coupon type: '{coupon_type}'."
        super().__init__(self.message)


class CouponNotApplicable(CouponServiceError):
    """Raised when a coupon cannot be applied due to unmet conditions."""

    def __init__(self, coupon_code: str, reason: str = "conditions not met"):
        self.message = f"Coupon '{coupon_code}' is not applicable: {reason}."
        super().__init__(self.message)


class CouponExpired(CouponServiceError):
    """Raised when a coupon is expired."""

    def __init__(self, coupon_code: str):
        self.message = f"Coupon '{coupon_code}' has expired."
        super().__init__(self.message)


class CouponUsageLimitReached(CouponServiceError):
    """Raised when a coupon's usage limit has been reached."""

    def __init__(self, coupon_code: str):
        self.message = f"Coupon '{coupon_code}' usage limit reached."
        super().__init__(self.message)


class InvalidSchemaArguments(CouponServiceError):
    """Raised when schema validation fails with general invalid arguments."""

    def __init__(self, errors: dict, message="Invalid arguments provided."):
        self.errors = errors
        self.message = message
        super().__init__(self.message)


class MissingRequiredFieldError(InvalidSchemaArguments):
    """Raised when a required field is missing during schema validation."""

    def __init__(self, fields: list, message="Missing required fields."):
        self.fields = fields
        self.message = f"{message}: {', '.join(fields)}"
        super().__init__({field: ["Missing data for required field."] for field in fields}, self.message)


class TypeMissMatchError(InvalidSchemaArguments):
    """Raised when a field has a type mismatch during schema validation."""

    def __init__(self, fields: dict, message="Type mismatch for fields."):
        self.fields = fields
        self.message = f"{message}: {', '.join(fields.keys())}"
        super().__init__(fields, self.message)
