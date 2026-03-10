# Detailed Design Patterns & Class Structure

This document provides a detailed breakdown of the GoF (Gang of Four) design patterns and the specific class structure for the coupon service.

---

## 1. Architectural Patterns

At a high level, we structure the application using:

-   **Service Layer:** Business logic is encapsulated within `services/coupon_service.py`.
- **Repository Pattern (Data Access Layer):** Data persistence logic is handled by `server/coupon_server.py`. (Redis caching is planned for future versions).


## 2. GoF (Gang of Four) Design Patterns

Within this architecture, we leverage specific GoF design patterns to handle complexity and ensure extensibility.

### 2.1. Behavioral: The Strategy Pattern

This is the **primary pattern** for handling different coupon calculation logics. It allows us to define a family of algorithms, put each in its own class, and make them interchangeable.

-   **Problem:** The `CouponService` needs to perform different validation logic based on the coupon's `type` (`cart-wise`, `product-wise`, `bxgy`). A large `if/elif/else` block would be brittle and hard to extend.
-   **Solution:**
    1.  We will define an abstract base class, `CouponValidationStrategy`, with two main methods: `is_applicable(cart, coupon)` and `calculate_discount(cart, coupon)`.
    2.  We will create **concrete strategy classes** for each coupon type (`CartWiseStrategy`, `ProductWiseStrategy`, `BxGyStrategy`) that inherit from the base class and implement these methods with their specific logic.
    3.  The `CouponService` will delegate the validation and calculation tasks to the appropriate strategy object.
-   **Benefit:** To add a new coupon type (e.g., "Free Shipping"), we only need to create a new `FreeShippingStrategy` class. No changes are needed in the `CouponService`, making the system highly extensible and compliant with the Open/Closed Principle.

### 2.2. Creational: The Factory Method Pattern

-   **Problem:** The `CouponService` needs a way to get the correct strategy object for a given coupon without being tightly coupled to the concrete strategy classes.
-   **Solution:** We will create a `StrategyFactory`. It will have a single method, `get_strategy(coupon_type)`, which acts as a factory method. It will contain a simple mapping from a `coupon_type` string to the corresponding strategy class instance.
-   **Benefit:** This decouples the service (the "client") from the creation of the strategies (the "products"). The service doesn't need to know how to instantiate each strategy; it just asks the factory for the one it needs.

### 2.3. Structural: The Server Layer as a Facade (Custom ODM)

-   **Problem:** The `CouponService` needs to interact with the database, but it shouldn't be cluttered with `pymongo` driver code, query syntax, or data-to-object mapping logic.
-   **Solution:** The `CouponServer` class in `server/coupon_server.py` will serve as a **Facade**. It will provide a simple, clean API to the service layer, such as `get_by_code(code)` and `save(coupon)`. Internally, it will handle the complexities of creating database connections, building queries, executing them with `pymongo`, and mapping the results to our `Coupon` model objects. This acts as a custom Object-Document Mapper (ODM).
-   **Benefit:** The service layer is completely ignorant of the database implementation details. The `CouponServer` provides a simplified, business-oriented interface to the data persistence system.

---

## 3. Detailed Class Diagram (Textual Representation)

This diagram shows the inheritance and composition relationships between the key classes.

```
+---------------------------+
| <<Abstract>>              |
| CouponValidationStrategy  |
+---------------------------+
| + is_applicable(cart, coupon): bool |
| + calculate_discount(cart, coupon): float |
+---------------------------+
           ^
           | (Inheritance)
+----------+----------------+----------+
|                                     |
+------------------+   +-------------------+   +--------------+
| CartWiseStrategy |   |ProductWiseStrategy|   | BxGyStrategy |
+------------------+   +-------------------+   +--------------+
| +is_applicable() |   | +is_applicable()  |   | +is_applicable() |
| +calc_discount() |   | +calc_discount()  |   | +calc_discount() |
+------------------+   +-------------------+   +--------------+


+-----------------+      (creates)      +---------------------------+
| StrategyFactory | ------------------> | <<Abstract>>              |
+-----------------+                     | CouponValidationStrategy  |
+-----------------+


+----------------------------+
|      <<Service>>           |
|       CouponService        |
| (services/coupon_service.py)|
+----------------------------+
| - coupon_server: CouponServer |
| - strategy_factory: StrategyFactory |
| (CacheManager: Future)     |
+----------------------------+
| + apply_coupon(code, cart) |
| + create_coupon(data)      |
+----------------------------+
       |
       | (Composition: has-a)
       V
+----------------------------+      (uses)      +-----------------+
|    <<Server>>              |----------------->|    PyMongo      |
|     CouponServer           |                  +-----------------+
| (server/coupon_server.py)  |
+----------------------------+
| + find_by_code(code)       |
| + save(coupon)             |
+----------------------------+

+----------------------------+
|      <<Cache>> (Future)    |
|     CacheManager           |
| (Redis Caching)            |
+----------------------------+

+----------------------------+
|      <<Schema>>            |
|     CouponSchema           |
| (schema/coupon_schema.py)  |
+----------------------------+
| + load(data)               |
| + dump(obj)                |
+----------------------------+

+----------------------------+
|      <<Model>>             |
|        Coupon              |
| (models.py)                |
+----------------------------+
| - _id                      |
| - coupon_code              |
| - type                     |
| - ...                      |
+----------------------------+
| + from_dict()              |
| + to_dict()                |
+----------------------------+

+----------------------------+
|      <<Route>>             |
|     CouponRoutes           |
| (route/coupon_routes.py)   |
+----------------------------+
| + create_coupon_endpoint() |
| + get_coupons_endpoint()   |
+----------------------------+
```
