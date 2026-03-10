# Coupon Management API for E-commerce

This document outlines the design and thought process for building a RESTful API to manage and apply discount coupons
for an e-commerce platform, as per the "Software Developer (Backend) Task for Monk Commerce 2025".

The primary focus of this document is to explore the variety of use cases, edge cases, and the overall system design.

## 1. Project Overview & High-Level Design

The goal is to create a flexible and extensible REST API for handling different types of coupons, following the standards of ecosystem. The system will be designed as a microservice that can be integrated into a larger e-commerce platform.

The architecture is centered around a **Flask** application using a **Strategy Pattern** for discount calculations, allowing for easy addition of new coupon types in the future.

## 2. Tech Stack

- **Backend Framework:** Flask
- **Schema Validation:** Marshmallow (for request/response validation)
- **Database:** MongoDB
- **Containerization:** Docker & Docker Compose
- **Testing:** Pytest (with a dedicated test MongoDB database)

## 3. API Endpoints

The following RESTful endpoints are provided:

### Coupon Management

- `POST /api/v1/coupons`: Create a new coupon.
- `GET /api/v1/coupons`: Retrieve a list of all coupons.
- `GET /api/v1/coupons/{id}`: Retrieve a specific coupon by its ID.
- `PUT /api/v1/coupons/{id}`: Update an existing coupon by its ID.
- `DELETE /api/v1/coupons/{id}`: Delete a coupon by its ID.

### Coupon Application

- `POST /api/v1/applicable-coupons`: Takes a cart object and returns a list of all coupons that can be applied, along with the calculated discount for each.
- `POST /api/v1/apply-coupon/{id}`: Applies a specific coupon to a cart and returns the updated cart with the discount applied.

## 4. Database Schema

The database uses a flexible schema to support different coupon types. A single `coupons` collection stores all coupon data.

**Coupon Model:**

```json
{
  "_id": "string (Short ID)",
  "coupon_code": "string",
  "type": "string (e.g., 'cart-wise', 'product-wise', 'bxgy')",
  "description": "string",
  "metadata": {
  },
  "status": "string ('active' or 'inactive')",
  "expires_at": "datetime (ISO)",
  "_created_at": "datetime",
  "_modified_at": "datetime",
  "_created_by": "string",
  "_modified_by": "string"
}
```

**`metadata` examples:**

- **Cart-wise:**
  ```json
  { "min_cart_total": 100.00, "discount_percentage": 10 }
  ```
- **Product-wise:**
  ```json
  { "product_id": "prod_123", "discount_percentage": 10.00 }
  ```
- **BxGy (Standard Pool Logic):**
  ```json
  {
    "buy_products": [{"product_id": "prod_A"}, {"product_id": "prod_B"}],
    "buy_quantity": 3,
    "get_products": [{"product_id": "prod_C"}],
    "get_quantity": 1,
    "repetition_limit": 2
  }
  ```
- **BxGy (PDF Task Format):**
  ```json
  {
    "buy_products": [{"product_id": "prod_A", "quantity": 3}],
    "get_products": [{"product_id": "prod_C", "quantity": 1}],
    "repetition_limit": 2
  }
  ```

## 5. Advanced BxGy Logic (Implemented)

The system implements a sophisticated **Pool-Based BxGy Strategy**:

- **Pool Summation:** Sums quantities of all items in the cart belonging to the "Buy" list.
- **Repetition Logic:** Calculates repetitions using floor division and caps it via `repetition_limit`.
- **Cheapest First:** Eligible "Get" items are sorted by price ascending, and the cheapest ones are discounted first.
- **Flexible Metadata:** Supports both top-level quantities (`buy_quantity`) and per-product quantities inside the list (matching the PDF task examples).

## 6. Item-Level Discount Breakdown (Implemented)

The `apply-coupon` response provides a detailed breakdown of discounts at the item level for full transparency.

## 7. Considered Use Cases & Edge Cases

### Cart-wise Coupons
- **Implemented:** Percentage discount applied if the cart total is above a certain threshold.
- **Proportional Distribution:** The discount is spread across all items in the response breakdown.

### Product-wise Coupons
- **Implemented:** Fixed or percentage discount on a single product.
- **Interaction:** Handles multiple quantities of the target product.

### BxGy (Buy X, Get Y) Coupons
- **Implemented:** "Buy from a set, get from another set" logic.
- **Repetition limit:** Limits how many times the deal applies per order.
- **PDF Compatibility:** Implementation updated to handle the metadata structure provided in the Monk Commerce task PDF.

### Coupon Expiration (Implemented)
- **Implemented:** Optional `expires_at` date enforcement. Expired coupons are automatically filtered out from applicable coupons and rejected during application.

## 8. Future Implementations

- **Usage Limits**: Total usage count limits (e.g., first 100 customers).
- **Redis Caching**: Performance optimization for coupon lookups and atomic counters.

## 9. Assumptions

- All monetary values are in a single, consistent currency.
- Product information (price/ID) is provided by the cart object.
- The API is stateless.

## How to Run the Application

1.  **Navigate to the service directory:** `cd coupon_service`
2.  **Build and start:** `docker-compose up --build -d`
3.  **Run Tests:** `export PYTHONPATH=$PYTHONPATH:$(pwd) && python3 -m pytest tests/test_service/test_coupon_service.py`
