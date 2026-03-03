# Coupon Logic, Cases, and Error States

This document details the various logical cases, conditions, and positive/negative paths for each coupon type as part of the planning phase.

---

## 1. Cart-Wise Coupons

These coupons apply a discount to the entire cart, typically based on the total value.

### Scenario 1.1: Minimum Purchase Threshold
- **Description:** A discount is applied only if the total value of the cart meets or exceeds a certain amount.
- **Condition:** `cart.total >= threshold_amount`
- **Positive Cases:**
    - A user's cart total is **greater than** the threshold.
        - **Example:** Threshold is $100, cart total is $120.
        - **Result:** The coupon discount is successfully applied.
    - A user's cart total is **exactly equal to** the threshold.
        - **Example:** Threshold is $100, cart total is $100.
        - **Result:** The coupon discount is successfully applied.
- **Negative Cases:**
    - A user's cart total is **less than** the threshold.
        - **Example:** Threshold is $100, cart total is $90.
        - **Error Message:** "Cart total does not meet the minimum requirement of $100."
    - The user's cart is empty.
        - **Example:** Cart total is $0.
        - **Error Message:** "Cannot apply coupon to an empty cart."

### Scenario 1.2: Excluding Specific Items from Threshold Calculation
- **Description:** Certain items (e.g., gift cards, non-discountable items) do not contribute to the total required to meet the threshold.
- **Condition:** `(cart.total - excluded_items.total) >= threshold_amount`
- **Positive Cases:**
    - The adjusted cart total (after excluding specified items) is still over the threshold.
        - **Example:** Threshold $100. Cart has $120 of normal items and a $20 gift card. Adjusted total is $120.
        - **Result:** Discount is applied (typically only to the non-excluded items).
- **Negative Cases:**
    - The adjusted cart total falls below the threshold.
        - **Example:** Threshold $100. Cart has $90 of normal items and a $20 gift card. Adjusted total is $90.
        - **Error Message:** "Eligible cart total does not meet the minimum requirement of $100."

---

## 2. Product-Wise Coupons

These coupons apply a discount to one or more specific items in the cart.

### Scenario 2.1: Discount on a Single, Specific Product
- **Description:** A discount is applied to a specific product (e.g., "10% off Product A").
- **Condition:** `product_id` is present in `cart.items`.
- **Positive Cases:**
    - The specified product is in the cart (quantity 1).
        - **Result:** The discount is applied to that single item.
    - The specified product is in the cart with a quantity greater than one.
        - **Result:** The discount is applied to *every unit* of that item.
- **Negative Cases:**
    - The specified product is not in the.
        - **Error Message:** "This coupon is only valid for [Product Name], which is not in your cart."

### Scenario 2.2: Discount on Any Product from a List
- **Description:** A discount applies to any product from a predefined list (e.g., "20% off any of these 5 products").
- **Condition:** At least one `product_id` from a given list is present in `cart.items`.
- **Positive Cases:**
    - The cart contains one of the eligible products.
        - **Result:** The discount is applied to that product.
    - The cart contains multiple different products from the eligible list.
        - **Result:** The discount is applied to all applicable products in the cart.
- **Negative Cases:**
    - The cart contains no products from the eligible list.
        - **Error Message:** "This coupon requires at least one eligible product in the cart."

---

## 3. BxGy (Buy X, Get Y) Coupons

These complex coupons involve "Buy-Get" logic (e.g., "Buy One, Get One Free").

### Scenario 3.1: Buy X of Product A, Get Y of Product B
- **Description:** A user must purchase a certain quantity of one product to get a discount on another.
- **Condition:** `cart.items` must contain at least X units of Product A and Y units of Product B.
- **Positive Cases:**
    - The cart has exactly X units of A and Y units of B.
        - **Result:** Y units of Product B are discounted (e.g., made free).
    - The cart has more than X units of A and more than Y units of B.
        - **Result:** Y units of Product B are still the only ones discounted (unless repetition is allowed).
- **Negative Cases:**
    - The cart has enough of the "buy" item but not enough of the "get" item.
        - **Example:** Buy 2 A, Get 1 B. Cart has 2 A and 0 B.
        - **Error Message:** "Add an eligible item to your cart to receive your discount."
    - The cart has the "get" item but not enough of the "buy" item.
        - **Example:** Buy 2 A, Get 1 B. Cart has 1 A and 1 B.
        - **Error Message:** "Buy at least [X] of [Product A] to qualify for this offer."

### Scenario 3.2: Repetition Limit
- **Description:** The coupon can only be applied a certain number of times in a single transaction.
- **Condition:** The application logic must track how many times the BxGy condition is met and cap it at `repetition_limit`.
- **Positive Cases (Logic Constraint):**
    - A "Buy 2, Get 1 Free" coupon has a repetition limit of 3. The cart contains 6 "buy" items and 3 "get" items.
        - **Result:** The condition is met 3 times. All 3 "get" items are discounted.
    - A "Buy 2, Get 1 Free" coupon has a repetition limit of 3. The cart contains 8 "buy" items and 4 "get" items.
        - **Result:** The condition is met 4 times, but the logic caps the discount at the limit. Only 3 "get" items are discounted. This is not an error, but a correctly handled limitation.

### Scenario 3.3: Buy from a Set, Get from a Set
- **Description:** Buy a total quantity of items from a set of products to get a discount on items from another set.
- **Condition:** `sum(quantity of items from buy_set) >= X` and `sum(quantity of items from get_set) >= Y`.
- **Positive Cases:**
    - "Buy any 2 T-shirts, get 1 pair of socks free". Cart has 1 "Blue T-shirt", 1 "Red T-shirt", and 1 "White Socks".
        - **Result:** The "White Socks" are discounted.
- **Negative Cases:**
    - The cart does not have enough total items from the "buy" set.
        - **Error Message:** "Add more eligible items to your cart to qualify for this offer."
- **Assumption/Rule:** When the "get" set contains multiple items of different prices, the discount is applied to the **cheapest** eligible item(s) in the cart first.

---

## 4. General Errors & Global Conditions

These conditions and errors can apply to any coupon type.

- ### Invalid Coupon
    - **Description:** A user tries to apply a coupon code or ID that does not exist in the database.
    - **Condition:** `coupon_id` not found.
    - **Error (HTTP 404 Not Found):** "Coupon not found."

- ### Expired Coupon (Future Implementation)
    - **Description:** The coupon is used after its expiration date.
    - **Condition:** `current_date > coupon.expires_at`.
    - **Error (HTTP 400 Bad Request):** "This coupon has expired."

- ### Usage Limit Reached (Future Implementation)
    - **Description:** The coupon has a global redemption limit which has already been met.
    - **Condition:** `coupon.usage_count >= coupon.usage_limit`.
    - **Error (HTTP 400 Bad Request):** "This coupon is no longer valid."

- ### Coupon Stacking (when disallowed)
    - **Description:** A user tries to apply a coupon when a discount is already active on the cart or an item.
    - **Condition:** `cart.has_active_discount == true`.
    - **Error (HTTP 400 Bad Request):** "Another discount is already active. Multiple coupons cannot be used together."

- ### Invalid Input / Schema Validation
    - **Description:** The request payload is validated against a Marshmallow schema using the custom `SchemaValidation` utility found in `@base/util/schema_validation`. This utility will raise specific, structured errors.
    - **Condition:** The `validate_payload` method of the `SchemaValidation` class finds discrepancies between the payload and the schema.
    - **Negative Cases & Errors:**
        - **Missing Mandatory Fields:** One or more required fields are missing from the payload.
            - **Example:** `POST /coupons` is missing the `type` field.
            - **Error Raised:** `MissingRequiredFieldError`.
            - **Example JSON Response (HTTP 400/422):**
              ```json
              {
                "error_code": "MISSING_REQUIRED_FIELD",
                "message": "The following fields are required: type"
              }
              ```
        - **Incorrect Data Type:** A field is sent with a data type that does not match the schema's expectation.
            - **Example:** The `min_cart_total` is sent as a string (`"100"`) instead of a number (`100`).
            - **Error Raised:** `TypeMissMatchError`.
            - **Example JSON Response (HTTP 400/422):**
              ```json
              {
                "error_code": "TYPE_MISMATCH",
                "message": "The following fields have a type mismatch: details.min_cart_total"
              }
              ```
        - **Other Invalid Arguments:** The payload has other validation issues (e.g., invalid value for a field with choices).
            - **Example:** The `type` field is `super-discount`, which is not a valid enum choice.
            - **Error Raised:** `InvalidSchemaArguments`.
            - **Example JSON Response (HTTP 400/422):**
              ```json
              {
                "error_code": "INVALID_ARGUMENTS",
                "message": "Invalid arguments provided",
                "details": {
                  "Unknown field": ["type"]
                }
              }
              ```

---

## 5. Implementation Scope

This section explicitly defines the features that will be implemented in the initial version versus those deferred for future development.

### General Features
- **Covered Now:**
    - Core API endpoints: `POST /coupons`, `GET /coupons`, `POST /applicable-coupons`, `POST /apply-coupon`.
    - Schema validation for all incoming requests.
    - Dockerized environment for the Flask app, MongoDB, and Redis.
- **Future Enhancements:**
    - Full CRUD for coupons (`PUT`, `DELETE`, `GET by ID`).
    - Coupon expiration dates (`expires_at`).
    - Global usage limits.
    - Rules for stacking multiple coupons.
    - User-specific coupons.
    - Authentication and authorization for management endpoints.

### Cart-Wise Coupons
- **Covered Now:**
    - A simple percentage discount based on a minimum cart total.
- **Future Enhancements:**
    - Tiered discounts (e.g., 10% off >$100, 15% off >$200).
    - Fixed amount discounts (e.g., $10 off).
    - Excluding specific items from the threshold calculation.

### Product-Wise Coupons
- **Covered Now:**
    - A discount (percentage or fixed amount) on a single, specific product ID.
- **Future Enhancements:**
    - Discounts that apply to a list of multiple products.
    - Discounts based on a product category.

### BxGy (Buy X, Get Y) Coupons
- **Covered Now:**
    - A simple "Buy X of Product A, Get Y of Product B" logic.
    - A basic repetition limit on the coupon.
- **Future Enhancements:**
    - Complex "Buy from a set of products, get from another set" logic.
    - Rules to automatically discount the cheapest item from the "get" set.

