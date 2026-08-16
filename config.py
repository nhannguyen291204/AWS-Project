import os

# AWS Configuration
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "3975356-s3test")

# Source Data JSON File
DATA_JSON_FILE = os.getenv("DATA_JSON_FILE", "Assignment2-spotify-data-1.json")

# DynamoDB Table Names
DYNAMODB_LOGIN_TABLE = "login"
DYNAMODB_MUSIC_TABLE = "music"
DYNAMODB_SUBSCRIPTION_TABLE = "subscriptions"

# Flask Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "cosc2980-assignment2-secret-key-3975356")
