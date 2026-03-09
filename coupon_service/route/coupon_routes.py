from flask import Blueprint, jsonify, request
from coupon_service.utils.errors import (
    CouponNotFound,
    CouponAlreadyExists,
    CouponInactive
)
from coupon_service.services.coupon_service import CouponService
from coupon_service.schema.coupon_schema import (
    CouponCreateSchema,
    CouponUpdateSchema,
    CouponResponseSchema,
    ApplyCouponRequestSchema,
)
from coupon_service.utils.custom_schema_validation import SchemaValidation
from coupon_service.utils.constants import BlueprintNames, HttpStatusCodes, HttpMethods, ResponseKeys

# Create a Blueprint for the coupon API
coupon_api_blueprint = Blueprint(BlueprintNames.COUPON_API, __name__)


@coupon_api_blueprint.route("/coupons", methods=[HttpMethods.POST])
def create_coupon():
    """
    Endpoint to create a new coupon.
    """
    params = request.get_json()
    SchemaValidation(CouponCreateSchema()).validate_payload(params)
    try:
        coupon_service = CouponService()
        coupon_service.create_coupon(params)
        return (jsonify({ResponseKeys.MESSAGE: "Coupon has been created."}),
                HttpStatusCodes.CREATED)
    except CouponAlreadyExists as e:
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.CONFLICT


@coupon_api_blueprint.route("/coupons", methods=[HttpMethods.GET])
def get_all_coupons():
    """
    Endpoint to retrieve all ACTIVE coupons.
    """
    coupon_service = CouponService()
    all_coupons = coupon_service.get_all_active_coupons()
    response_schema = CouponResponseSchema()
    return jsonify(response_schema.dump(all_coupons, many=True)), HttpStatusCodes.OK


@coupon_api_blueprint.route("/coupons/<coupon_code>", methods=[HttpMethods.GET])
def get_coupon_by_code(coupon_code):
    """
    Endpoint to retrieve a specific coupon by its code.
    """
    try:
        coupon_service = CouponService()
        coupon = coupon_service.get_coupon_by_code(coupon_code)
        response_schema = CouponResponseSchema()
        return jsonify(response_schema.dump(coupon)), HttpStatusCodes.OK
    except CouponNotFound as e:
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.NOT_FOUND
    except CouponInactive as e:
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.FORBIDDEN


@coupon_api_blueprint.route("/coupons/<coupon_code>", methods=[HttpMethods.PUT])
def update_coupon(coupon_code):
    """
    Endpoint to update a specific coupon by its code.
    """
    params = request.get_json()
    SchemaValidation(CouponUpdateSchema()).validate_payload(params, partial=True)

    try:
        coupon_service = CouponService()
        coupon_service.update_coupon(coupon_code, params)
        return jsonify({ResponseKeys.MESSAGE: "Coupon has been updated."}), HttpStatusCodes.OK
    except CouponNotFound as e:
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.NOT_FOUND
    except CouponInactive as e:
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.FORBIDDEN


@coupon_api_blueprint.route("/coupons/<coupon_code>", methods=[HttpMethods.DELETE])
def delete_coupon(coupon_code):
    """
    Endpoint to delete a specific coupon by its code.
    """
    try:
        coupon_service = CouponService()
        coupon_service.delete_coupon(coupon_code)
        return (
            jsonify({ResponseKeys.MESSAGE: f"Coupon with code {coupon_code} has been deleted."}),
            HttpStatusCodes.OK,
        )
    except CouponNotFound as e:
        return jsonify({ResponseKeys.ERROR: e.message}), HttpStatusCodes.NOT_FOUND


@coupon_api_blueprint.route("/applicable-coupons", methods=[HttpMethods.POST])
def get_applicable_coupons():
    """
    Endpoint to find all coupons applicable to a given cart.
    """
    params = request.get_json()
    SchemaValidation(ApplyCouponRequestSchema()).validate_payload(params)

    try:
        coupon_service = CouponService()
        applicable_coupons = coupon_service.get_applicable_coupons(params["cart"])
        return jsonify({ResponseKeys.APPLICABLE_COUPONS: applicable_coupons}), HttpStatusCodes.OK
    except Exception as e:
        return jsonify({ResponseKeys.ERROR: str(e)}), HttpStatusCodes.INTERNAL_SERVER_ERROR


@coupon_api_blueprint.route("/apply-coupon/<coupon_code>", methods=[HttpMethods.POST])
def apply_coupon(coupon_code):
    """
    Endpoint to apply a specific coupon (by code) to a given cart.
    """
    params = request.get_json()
    SchemaValidation(ApplyCouponRequestSchema()).validate_payload(params)

    try:
        coupon_service = CouponService()
        updated_cart_response = coupon_service.apply_coupon_to_cart(
            coupon_code=coupon_code,
            cart=params["cart"],
        )
        return jsonify(updated_cart_response), HttpStatusCodes.OK
    except (CouponNotFound, CouponInactive) as e:
        status_code = HttpStatusCodes.NOT_FOUND if isinstance(e, CouponNotFound) else HttpStatusCodes.FORBIDDEN
        return jsonify({ResponseKeys.ERROR: e.message}), status_code
    except ValueError as e:
        return jsonify({ResponseKeys.ERROR: str(e)}), HttpStatusCodes.BAD_REQUEST
    except Exception as e:
        return jsonify({ResponseKeys.ERROR: str(e)}), HttpStatusCodes.INTERNAL_SERVER_ERROR
