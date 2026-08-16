# 🎵 Hướng Dẫn Sử Dụng Ứng Dụng AWS Music Subscription (Dành Cho Người Mới Bắt Đầu)

Tài liệu này được viết bằng Tiếng Việt với các bước đơn giản nhất, giúp bạn dễ dàng chạy ứng dụng web nghe nhạc sử dụng dịch vụ đám mây AWS (DynamoDB & S3).

---

## 📌 1. Dự án này là gì?

Đây là một ứng dụng Web viết bằng **Node.js (Express)** kết hợp với các dịch vụ đám mây **AWS**:
* **AWS DynamoDB** (CSDL NoSQL): Dùng để lưu trữ thông tin Người dùng (login/đăng ký), Bài hát, và Danh sách đăng ký nhạc.
* **AWS S3** (Kho lưu trữ): Dùng để lưu trữ ảnh đại diện của các nghệ sĩ / ca sĩ.

---

## 🛠️ 2. Chuẩn bị những gì?

Trước khi bắt đầu, bạn cần có:
1. **Node.js** đã cài đặt trên máy tính.
2. Tài khoản **AWS Academy Learner Lab** (đang hoạt động).
3. Đã tạo sẵn **1 S3 Bucket** trên AWS Console (Ví dụ đặt tên bucket là `my-music-bucket-12345` - lưu ý tên bucket trên S3 phải là duy nhất trên toàn cầu).

---

## 🚀 3. Các bước chạy ứng dụng trên máy tính (Local)

### 🔹 Bước 1: Mở Terminal / Command Prompt tại thư mục dự án
Mở thư mục `nw` bằng VS Code hoặc Terminal.

### 🔹 Bước 2: Tạo file cấu hình `.env`
Chạy lệnh sau để tạo file `.env` từ file mẫu:
```bash
cp .env.example .env
```
*(Nếu dùng Windows CMD, bạn copy file `.env.example` rồi đổi tên thành `.env`)*

### 🔹 Bước 3: Điền thông tin AWS vào file `.env`
Mở file `.env` lên, bạn sẽ thấy các thông tin cần điền:

1. Vào trang **AWS Academy Learner Lab** -> chọn **AWS Details** -> bấm **Show** ở mục *AWS CLI credentials*.
2. Copy các giá trị dán vào `.env`:
   * `AWS_ACCESS_KEY_ID`: Điền `aws_access_key_id` từ AWS.
   * `AWS_SECRET_ACCESS_KEY`: Điền `aws_secret_access_key` từ AWS.
   * `AWS_SESSION_TOKEN`: Điền `aws_session_token` từ AWS (Token tạm thời).
   * `AWS_REGION`: Để mặc định là `us-east-1`.
   * `S3_BUCKET_NAME`: Điền tên S3 Bucket bạn đã tạo ở phần Chuẩn bị.
   * `FIRST_NAME` & `LAST_NAME`: Điền Tên và Họ của bạn (ví dụ: `FIRST_NAME=Van A`, `LAST_NAME=Nguyen`).

### 🔹 Bước 4: Cài đặt thư viện (Dependencies)
Gõ lệnh sau và ấn Enter:
```bash
npm install
```

### 🔹 Bước 5: Nạp dữ liệu mẫu vào AWS (Bootstrap)
Gõ lệnh sau và ấn Enter:
```bash
npm run bootstrap
```
👉 **Lệnh này làm gì?**
* Tự động tạo 3 bảng trên DynamoDB: `login`, `music`, `subscriptions`.
* Đọc dữ liệu 128 bài hát trong file `a2.json`, tự động tải ảnh nghệ sĩ về và up lên S3 Bucket của bạn.
* Tạo sẵn 10 tài khoản người dùng mẫu để bạn đăng nhập thử.

### 🔹 Bước 6: Khởi chạy ứng dụng Web
Gõ lệnh sau:
```bash
npm start
```
Khi màn hình báo Server đang chạy, bạn mở trình duyệt (Chrome/Edge/Safari) và truy cập vào đường dẫn:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## 🔑 4. Tài khoản đăng nhập dùng thử

Lệnh `npm run bootstrap` ở trên đã tự tạo sẵn 10 tài khoản sinh viên mẫu:

| Email đăng nhập | Mật khẩu (Password) |
| :--- | :--- |
| `s3000000@student.rmit.edu.au` | `012345` |
| `s3000001@student.rmit.edu.au` | `123456` |
| `s3000002@student.rmit.edu.au` | `234567` |
| ... | ... |
| `s3000009@student.rmit.edu.au` | `901234` |

*(Quy tắc mật khẩu: dịch sang phải 1 số từ 012345)*

---

## ☁️ 5. Hướng dẫn đưa ứng dụng lên máy chủ AWS EC2

Nếu bài tập yêu cầu triển khai (deploy) ứng dụng lên đám mây AWS EC2:

1. **Tạo 1 máy chủ EC2 (Ubuntu 22.04/20.04)** trên AWS Console:
   * Mở cổng **Security Group**: Cho phép **HTTP (port 80)** và **SSH (port 22)**.
   * Gán **IAM Role** cho EC2 có quyền truy cập DynamoDB và S3.

2. **Upload code từ máy bạn lên EC2**:
   ```bash
   scp -i "file-key-cua-ban.pem" -r . ubuntu@DC_IP_HOAC_DNS_EC2:/home/ubuntu/music-app
   ```

3. **Truy cập vào EC2 qua SSH**:
   ```bash
   ssh -i "file-key-cua-ban.pem" ubuntu@DC_IP_HOAC_DNS_EC2
   ```

4. **Chạy script tự động cài đặt trên EC2**:
   ```bash
   cd /home/ubuntu/music-app
   cp .env.example .env
   nano .env   # (Điền thông tin AWS tương tự bước ở local)
   sudo bash deploy/setup-ec2.sh
   ```

5. Sau khi hoàn tất, bạn mở trình duyệt gõ `http://IP_PUBLIC_CUA_EC2` là có thể truy cập trang web!

---

## 🔍 6. Các câu lệnh hữu ích khi kiểm tra lỗi

* **Kiểm tra trạng thái app**: `npm run check`
* **Xem nhật ký hoạt động (Logs) trên EC2**: `sudo journalctl -u music-app -f`
