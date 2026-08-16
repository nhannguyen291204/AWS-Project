# 🎵 Hướng Dẫn Chạy & Triển Khai Dự Án AWS Music Subscription

Tài liệu hướng dẫn chi tiết dành cho các thành viên trong nhóm làm việc chung dự án. Bất kỳ ai clone code về chỉ cần thực hiện đúng theo các bước dưới đây là ứng dụng có thể chạy mượt mà 100%.

---

## 📌 1. Tổng quan dự án

Ứng dụng Web viết bằng **Node.js (Express)** kết hợp với các dịch vụ đám mây **AWS**:
* **AWS DynamoDB**: Lưu trữ thông tin Người dùng (Login / Register), Danh sách 128 bài hát, và Subscriptions.
* **AWS S3**: Lưu trữ ảnh nghệ sĩ / ca sĩ của các bài hát.

---

## 🛠️ 2. Các bước chạy trên máy cá nhân (Local)

### 🔹 Bước 1: Clone dự án & Tạo file `.env`
1. Clone dự án về máy:
   ```bash
   git clone https://github.com/nhannguyen291204/AWS-Project.git
   cd nw
   ```
2. Tạo file cấu hình từ file mẫu:
   ```bash
   cp .env.example .env
   ```
   *(Nếu dùng Windows CMD: `copy .env.example .env`)*

### 🔹 Bước 2: Điền thông tin AWS vào file `.env`
Mở file `.env` vừa tạo và điền các thông tin sau:

1. Vào trang **AWS Academy Learner Lab** ➡️ bấm **AWS Details** ➡️ bấm chữ **Show** ở mục *AWS CLI credentials*.
2. Copy các giá trị dán tương ứng vào `.env`:
   * `AWS_ACCESS_KEY_ID`: Điền giá trị `aws_access_key_id`
   * `AWS_SECRET_ACCESS_KEY`: Điền giá trị `aws_secret_access_key`
   * `AWS_SESSION_TOKEN`: Điền giá trị `aws_session_token` (Lưu ý: Token này sẽ hết hạn sau vài tiếng, khi hết hạn bạn chỉ cần vào AWS lấy token mới dán lại vào đây).
   * `AWS_REGION`: Để mặc định `us-east-1`
   * `S3_BUCKET_NAME`: Tên S3 Bucket của bạn trên AWS (ví dụ: `cloudmusic-a2`).
   * `FIRST_NAME` & `LAST_NAME`: Điền Họ và Tên của bạn.

### 🔹 Bước 3: Cài đặt thư viện (Dependencies)
```bash
npm install
```

### 🔹 Bước 4: Khởi tạo dữ liệu AWS (Bootstrap)
Chạy lệnh nạp dữ liệu:
```bash
npm run bootstrap
```
👉 **Lệnh này tự động thực hiện:**
* Tạo 3 bảng trên DynamoDB: `login`, `music`, `subscription`.
* Đọc 128 bài hát từ `a2.json`, tự động tải ảnh về và upload lên S3 Bucket.
* Tạo sẵn 10 tài khoản dùng thử từ `s3000000@student.rmit.edu.au` đến `s3000009@student.rmit.edu.au`.

### 🔹 Bước 5: Khởi chạy ứng dụng
```bash
npm start
```
Mở trình duyệt truy cập: **[http://localhost:3000](http://localhost:3000)**

🔑 **Tài khoản đăng nhập dùng thử:**
- **Email**: `s3000000@student.rmit.edu.au`
- **Mật khẩu**: `012345`

---

## ☁️ 3. Triển khai (Deploy) siêu nhanh lên AWS EC2 bằng `git clone`

Dùng `git clone` trực tiếp trên EC2 vừa nhanh gọn, vừa không tốn thời gian upload file!

### 🔹 Bước 1: Chuẩn bị EC2
* Bật 1 instance Ubuntu trên AWS Console.
* Mở **Security Group**: Cho phép cổng **HTTP (80)** và **SSH (22)**.
* Gán **IAM Role** cho EC2 có quyền làm việc với DynamoDB và S3.

### 🔹 Bước 2: SSH vào EC2 & Git Clone mã nguồn
1. SSH vào máy chủ EC2:
   ```bash
   ssh -i "duong_dan_den_file_key.pem" ubuntu@IP_PUBLIC_EC2
   ssh -i "/Users/macbook/Downloads/labsuser.pem" ubuntu@3.80.1.214

/Users/macbook/Downloads/labsuser.pem
   ```
2. Clone trực tiếp mã nguồn vào thư mục `music-app`:
   ```bash
   git clone https://github.com/nhannguyen291204/AWS-Project.git /home/ubuntu/music-app
   cd /home/ubuntu/music-app
   ```

### 🔹 Bước 3: Tạo file `.env` trên EC2
* **Cách 1 (Nhanh nhất - SCP file `.env` từ máy cá nhân lên)**:
  Mở cửa sổ Terminal ở máy bạn và gõ:
  ```bash
  scp -i "duong_dan_den_file_key.pem" .env ubuntu@IP_PUBLIC_EC2:/home/ubuntu/music-app/.env
  ```
* **Cách 2 (Tạo trực tiếp trên EC2)**:
  ```bash
  cp .env.example .env
  nano .env    # Dán thông tin AWS vào, bấm Ctrl+O -> Enter -> Ctrl+X để lưu
  ```

### 🔹 Bước 4: Chạy script tự động cài đặt
Tại thư mục `/home/ubuntu/music-app` trên EC2:
```bash
sudo bash deploy/setup-ec2.sh
```
*(Script sẽ tự động cài Node.js, Nginx, cài `npm install` và chạy service ngầm)*

### 🔹 Bước 5: Kiểm tra ứng dụng
```bash
sudo systemctl status music-app
```
*(Hiển thị `active (running)` màu xanh là hoàn tất 100%)*

Mở trình duyệt gõ: `http://IP_PUBLIC_EC2` để truy cập ứng dụng!

---

## ⚠️ Lưu ý khắc phục sự cố nhanh (Troubleshooting)

1. **Báo lỗi `UnrecognizedClientException` / `Unexpected server error`**:
   - Do mã `AWS_SESSION_TOKEN` trong `.env` đã hết hạn. Hãy vào AWS Learner Lab lấy lại 3 dòng AWS credentials mới và dán lại vào `.env`.
2. **Báo lỗi `Operation timed out` khi SSH vào EC2**:
   - Kiểm tra xem máy chủ EC2 có bị đổi IP mới khi bật lại không.
   - Kiểm tra Security Group của EC2 đã mở port 22 (SSH) chưa.
