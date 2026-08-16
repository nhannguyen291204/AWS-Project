import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash
)
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# AWS Resource Initializations using standard SDK credential chain
dynamodb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
s3_client = boto3.client("s3", region_name=config.AWS_REGION)

login_table = dynamodb.Table(config.DYNAMODB_LOGIN_TABLE)
music_table = dynamodb.Table(config.DYNAMODB_MUSIC_TABLE)
subscription_table = dynamodb.Table(config.DYNAMODB_SUBSCRIPTION_TABLE)

def get_image_url(s3_key_or_url):
    """
    Retrieves artist image from Amazon S3 (Bucket: 3975356-s3test).
    Generates an S3 presigned URL if s3_key starts with 'images/', otherwise returns direct URL.
    """
    if not s3_key_or_url:
        return ""
    if str(s3_key_or_url).startswith("images/"):
        try:
            url = s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": config.S3_BUCKET_NAME, "Key": s3_key_or_url},
                ExpiresIn=3600
            )
            return url
        except Exception as e:
            print(f"Error generating presigned S3 URL for {s3_key_or_url}: {e}")
            return f"https://{config.S3_BUCKET_NAME}.s3.{config.AWS_REGION}.amazonaws.com/{s3_key_or_url}"
    return s3_key_or_url

@app.route("/")
def main():
    # Task 1.3.2 check
    if "user_email" not in session:
        return redirect(url_for("login"))

    user_email = session["user_email"]
    user_name = session.get("user_name", "")

    # Task 1.5.2.1: Fetch user subscriptions (title, artist, year) from DynamoDB
    subscriptions = []
    try:
        resp = subscription_table.query(
            KeyConditionExpression=Key("email").eq(user_email)
        )
        items = resp.get("Items", [])
        for item in items:
            s3_key = item.get("s3_key") or item.get("img_url") or item.get("image_url")
            # Task 1.5.2.2: Retrieve artist image from S3
            item["resolved_image_url"] = get_image_url(s3_key)
            subscriptions.append(item)
    except Exception as e:
        print(f"Error querying subscriptions: {e}")

    query_results = session.pop("query_results", None)
    query_error = session.pop("query_error", None)

    return render_template(
        "main.html",
        user_name=user_name, # Task 1.5.1
        user_email=user_email,
        subscriptions=subscriptions, # Task 1.5.2.1 & 1.5.2.2
        query_results=query_results,
        query_error=query_error
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        # Task 1.3.1: Validate credentials against login table
        if not email or not password:
            return render_template("login.html", error="email or password is invalid")

        try:
            resp = login_table.get_item(Key={"email": email})
            item = resp.get("Item")
            
            if not item or item.get("password") != password:
                # Task 1.3.1 exact error string
                return render_template("login.html", error="email or password is invalid")

            # Task 1.3.2: Valid credentials -> save session & redirect to main page
            session["user_email"] = item["email"]
            session["user_name"] = item.get("user_name", email)
            return redirect(url_for("main"))

        except Exception as e:
            print(f"Login DynamoDB Error: {e}")
            return render_template("login.html", error="email or password is invalid")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        user_name = request.form.get("user_name", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not user_name or not password:
            return render_template("register.html", error="Please fill in all fields")

        try:
            # Task 1.4.1: Check if entered email matches email stored in login table
            resp = login_table.get_item(Key={"email": email})
            if "Item" in resp:
                # Task 1.4.1 exact error string
                return render_template("register.html", error="The email already exists")

            # Task 1.4.2.1: Unique email -> store new user info in login table
            login_table.put_item(
                Item={
                    "email": email,
                    "user_name": user_name,
                    "password": password
                }
            )
            # Task 1.4.2.2: Redirect to login page
            flash("Registration successful! Please login with your new account.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            print(f"Register Error: {e}")
            return render_template("register.html", error="An error occurred during registration.")

    return render_template("register.html")

@app.route("/query", methods=["POST"])
def query_music():
    if "user_email" not in session:
        return redirect(url_for("login"))

    title_query = request.form.get("title", "").strip()
    year_query = request.form.get("year", "").strip()
    artist_query = request.form.get("artist", "").strip()

    # Task 1.5.3.2.1: Build AND FilterExpression for multiple query conditions
    conditions = []
    if title_query:
        conditions.append(Attr("title").contains(title_query))
    if year_query:
        conditions.append(Attr("year").eq(year_query))
    if artist_query:
        conditions.append(Attr("artist").contains(artist_query))

    try:
        if not conditions:
            resp = music_table.scan()
        else:
            # Connect multiple query conditions using AND operator by default
            filter_expr = conditions[0]
            for cond in conditions[1:]:
                filter_expr = filter_expr & cond
            resp = music_table.scan(FilterExpression=filter_expr)

        items = resp.get("Items", [])

        # Additional in-memory filtering for flexible case-insensitive AND matching
        filtered_items = []
        for item in items:
            match_title = not title_query or title_query.lower() in item.get("title", "").lower()
            match_year = not year_query or year_query.lower() == str(item.get("year", "")).lower()
            match_artist = not artist_query or artist_query.lower() in item.get("artist", "").lower()

            if match_title and match_year and match_artist:
                s3_key = item.get("s3_key") or item.get("img_url") or item.get("image_url")
                # Task 1.5.3.2.2: Retrieve corresponding artist image from S3
                item["resolved_image_url"] = get_image_url(s3_key)
                filtered_items.append(item)

        if not filtered_items:
            # Task 1.5.3.1 exact error string
            session["query_error"] = "No result is retrieved. Please query again"
        else:
            session["query_results"] = filtered_items

    except Exception as e:
        print(f"Query Error: {e}")
        # Task 1.5.3.1 exact error string
        session["query_error"] = "No result is retrieved. Please query again"

    return redirect(url_for("main"))

@app.route("/subscribe", methods=["POST"])
def subscribe():
    """
    Task 1.5.3.2.3: Add subscribed music info and corresponding artist image into subscription area
    and store subscribed music info in DynamoDB.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    user_email = session["user_email"]
    title = request.form.get("title")
    artist = request.form.get("artist")
    year = request.form.get("year")
    s3_key = request.form.get("s3_key")
    img_url = request.form.get("img_url") or request.form.get("image_url")

    if title:
        try:
            subscription_table.put_item(
                Item={
                    "email": user_email,
                    "title": title,
                    "artist": artist,
                    "year": str(year),
                    "s3_key": s3_key,
                    "image_url": img_url,
                    "img_url": img_url
                }
            )
        except Exception as e:
            print(f"Subscribe Error: {e}")

    return redirect(url_for("main"))

@app.route("/remove_subscription", methods=["POST"])
def remove_subscription():
    """
    Task 1.5.2.3: Remove subscribed music info and artist info from subscription area
    and the corresponding table in DynamoDB.
    """
    if "user_email" not in session:
        return redirect(url_for("login"))

    user_email = session["user_email"]
    title = request.form.get("title")

    if title:
        try:
            subscription_table.delete_item(
                Key={
                    "email": user_email,
                    "title": title
                }
            )
        except Exception as e:
            print(f"Remove Subscription Error: {e}")

    return redirect(url_for("main"))

@app.route("/logout")
def logout():
    """
    Task 1.5.4: Redirect user to login page on Logout
    """
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
