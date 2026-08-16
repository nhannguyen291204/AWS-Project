import json
import os
import requests
import boto3
from botocore.exceptions import ClientError
import config

def get_dynamodb_client():
    return boto3.client("dynamodb", region_name=config.AWS_REGION)

def get_dynamodb_resource():
    return boto3.resource("dynamodb", region_name=config.AWS_REGION)

def get_s3_client():
    return boto3.client("s3", region_name=config.AWS_REGION)

def create_tables():
    dynamodb = get_dynamodb_client()
    existing_tables = dynamodb.list_tables()["TableNames"]

    # Task 1.1.1: Create 'login' table
    if config.DYNAMODB_LOGIN_TABLE not in existing_tables:
        print(f"Creating DynamoDB table '{config.DYNAMODB_LOGIN_TABLE}'...")
        dynamodb.create_table(
            TableName=config.DYNAMODB_LOGIN_TABLE,
            KeySchema=[
                {"AttributeName": "email", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "email", "AttributeType": "S"}
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        print(f"Table '{config.DYNAMODB_LOGIN_TABLE}' creation initiated.")
    else:
        print(f"Table '{config.DYNAMODB_LOGIN_TABLE}' already exists.")

    # Task 1.1.2: Create 'music' table
    if config.DYNAMODB_MUSIC_TABLE not in existing_tables:
        print(f"Creating DynamoDB table '{config.DYNAMODB_MUSIC_TABLE}'...")
        dynamodb.create_table(
            TableName=config.DYNAMODB_MUSIC_TABLE,
            KeySchema=[
                {"AttributeName": "title", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "title", "AttributeType": "S"}
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        print(f"Table '{config.DYNAMODB_MUSIC_TABLE}' creation initiated.")
    else:
        print(f"Table '{config.DYNAMODB_MUSIC_TABLE}' already exists.")

    # Create 'subscriptions' table
    if config.DYNAMODB_SUBSCRIPTION_TABLE not in existing_tables:
        print(f"Creating DynamoDB table '{config.DYNAMODB_SUBSCRIPTION_TABLE}'...")
        dynamodb.create_table(
            TableName=config.DYNAMODB_SUBSCRIPTION_TABLE,
            KeySchema=[
                {"AttributeName": "email", "KeyType": "HASH"},
                {"AttributeName": "title", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "email", "AttributeType": "S"},
                {"AttributeName": "title", "AttributeType": "S"}
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 5,
                "WriteCapacityUnits": 5
            }
        )
        print(f"Table '{config.DYNAMODB_SUBSCRIPTION_TABLE}' creation initiated.")
    else:
        print(f"Table '{config.DYNAMODB_SUBSCRIPTION_TABLE}' already exists.")

    # Wait for tables to become active
    waiter = dynamodb.get_waiter("table_exists")
    waiter.wait(TableName=config.DYNAMODB_LOGIN_TABLE)
    waiter.wait(TableName=config.DYNAMODB_MUSIC_TABLE)
    waiter.wait(TableName=config.DYNAMODB_SUBSCRIPTION_TABLE)
    print("All DynamoDB tables are active!")

def seed_initial_login_users():
    """
    Task 1.1.1: Populates 10 initial student entities into 'login' table.
    """
    dynamodb_res = get_dynamodb_resource()
    login_table = dynamodb_res.Table(config.DYNAMODB_LOGIN_TABLE)

    passwords = [
        "012345", "123456", "234567", "345678", "456789",
        "567890", "678901", "789012", "890123", "901234"
    ]

    print("Seeding initial 10 login entities into 'login' table...")
    for i in range(10):
        email = f"s380000{i}@student.rmit.edu.au"
        user_name = f"Firstname Lastname{i}"
        password = passwords[i]

        login_table.put_item(
            Item={
                "email": email,
                "user_name": user_name,
                "password": password
            }
        )
        print(f"Seeded user: {email} ({user_name})")
    print("Task 1.1.1 Login seeding complete!")

def create_s3_bucket():
    s3 = get_s3_client()
    bucket_name = config.S3_BUCKET_NAME
    try:
        if config.AWS_REGION == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": config.AWS_REGION}
            )
        print(f"S3 Bucket '{bucket_name}' created/verified successfully.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ["BucketAlreadyOwnedByYou", "BucketAlreadyExists"]:
            print(f"S3 Bucket '{bucket_name}' already exists and is ready.")
        else:
            print(f"Notice regarding S3 bucket '{bucket_name}': {e}")

def populate_music_table_and_s3():
    """
    Task 1.1.3 & Task 1.2:
    Automatically reads data from Assignment2-spotify-data-1.json (or a2.json),
    downloads artist/album images from img_url/image_url, uploads to S3, and loads into DynamoDB music table.
    """
    s3 = get_s3_client()
    dynamodb_res = get_dynamodb_resource()
    music_table = dynamodb_res.Table(config.DYNAMODB_MUSIC_TABLE)

    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, config.DATA_JSON_FILE)
    if not os.path.exists(json_path):
        json_path = os.path.join(base_dir, "a2.json")
    
    if not os.path.exists(json_path):
        print(f"Source JSON file not found at '{json_path}'!")
        return

    print(f"Reading dataset from '{json_path}'...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        songs = data.get("songs", data.get("music", []))
    elif isinstance(data, list):
        songs = data
    else:
        songs = []

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    print(f"Processing {len(songs)} music entries...")
    for song in songs:
        title = song.get("title")
        artist = song.get("artist")
        year = str(song.get("year"))
        web_url = song.get("web_url", "")
        img_url = song.get("img_url") or song.get("image_url", "")

        # Format S3 object Key
        artist_slug = str(artist).replace(" ", "_").replace("/", "_").lower()
        title_slug = str(title).replace(" ", "_").replace("/", "_").lower()
        s3_key = f"images/{artist_slug}_{title_slug}.jpg"

        # Task 1.2: Download image from img_url and upload to S3 Bucket
        if img_url:
            try:
                resp = requests.get(img_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    s3.put_object(
                        Bucket=config.S3_BUCKET_NAME,
                        Key=s3_key,
                        Body=resp.content,
                        ContentType=resp.headers.get("Content-Type", "image/jpeg")
                    )
                    print(f"Uploaded to S3: s3://{config.S3_BUCKET_NAME}/{s3_key}")
                else:
                    print(f"Warning: HTTP {resp.status_code} downloading image for '{title}'")
                    s3_key = img_url
            except Exception as err:
                print(f"Error downloading image for '{title}': {err}")
                s3_key = img_url
        else:
            s3_key = ""

        # Task 1.1.2 & 1.1.3: Insert into DynamoDB 'music' table
        music_table.put_item(
            Item={
                "title": title,
                "artist": artist,
                "year": year,
                "web_url": web_url,
                "image_url": img_url,
                "img_url": img_url,
                "s3_key": s3_key
            }
        )
        print(f"Loaded item into DynamoDB 'music': '{title}' by '{artist}' ({year})")

    print("Task 1.1.2, 1.1.3 & 1.2 completed successfully!")

if __name__ == "__main__":
    print("=== COSC2980 Assignment 2 Full Auto Setup ===")
    create_tables()
    seed_initial_login_users()
    create_s3_bucket()
    populate_music_table_and_s3()
    print("=== Setup Completed Successfully ===")
