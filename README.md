# Trình Thu Thập Dữ Liệu Tiền Điện Tử

## Tổng Quan
Dự án này kết nối với API WebSocket của sàn giao dịch Bitget để lấy dữ liệu giá tiền điện tử theo thời gian thực. Dự án thu thập dữ liệu ticker cho các cặp tiền điện tử đã chọn và lưu trữ dữ liệu dưới dạng CSV và trong cơ sở dữ liệu PostgreSQL để phân tích.

## Tính Năng
- Thu thập dữ liệu thời gian thực từ sàn giao dịch Bitget
- Theo dõi nhiều loại tiền điện tử (hiện tại là SOLUSDT, BTCUSDT, ETHUSDT)
- Lưu trữ dữ liệu dưới định dạng CSV để phân tích nhanh
- Tích hợp cơ sở dữ liệu PostgreSQL để lưu trữ lâu dài
- Thời gian thu thập dữ liệu có thể tùy chỉnh

## Yêu Cầu
- Python 3.7+
- Các gói Python cần thiết:
  - websocket-client
  - pandas
  - sqlalchemy
  - psycopg2
- Cơ sở dữ liệu PostgreSQL

## Cài Đặt

1. Clone repository hoặc tải xuống các tệp
2. Cài đặt các gói cần thiết:
```
pip install websocket-client pandas sqlalchemy psycopg2
```
3. Thiết lập cơ sở dữ liệu PostgreSQL và tạo bảng cần thiết:
```sql
CREATE TABLE coin_prices (
    id SERIAL PRIMARY KEY,
    thoi_gian TIMESTAMPTZ NOT NULL,
    gia NUMERIC(20, 8),
    gia_mua NUMERIC(20, 8),
    gia_ban NUMERIC(20, 8),
    khoi_luong_24h NUMERIC(30, 8),
    high24h NUMERIC(20, 8),
    low24h NUMERIC(20, 8),
    instId TEXT,  
    best_purchase_price NUMERIC(20, 8),
    best_sale_price NUMERIC(20, 8)
);
```

## Cách Sử Dụng

1. Mở notebook `wedstock_connect.ipynb` trong Jupyter hoặc VS Code
2. Cấu hình các tham số:
   - `INSTRUMENT_IDS`: Danh sách các cặp tiền điện tử cần theo dõi
   - `run_duration`: Thời gian thu thập dữ liệu (tính bằng giây)
   - Thông số kết nối cơ sở dữ liệu (host, port, database, username, password)
3. Chạy lần lượt các ô trong notebook

## Cách Hoạt Động

1. Ứng dụng kết nối với API WebSocket của Bitget
2. Đăng ký theo dõi kênh ticker cho các cặp tiền điện tử đã xác định
3. Dữ liệu thời gian thực được thu thập và lưu trữ trong:
   - Tệp CSV (`data.csv`)
   - Bảng cơ sở dữ liệu PostgreSQL (`coin_prices`)
4. Kết nối WebSocket được duy trì trong khoảng thời gian đã chỉ định
5. Dữ liệu có thể được truy vấn từ cơ sở dữ liệu để phân tích

## Các Trường Dữ Liệu

- `thoi_gian`: Thời gian của điểm dữ liệu
- `gia`: Giá hiện tại
- `gia_mua`: Giá mua (bid price)
- `gia_ban`: Giá bán (ask price)
- `khoi_luong_24h`: Khối lượng giao dịch trong 24 giờ
- `high24h`: Giá cao nhất trong 24 giờ
- `low24h`: Giá thấp nhất trong 24 giờ
- `instId`: Mã công cụ (cặp tiền điện tử)
- `best_purchase_price`: Khối lượng mua tốt nhất
- `best_sale_price`: Khối lượng bán tốt nhất

## Cấu Hình Cơ Sở Dữ Liệu

Ứng dụng kết nối với cơ sở dữ liệu PostgreSQL với các thông số mặc định sau:
- Host: localhost
- Port: 5432
- Database: postgres
- Username: postgres
- Password: postgres

Bạn có thể chỉnh sửa các thông số này trong notebook để phù hợp với cài đặt của bạn.

## Ghi Chú

- Thời gian thu thập dữ liệu có thể được điều chỉnh bằng cách thay đổi biến `run_duration`
- Để dừng thu thập dữ liệu trước thời gian đã chỉ định, nhấn Ctrl+C
- Tệp CSV được tạo trong cùng thư mục với notebook
- Có thể thiết lập các thời gian khác nhau với biến `a` (60 giây), `b` (1 giờ) và `c` (1 ngày)
