# Schema & Data Design

This document details the data storage design for the coupon service, covering both the persistent database (MongoDB) and the in-memory cache (Redis).

---

## 1. MongoDB Schema Design

We will use a single collection approach in MongoDB to store all coupon types. This provides flexibility and makes it easy to query for coupons without knowing their type in advance.

**Collection:** `coupons`

---

### Document Structure

Each document in the `coupons` collection will represent a single coupon and will have the following structure:

| Key | Data Type | Description | Example |
|---|---|---|---|
| `_id` | String | The primary key for the document. Manually generated as a short base63 string from a Snowflake ID. | `"base63ID"` |
| `coupon_code` | String | A unique, user-facing, human-readable code for the coupon. Indexed for fast lookups. | `"SUMMER25"` |
| `status` | String | The current status of the coupon. Must be one of: `active`, `inactive`. | `"active"` |
| `type` | String | **Discriminator Key.** Defines the coupon type. Must be one of: `cart-wise`, `product-wise`, `bxgy`. | `"cart-wise"` |
| `description` | String | A user-friendly description of the coupon for display purposes. | `"10% off on orders over $100"` |
| `metadata` | Object | A flexible sub-document containing the specific rules and conditions that apply to this coupon type. | See examples below. |
| `_created_at` | ISODate | Timestamp of when the document was created. Automatically managed. | `ISODate("2023-01-28...")` |
| `_modified_at` | ISODate | Timestamp of the last update. Automatically managed. | `ISODate("2023-01-29...")` |
| `_created_by` | String | User ID who created the coupon. | `"flobot"` |
| `_modified_by` | String | User ID who last modified the coupon. | `"flobot"` |

---

### Future Fields (To be implemented)

| Key | Data Type | Description | Example |
|---|---|---|---|
| `expires_at`| ISODate | The date and time when the coupon becomes invalid. | `ISODate("2023-12-31...")` |
| `usage_limit`| Integer | The total number of times this coupon can be used. | `1000` |
| `usage_count`| Integer | The current count of how many times the coupon has been used. | `150` |

---

### `metadata` Sub-Document Examples

The structure of the `metadata` object changes based on the `type` field.

#### For `type: "cart-wise"`
| Key | Data Type | Description |
|---|---|---|
| `min_cart_total` | Number | The minimum total value the cart must have to qualify. |
| `discount_percentage` | Number | The percentage discount to apply to the cart total. |

*Example:*
```json
"metadata": {
  "min_cart_total": 100.00,
  "discount_percentage": 10
}
```

#### For `type: "product-wise"`
| Key | Data Type | Description |
|---|---|---|
| `product_id` | String | The ID of the product that this coupon applies to. |
| `discount_amount` | Number | A fixed amount to discount from the product's price. |
| `discount_percentage`| Number | A percentage to discount from the product's price. |

*Example:*
```json
"metadata": {
  "product_id": "prod_12345",
  "discount_amount": 5.50
}
```

#### For `type: "bxgy"`
| Key | Data Type | Description |
|---|---|---|
| `buy_products` | Array of Objects | A list of products the user must have in their cart. |
| `get_products` | Array of Objects | A list of products the user will get a discount on. |
| `repetition_limit`| Number | The maximum number of times this offer can be applied in one cart. |

*Example:*
```json
"metadata": {
  "buy_products": [
    { "product_id": "prod_A", "quantity": 2 }
  ],
  "get_products": [
    { "product_id": "prod_B", "quantity": 1 }
  ],
  "repetition_limit": 3
}
```

---

## New Collection: `user_coupon_purchases`

This collection will store a record of each successful coupon application on a user's purchase.

### Document Structure

| Key | Data Type | Description | Example |
|---|---|---|---|
| `_id` | String | Primary key (short base63 Snowflake ID). | `"purchaseID"` |
| `user_id` | String | The ID of the user who made the purchase. | `"user_abc"` |
| `coupon_id` | String | The `_id` of the coupon applied. | `"base63ID"` |
| `coupon_code` | String | The `coupon_code` of the coupon applied. | `"SUMMER25"` |
| `purchase_details` | Object | Snapshot of the cart/purchase details at the time of application. | `{ "items": [...], "original_total": 150.00 }` |
| `discount_amount` | Number | The total discount applied by this coupon. | `15.00` |
| `final_price` | Number | The final price of the purchase after discount. | `135.00` |
| `applied_at` | ISODate | Timestamp of when the coupon was successfully applied/purchase made. | `ISODate("2023-01-29...")` |

---

## Future Redis Integration

Redis will be used for performance-critical operations like caching and atomic counters in future versions.

### Future Use Cases:
1. **Caching Coupon Objects:** To reduce read load on MongoDB.
2. **Caching Applicable Coupon Calculations:** To cache the results of the `applicable-coupons` calculation for a given cart.
3. **Atomic Usage Counter:** To safely handle concurrency for limited-use coupons.
