# Coupon Management API for E-commerce

This document outlines the design and thought process for building a RESTful API to manage and apply discount coupons
for an e-commerce platform, as per the "Software Developer (Backend) Task for Monk Commerce 2025".

The primary focus of this document is to explore the variety of use cases, edge cases, and the overall system design.

## 1. Project Overview & High-Level Design

The goal is to create a flexible and extensible REST API for handling different types of coupons, following the standards of ecosystem. The system will be designed as a microservice that can be integrated into a larger e-commerce platform.

The architecture will be centered around a **Flask** application. Flask is a lightweight and flexible Python web framework, which aligns with the existing microservices in the project. Request and response data will be strictly validated using schema validation libraries.

The entire service will be containerized using **Docker**. A `docker-compose.yml` file will be used to orchestrate the application container along with **MongoDB** and **Redis** containers, ensuring a consistent development and testing environment.

## 2. Tech Stack

- **Backend Framework:** Flask
- **Schema Validation:** Marshmallow (for request/response validation)
- **Database:** MongoDB
- **Containerization:** Docker & Docker Compose
- **Testing:** Unittest (with a dedicated test MongoDB database)

## 3. API Endpoints

The following RESTful endpoints are provided:

### Coupon Management

- `POST /api/v1/coupons`: Create a new coupon.
- `GET /api/v1/coupons`: Retrieve a list of all coupons.
- `GET /api/v1/coupons/{id}`: Retrieve a specific coupon by its ID.
- `PUT /api/v1/coupons/{coupon_code}`: Update an existing coupon by its code.
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
    // Coupon-specific details and conditions
  },
  "status": "string ('active' or 'inactive')",
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
  { "product_id": "prod_123", "discount_amount": 5.00 }
  ```
- **BxGy:**
  ```json
  {
    "buy_products": [{"product_id": "prod_A", "quantity": 2}],
    "get_products": [{"product_id": "prod_B", "quantity": 1}],
    "repetition_limit": 3
  }
  ```

## 5. Considered Use Cases & Edge Cases

This is the core of the task, exploring the complexity of a real-world coupon system.

### Cart-wise Coupons

- **Implemented:**
    - A percentage discount is applied if the cart total is above a certain threshold.
- **Unimplemented / To Consider:**
    - **Fixed amount discount** (e.g., $10 off on orders over $100).
    - **Tiered discounts** (e.g., 10% off for >$100, 15% off for >$200).
    - **Excluding specific products** from the cart total calculation.
    - **Stacking:** Can this coupon be used with other coupons? (e.g., a cart-wise discount on top of a product-wise
      discount).

### Product-wise Coupons

- **Implemented:**
    - A fixed or percentage discount on a single product.
- **Unimplemented / To Consider:**
    - **Discount on a list of products**.
    - **Discount on a product category** (e.g., 15% off all "footwear"). This would require product-category
      relationships.
    - **Interaction with other discounts:** If a product is eligible for multiple discounts, which one applies? The best
      one? Or do they stack?

### BxGy (Buy X, Get Y) Coupons

- **Implemented:**
    - A simple "Buy X of product A, Get Y of product B" logic.
- **Unimplemented / To Consider:**
    - **"Buy from a set of products, get from another set"**: e.g., "Buy any 2 T-shirts, get 1 pair of socks free".
    - **Cheapest item free**: In a "Buy 2, Get 1 Free" scenario for the same product, the discount is the price of one
      item.
    - **Partial fulfillment**: What if the user has "buy" items but not "get" items in the cart? The coupon is not
      applicable. What if they have more "get" items than the coupon allows? Only the specified number of items should
      be discounted.
    - **Repetition limit**: If a BxGy coupon has a repetition limit of 2, and the user's cart qualifies for it 3 times,
      it should only be applied twice.

### General/Bonus Cases (Future Implementations)

- **Coupon Expiration**: Coupons will have an optional `expires_at` date to enforce time-based validity.
- **Usage Limits**: A coupon can be limited to a total number of uses (e.g., "for the first 100 customers").
- **Redis Caching**: Caching of coupon definitions and application results to optimize performance.
- **User-specific coupons**: Coupons that are tied to a user ID.
- **Region-specific coupons**: Coupons that are only valid in certain countries or regions.

## 6. Assumptions

- All monetary values are in a single, consistent currency.
- Product information (like price and ID) is provided by the e-commerce platform via the cart object.
- The API is stateless.

## 7. Limitations of Initial Implementation

- The initial implementation does not include Redis caching.
- Enforcing `expires_at` and `usage_limit` is not yet implemented.
- The initial implementation covers the core "happy path" for each coupon type.
- The system follows the microservice architecture.

## 8. Future Enhancements

- **Redis Integration:** Implement caching and atomic usage counters.
- **Advanced Stacking Rules:** Develop a rule engine for combining multiple coupons.
- **Admin UI:** A simple web interface for managing coupons.
- **Analytics:** Track coupon usage to provide insights.
- **Asynchronous Tasks:** Use a task queue for background operations.
- **Authentication & Authorization:** Secure the coupon management endpoints.

## How to Run the Application

To get the coupon service up and running using Docker Compose:

1.  **Navigate to the service directory:**
    ```bash
    cd assessment/coupon_service
    ```
2.  **Build and start the containers:** This command will build the Docker image for the Flask application and start all services (Flask app, MongoDB, Redis) in detached mode.
    ```bash
    docker-compose up --build -d
    ```
3.  **Verify service status (Optional):** To check if the containers are running:
    ```bash
    docker-compose ps
    ```
4.  **Access the API:** The Flask application will be accessible at `http://localhost:5000`. You can test the health endpoint:
    ```bash
    curl http://localhost:5000/health
    ```
5.  **Stop the services:** To stop and remove the containers:
    ```bash
    docker-compose down
    ```
