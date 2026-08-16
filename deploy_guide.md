# Hướng Dẫn Deploy Ứng Dụng Nhanh lên Máy Chủ Ảo AWS EC2 (Ubuntu & Apache2)

Hướng dẫn này trình bày chi tiết từng bước để triển khai bài lab/assignment 2 môn Cloud Computing (COSC2980) sử dụng máy chủ Ubuntu EC2, Web server Apache2 (`mod_wsgi`), Python 3, và kết nối với AWS DynamoDB & S3.

---

## 1. Chuẩn Bị Tải Nguyên trên AWS

### Step 1.1: Gán IAM Role cho EC2 Instance (AWS Academy / Learner Lab)
Trong môi trường **AWS Academy Learner Lab (Vocareum)**, sinh viên **không có quyền tạo IAM Role mới** (gặp lỗi `iam:CreateRole is not authorized`). 
Thay vào đó, AWS Academy đã tạo sẵn Role mang tên **`LabRole`** có đầy đủ quyền với DynamoDB và S3:

1. Vào EC2 Management Console -> Chọn Instance Ubuntu của bạn.
2. Bấm vào menu **Actions** -> **Security** -> **Modify IAM role**.
3. Tại ô tìm kiếm IAM role, chọn Role sẵn có tên là **`LabRole`** (hoặc `LabInstanceProfile`).
4. Bấm **Update IAM role** để gán cho EC2.

*(Nếu chạy ứng dụng ngoài môi trường AWS EC2 hoặc không dùng IAM Role, bạn có thể thiết lập `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` qua biến môi trường hoặc chạy `aws configure`).*


### Step 1.2: Mở Cổng Inbound Security Group
Trong Security Group của EC2 Instance:
- Mở cổng **HTTP (80)**: Source `0.0.0.0/0`
- Mở cổng **HTTPS (443)**: Source `0.0.0.0/0`
- Mở cổng **SSH (22)**: Source `My IP` hoặc `0.0.0.0/0`

---

## 2. Kết Nối Vào Máy Chủ EC2 & Cài Đặt Các Gói Cần Thiết

Kết nối SSH vào EC2 Ubuntu:
```bash
ssh -i "your-key.pem" ubuntu@your-ec2-public-ip
```

Cập nhật các gói hệ thống và cài đặt Apache2, Python3, `libapache2-mod-wsgi-py3`:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv apache2 libapache2-mod-wsgi-py3 git
```

Bật dịch vụ Apache2:
```bash
sudo systemctl start apache2
sudo systemctl enable apache2
```

---

## 3. Triển Khai Mã Nguồn Ứng Dụng

### Step 3.1: Đưa Mã Nguồn Vào Thư Mục `/var/www/html/cloudmusic`
```bash
# Tạo thư mục dự án
sudo mkdir -p /var/www/html/cloudmusic
sudo chown -R ubuntu:ubuntu /var/www/html/cloudmusic

# Copy toàn bộ file dự án vào /var/www/html/cloudmusic
# (Có thể clone qua Git hoặc dùng scp từ máy cá nhân)
# Ví dụ SCP từ máy local:
# scp -i "your-key.pem" -r ./* ubuntu@your-ec2-public-ip:/var/www/html/cloudmusic/
```

### Step 3.2: Tạo Môi Trường Ảo Python (Virtual Environment)
```bash
cd /var/www/html/cloudmusic
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 4. Khởi Tạo Cơ Sở Dữ Liệu DynamoDB & S3 Bucket

Chạy script `init_db.py` để tự động tạo bảng DynamoDB (`login`, `music`, `subscriptions`), tạo S3 Bucket, tải ảnh ca sĩ/bài hát từ `a2.json`, upload lên S3 và chèn dữ liệu nhạc vào DynamoDB:

```bash
# Đảm bảo đang ở môi trường ảo
source /var/www/html/cloudmusic/venv/bin/activate

# Chạy script khởi tạo
python3 init_db.py
```

*Kết quả mong đợi:*
- Bảng DynamoDB `login` được tạo với Hash Key: `email`.
- Bảng DynamoDB `music` được tạo với Hash Key: `title`.
- Bảng DynamoDB `subscriptions` được tạo với Hash Key: `email`, Range Key: `title`.
- Bucket S3 được tạo và ảnh được upload lên thư mục `images/`.

---

## 5. Cấu Hình Apache2 Web Server

### Step 5.1: Cấu Hình VirtualHost
Tạo file cấu hình VirtualHost cho Apache:
```bash
sudo nano /etc/apache2/sites-available/cloudmusic.conf
```

Dán nội dung sau vào file:
```apache
<VirtualHost *:80>
    ServerName localhost
    ServerAdmin webmaster@localhost

    # Định vị môi trường Python Virtual Environment và WSGI
    WSGIDaemonProcess cloudmusic python-home=/var/www/html/cloudmusic/venv python-path=/var/www/html/cloudmusic
    WSGIProcessGroup cloudmusic
    WSGIScriptAlias / /var/www/html/cloudmusic/wsgi.py

    <Directory /var/www/html/cloudmusic>
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>

    Alias /static /var/www/html/cloudmusic/static
    <Directory /var/www/html/cloudmusic/static/>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/cloudmusic_error.log
    CustomLog ${APACHE_LOG_DIR}/cloudmusic_access.log combined
</VirtualHost>
```

### Step 5.2: Kích Hoạt VirtualHost & Khởi Động Lại Apache
```bash
# Tắt trang mặc định của Apache
sudo a2dissite 000-default.conf

# Kích hoạt trang cloudmusic
sudo a2ensite cloudmusic.conf

# Kiểm tra cú pháp cấu hình Apache
sudo apache2ctl configtest
# Trả về "Syntax OK" là thành công!

# Khởi động lại Apache2
sudo systemctl restart apache2
```

---

## 6. Phương Án Dự Phòng: Triển Khai Apache2 làm Reverse Proxy tới Gunicorn

Nếu `mod_wsgi` gặp vấn đề tương thích phiên bản Python, bạn có thể dùng Gunicorn kết hợp Apache2 Reverse Proxy (`mod_proxy`):

### Step 6.1: Tạo Systemd Service cho Gunicorn
```bash
sudo nano /etc/systemd/system/cloudmusic.service
```

Nội dung file:
```ini
[Unit]
Description=Gunicorn instance to serve CloudMusic Flask app
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/var/www/html/cloudmusic
Environment="PATH=/var/www/html/cloudmusic/venv/bin"
ExecStart=/var/www/html/cloudmusic/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 wsgi:application

[Install]
WantedBy=multi-user.target
```

Kích hoạt và khởi chạy service:
```bash
sudo systemctl daemon-reload
sudo systemctl start cloudmusic
sudo systemctl enable cloudmusic
```

### Step 6.2: Cấu hình Apache Proxy Pass
Bật các module proxy của Apache:
```bash
sudo a2enmod proxy proxy_http
```

Sửa file `/etc/apache2/sites-available/cloudmusic.conf`:
```apache
<VirtualHost *:80>
    ServerName localhost

    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    Alias /static /var/www/html/cloudmusic/static
    <Directory /var/www/html/cloudmusic/static/>
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/cloudmusic_error.log
    CustomLog ${APACHE_LOG_DIR}/cloudmusic_access.log combined
</VirtualHost>
```

Khởi động lại Apache:
```bash
sudo systemctl restart apache2
```

---

## 7. Kiểm Tra Hoạt Động (Verification)

Mở trình duyệt truy cập: `http://<YOUR_EC2_PUBLIC_IP>`

1. **Đăng Ký (`/register`)**:
   - Nhập Email, Username, Password.
   - Thử đăng ký lại cùng 1 email -> Kiểm tra thông báo lỗi exact text: `"The email already exists"`.
2. **Đăng Nhập (`/login`)**:
   - Thử đăng nhập sai mật khẩu -> Kiểm tra thông báo lỗi exact text: `"email or password is invalid"`.
   - Đăng nhập đúng -> Chuyển hướng tới trang chính (`/`).
3. **Trang Chính (`/`)**:
   - **User Area**: Hiển thị đúng `user_name`.
   - **Query Area**: Nhập tiêu đề/năm/ca sĩ. Thử tìm thông tin không tồn tại -> Kiểm tra thông báo exact text: `"No result is retrieved. Please query again"`.
   - Bấm nút **Subscribe** bài hát -> Bài hát hiển thị kèm ảnh S3 trong Subscription Area và lưu vào DynamoDB `subscriptions`.
   - Bấm nút **Remove** -> Bài hát bị xóa khỏi giao diện và xóa dữ liệu trong DynamoDB `subscriptions`.
   - Bấm **Logout** -> Đăng xuất thành công về màn hình Đăng nhập.
