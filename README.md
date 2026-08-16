# AWS Music Subscription

> 🇻🇳 **Tiếng Việt**: Xem hướng dẫn sử dụng đơn giản bằng tiếng Việt tại [README_VI.md](file:///Users/macbook/Documents/nw/README_VI.md).

A Node.js/Express application using DynamoDB for users, music and subscriptions, plus S3 for artist images. It is designed for `us-east-1` in AWS Academy Learner Lab and can be hosted on an Ubuntu EC2 instance.

## 1. Configure locally

```bash
cp .env.example .env
npm install
```

Fill in `.env` with credentials downloaded from **AWS Academy Learner Lab > AWS Details > Show**. Use the temporary access key, secret key, and session token exactly as supplied. Create a unique S3 bucket in the same region first; then set its name in `S3_BUCKET_NAME`.

Set `FIRST_NAME` and `LAST_NAME` before bootstrap. The script creates ten initial users with emails `s3000000@student.rmit.edu.au` through `s3000009@student.rmit.edu.au`; their passwords are `012345`, `123456`, ... `901234`.

## 2. Provision data

```bash
npm run bootstrap
npm start
```

Open `http://localhost:3000`. `bootstrap` creates three on-demand DynamoDB tables, loads all 128 records in `a2.json`, downloads their images, uploads them to S3, and seeds the required login users. The S3 bucket must already exist.

## 3. Deploy on Ubuntu EC2

Create a free-tier Ubuntu 20.04/22.04 EC2 instance and its security group should allow inbound TCP 80 (HTTP) and 22 (SSH). Attach an IAM role permitting DynamoDB access for the three tables and S3 object read/write on the chosen bucket. An IAM role is safer than permanent credentials on EC2.

From your computer, copy this directory to the instance (do not copy `.env` unless you intentionally need it):

```bash
scp -i your-key.pem -r . ubuntu@YOUR_EC2_PUBLIC_DNS:/home/ubuntu/music-app
```

Then SSH in and run:

```bash
cd /home/ubuntu/music-app
cp .env.example .env
nano .env
sudo bash deploy/setup-ec2.sh
```

After `systemctl status music-app`, browse to `http://YOUR_EC2_PUBLIC_DNS`. Nginx proxies public port 80 to the app's local port 3000.

## Useful checks

```bash
npm run check
sudo journalctl -u music-app -f
aws dynamodb scan --table-name music --select COUNT --region us-east-1
```

## Security note

The supplied assessment schema explicitly requires a `password` field and known seed values, so this recreation stores it as specified. For any production use, replace it with a salted password hash and use a durable session store instead of the default memory store.
