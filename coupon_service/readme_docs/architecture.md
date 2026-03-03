# Coupon Service Architecture (Kissflow Compliant)

This document outlines the redesigned architecture for the coupon service, aligning with the established conventions and directory structure observed in the existing Kissflow `accounts` service. This ensures consistency, maintainability, and better integration within the larger project ecosystem.

---

## 1. High-Level Overview

The coupon service is a Flask-based microservice, containerized with Docker, utilizing MongoDB for persistent storage. The architecture emphasizes a clear separation of concerns, with distinct modules for routing, business logic, data access, schema validation, and utilities. Redis integration for caching is planned for future versions.

## 2. Project Structure

The `coupon_service` directory follows this structure:

```
coupon_service/
├── __init__.py               # Package initializer
├── main.py                   # Flask app entry point, configuration, blueprint registration
├── route/                    # Contains Flask Blueprints and API endpoint definitions
│   ├── __init__.py
│   └── coupon_routes.py      # All coupon-related API endpoints
├── services/                 # Core business logic layer
│   ├── __init__.py
│   └── coupon_service.py     # CouponService class (implements business rules)
│   └── strategy_factory.py   # Strategy pattern implementation for different coupon types
├── server/                   # Custom ODM / Data Access Layer
│   ├── __init__.py
│   └── coupon_server.py      # CouponServer class (handles pymongo interactions)
├── schema/                   # Marshmallow schemas for request/response validation
│   ├── __init__.py
│   └── coupon_schema.py      # All coupon-related Marshmallow schemas
├── utils/                    # Common utilities, constants, custom errors
│   ├── __init__.py
│   ├── constants.py          # Application-specific constants
│   ├── id_generator.py       # Snowflake-like ID generation
│   └── errors.py             # Custom error definitions
├── models.py                 # Internal Python dataclasses (e.g., Coupon)
├── tests/                    # Unit and integration tests
├── Dockerfile                # Docker image definition
└── requirements.txt          # Python dependencies
```

## 3. Component Responsibilities

### 3.1. `main.py`
-   **Purpose:** The central entry point for the Flask application.
-   **Responsibilities:** Initializes the Flask app, loads configuration (from environment variables), sets up database (MongoDB) and cache (Redis) connections, and registers all API blueprints.

### 3.2. `route/`
-   **Purpose:** Defines all API endpoints and handles the HTTP request/response cycle.
-   **Responsibilities:**
    -   Contains Flask `Blueprint` instances.
    -   Parses incoming HTTP requests.
    -   Uses `schema/coupon_schema.py` for payload validation via `@base/util/schema_validation`.
    -   Calls methods in `services/coupon_service.py` to execute business logic.
    -   Formats responses into JSON.
    -   Applies docstring-based access control (`=== rbac: ... ===`).

### 3.3. `services/`
-   **Purpose:** Encapsulates the core business logic of the application.
-   **Responsibilities:**
    -   The `CouponService` class implements all coupon-related business rules (e.g., `is_coupon_applicable`, `calculate_discount`).
    -   It orchestrates interactions with the `server/coupon_server.py` (for data persistence).
    -   It is completely decoupled from the web framework.

### 3.4. `server/`
-   **Purpose:** This is the custom Object-Document Mapper (ODM) or data access layer, mirroring the Kissflow `accounts/server` pattern.
-   **Responsibilities:**
    -   The `CouponServer` class handles all direct interactions with MongoDB using `pymongo`.
    -   It is responsible for mapping raw MongoDB documents to/from our internal `models.py` objects.
    -   It manages the generation of custom Snowflake IDs for `_id` fields.
    -   It provides a clean, object-oriented interface for the `services/coupon_service.py` to perform CRUD operations without knowing `pymongo` specifics.

### 3.5. `schema/`
-   **Purpose:** Defines the data structures and validation rules for API requests and responses using Marshmallow.
-   **Responsibilities:**
    -   Contains `coupon_schema.py` with classes like `CouponCreateSchema`, `CartSchema`, etc.
    -   These schemas are used by the `@base/util/schema_validation` utility in the `route/` layer.

### 3.6. `utils/`
-   **Purpose:** Provides common utilities, constants, and custom error definitions used across the service.
-   **Responsibilities:**
    -   `constants.py`: Stores application-wide constants (e.g., coupon types, status values).
    -   `errors.py`: Defines custom exceptions specific to the coupon service.

### 3.7. `models.py`
-   **Purpose:** Defines the internal Python classes that represent the application's data entities (e.g., `Coupon`).
-   **Responsibilities:** Provides a structured, object-oriented representation of data used within the `services/` and `server/` layers, independent of the database or API schema.

---

## 4. Data Storage & Caching

-   **MongoDB:** Used for persistent storage of coupon definitions. The `server/coupon_server.py` handles all interactions.
-   **Redis (Planned):** Redis will be integrated in future versions for caching frequently accessed data and for atomic operations (e.g., managing coupon usage counts).

This redesigned architecture ensures full compliance with the Kissflow project's established patterns.