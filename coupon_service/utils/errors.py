"""
Custom error definitions for the Coupon Service.
"""


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


class CouponAlreadyExists(CouponServiceError):
    """Raised when trying to create a coupon with an existing code."""

    def __init__(self, coupon_code: str):
        self.message = f"Coupon with code '{coupon_code}' already exists."
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
