import os
from flask import Flask, g
from pymongo import MongoClient

# Import the blueprint from our new structure
from coupon_service.route.coupon_routes import coupon_api_blueprint


def create_app():
    """
    Application Factory to create and configure the Flask app.
    """
    app = Flask(__name__)

    # --- Configuration ---
    # Load configuration from environment variables
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/coupon_db")

    # --- Database & Cache Connections ---
    # Use app context for managing connections
    @app.before_request
    def before_request():
        # Note: In a larger app, you'd use a more robust connection pool management
        # and potentially a custom Flask extension for DB/Redis.
        if "db" not in g:
            app.mongo_client = MongoClient(mongo_uri)
            g.db = app.mongo_client.get_database()

    @app.teardown_request
    def teardown_request(exception):
        # Close the database connection at the end of the request
        db_client = app.mongo_client  # Access the client stored on the app object
        if db_client is not None:
            db_client.close()

    # --- Register Blueprints ---
    app.register_blueprint(coupon_api_blueprint, url_prefix="/api/v1")

    # A simple health-check endpoint
    @app.route("/health")
    def health():
        return "OK", 200

    return app


# Create the app instance for Gunicorn to run
app = create_app()
