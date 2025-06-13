-- backend_flask/schema.sql

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_wishlist;
DROP TABLE IF EXISTS user_cart;
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS orders; -- For mock checkout

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE, -- Can be NULL if optional
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_preferences (
    user_id INTEGER PRIMARY KEY,
    -- Store preferences as JSON text for flexibility
    -- e.g., {"liked_colors": {"red": 2, "blue": 1}, "interacted_categories": ["Apparel", "Footwear"]}
    preferences_json TEXT, 
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE user_wishlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id TEXT NOT NULL, -- Assuming product IDs from catalog are strings
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    UNIQUE (user_id, product_id) -- Prevent duplicates
);

CREATE TABLE user_cart (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 1, -- Added quantity
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
    -- A product can only appear once in the cart; quantity is updated.
    -- To enforce this, we make the combination of user and product unique.
    -- This design is simpler for this project.
    -- UNIQUE(user_id, product_id)
);

CREATE TABLE orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_str_id TEXT UNIQUE NOT NULL, -- Human-readable string ID
    user_id INTEGER NOT NULL,
    items_json TEXT NOT NULL, -- JSON string of {"product_id": "id", "name": "name", "price": "price", "quantity": 1}
    total_price REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'confirmed_mock',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);