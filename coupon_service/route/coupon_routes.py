from flask import Blueprint, jsonify, request
from coupon_service.utils.errors import (
    CouponNotFound,
    CouponAlreadyExists,
)
from coupon_service.services.coupon_service import CouponService
from coupon_service.schema.coupon_schema import (
    CouponCreateSchema,
    CouponUpdateSchema,
    CouponResponseSchema,
    ApplyCouponRequestSchema,
)
from coupon_service.utils.custom_schema_validation import SchemaValidation
from coupon_service.utils.constants import BlueprintNames

# Create a Blueprint for the coupon API
coupon_api_blueprint = Blueprint(BlueprintNames.COUPON_API, __name__)


@coupon_api_blueprint.route("/coupons", methods=["POST"])
def create_coupon():
    """
    Endpoint to create a new coupon.
    ===
        rbac:
            UserType: Admin
    ===
    """
    params = request.get_json()
    SchemaValidation(CouponCreateSchema()).validate_payload(params)
    try:
        coupon_service = CouponService()
        # The service expects a dictionary, which it gets from params
        coupon_service.create_coupon(params)
        return jsonify({"message": "Coupon has been created."}), 201
    except CouponAlreadyExists as e:
        return jsonify({"error": e.message}), 409


@coupon_api_blueprint.route("/coupons", methods=["GET"])
def get_all_coupons():
    """
    Endpoint to retrieve all coupons.
    ===
        rbac:
            UserType: Admin
            UserType: User
    ===
    """
    coupon_service = CouponService()
    all_coupons = coupon_service.get_all_coupons()
    # Per user instruction, instantiate schemas locally
    response_schema = CouponResponseSchema()
    return jsonify(response_schema.dump(all_coupons, many=True)), 200


@coupon_api_blueprint.route("/coupons/<_id>", methods=["GET"])
def get_coupon_by_id(_id):
    """
    Endpoint to retrieve a specific coupon by its internal _id.
    ===
        rbac:
            UserType: Admin
            UserType: User
    ===
    """
    try:
        coupon_service = CouponService()
        coupon = coupon_service.get_coupon_by_id(_id)
        response_schema = CouponResponseSchema()
        return jsonify(response_schema.dump(coupon)), 200
    except CouponNotFound as e:
        return jsonify({"error": e.message}), 404


@coupon_api_blueprint.route("/coupons/<coupon_code>", methods=["PUT"])
def update_coupon(coupon_code):
    """
    Endpoint to update a specific coupon by its user-facing code.
    ===
        rbac:
            UserType: Admin
    ===
    """
    params = request.get_json()
    SchemaValidation(CouponUpdateSchema()).validate_payload(params, partial=True)

    try:
        coupon_service = CouponService()
        coupon_service.update_coupon(coupon_code, params)
        return jsonify({"message": "Coupon has been updated."}), 200
    except CouponNotFound as e:
        return jsonify({"error": e.message}), 404


@coupon_api_blueprint.route("/coupons/<_id>", methods=["DELETE"])
def delete_coupon(_id):
    """
    Endpoint to delete a specific coupon by its internal _id.
    ===
        rbac:
            UserType: Admin
    ===
    """
    try:
        coupon_service = CouponService()
        coupon_service.delete_coupon(_id)
        return (
            jsonify({"message": f"Coupon with ID {_id} has been deleted."}),
            200,
        )
    except CouponNotFound as e:
        return jsonify({"error": e.message}), 404


@coupon_api_blueprint.route("/applicable-coupons", methods=["POST"])
def get_applicable_coupons():
    """
    Endpoint to find all coupons applicable to a given cart.
    ===
        public: true
    ===
    """
    params = request.get_json()
    SchemaValidation(ApplyCouponRequestSchema()).validate_payload(params)  # Validate the cart structure

    try:
        coupon_service = CouponService()
        applicable_coupons = coupon_service.get_applicable_coupons(params["cart"])  # Pass the nested cart
        return jsonify(applicable_coupons), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@coupon_api_blueprint.route("/apply-coupon/<coupon_id>", methods=["POST"])
def apply_coupon(coupon_id):
    """
    Endpoint to apply a specific coupon to a given cart.
    ===
        public: true
    ===
    """
    params = request.get_json()
    SchemaValidation(ApplyCouponRequestSchema()).validate_payload(params)

    try:
        coupon_service = CouponService()
        updated_cart = coupon_service.apply_coupon_to_cart(
            coupon_id=coupon_id,
            cart=params["cart"],  # Assuming the cart is nested under a 'cart' key in the request body
        )
        return jsonify(updated_cart), 200
    except CouponNotFound as e:
        return jsonify({"error": e.message}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400  # Bad request for invalid applicability
    except Exception as e:
        return jsonify({"error": str(e)}), 500
