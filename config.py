import os

class DevelopmentConfig():
    DEBUG = True
    HOST = "0.0.0.0"
    PORT = int(os.environ.get("PORT", 5000))  # <-- usa la variable PORT de Railway

config = {
    "development": DevelopmentConfig
}