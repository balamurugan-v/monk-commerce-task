import logging
from marshmallow import Schema
from coupon_service.utils.errors import InvalidSchemaArguments, MissingRequiredFieldError, TypeMissMatchError


class SchemaValidationErrors:
    # These are the literal error messages from Marshmallow that the user's code expects to key on.
    MISSING_REQUIRED_FIELD_ERROR = "Missing data for required field."
    # This is a partial key, the user's code will do a `contains` check.
    TYPE_MISS_MATCH_ERROR = "Not a valid"


class SchemaValidation:
    def __init__(self, schema: Schema):
        self.schema = schema

    def __generate_validation_error_response(self, error_dict: dict, path: str = "", response: dict = None):
        """
        Get the Marshmallow Validation response as input and formate the data to kissflow error response
        :param error_dict: Validated error response
        :param path: current json path of the response json
        :param response:
        :return:
        """
        if not response:
            response = {}
        for key, value in error_dict.items():
            current_path = f"{path}.{key}" if path else f"{key}"
            if isinstance(value, list):
                for item in value:
                    response.setdefault(item, []).append(current_path)
            elif isinstance(value, dict):
                response = self.__generate_validation_error_response(value, current_path, response)
            else:
                response.setdefault("Invalid", []).append(current_path)
                logging.error(f"Invalid value: {value}, type: {type(value)}, key: {key}")
        return response

    def validate_payload(self, params, partial=None):
        """
        validating the payload based on the given schemas
        :param params: request payload
        :param partial:  Whether to ignore missing fields and not require
        return:
        """
        _response = self.schema.validate(params, partial=partial)
        if not _response:
            return
        error_response = self.__generate_validation_error_response(_response, "", {})
        errors = {
            SchemaValidationErrors.MISSING_REQUIRED_FIELD_ERROR: MissingRequiredFieldError(
                error_response.get(SchemaValidationErrors.MISSING_REQUIRED_FIELD_ERROR)
            ),
            SchemaValidationErrors.TYPE_MISS_MATCH_ERROR: TypeMissMatchError(
                error_response.get(SchemaValidationErrors.TYPE_MISS_MATCH_ERROR)
            ),
        }

        if len(error_response) == 1:
            for key in error_response:
                if key in errors:
                    raise errors[key]

        raise InvalidSchemaArguments(error_response)

    def load(self, params, partial=None):
        self.validate_payload(params, partial=partial)
        return self.schema.load(params, partial=partial)
