"""
PostgreSQL Helper - Công cụ hỗ trợ kết nối và quản lý PostgreSQL
"""
import psycopg2
import subprocess
import os
import time

def check_postgres_container():
    """Kiểm tra PostgreSQL container có đang chạy không"""
    try:
        result = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        return "postgres_container" in result.stdout
    except Exception as e:
        return False

def start_postgres_container():
    """Khởi động PostgreSQL container"""
    try:
        compose_dir = os.path.join(os.getcwd(), "postgre-compose")
        if os.path.exists(compose_dir):
            os.chdir(compose_dir)
            subprocess.run(["docker-compose", "up", "-d"], check=True)
            print("Đã khởi động PostgreSQL container")
            time.sleep(5)  # Chờ container khởi động
            return True
        else:
            print(f"Thư mục {compose_dir} không tồn tại")
            return False
    except Exception as e:
        print(f"Lỗi khi khởi động container: {e}")
        return False

def create_postgres_table(host='localhost', port='5000', database='postgres', username='postgres', password='postgres'):
    """Tạo bảng coin_prices trong PostgreSQL"""
    try:
        # Kiểm tra container
        if not check_postgres_container():
            if not start_postgres_container():
                return False
        
        # Kết nối đến PostgreSQL
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=database,
            user=username,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Tạo bảng nếu chưa tồn tại
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS coin_prices (
            id SERIAL PRIMARY KEY,
            thoi_gian TIMESTAMPTZ NOT NULL,
            gia NUMERIC(20, 8),
            gia_mua NUMERIC(20, 8),
            gia_ban NUMERIC(20, 8),
            khoi_luong_24h NUMERIC(30, 8),
            high24h NUMERIC(20, 8),
            low24h NUMERIC(20, 8),
            instid TEXT,  
            best_purchase_price NUMERIC(20, 8),
            best_sale_price NUMERIC(20, 8)
        );
        '''
        cursor.execute(create_table_query)
        
        # Kiểm tra bảng đã tạo chưa
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'coin_prices');")
        table_exists = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        return table_exists
    except Exception as e:
        print(f"Lỗi: {e}")
        return False

def test_postgres_connection(host='localhost', port='5000', database='postgres', username='postgres', password='postgres'):
    """Kiểm tra kết nối đến PostgreSQL và báo cáo chi tiết"""
    results = {
        "localhost": False,
        "127.0.0.1": False,
        "container_running": check_postgres_container(),
        "error_message": None
    }
    
    # Thử kết nối với localhost
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=port,
            dbname=database,
            user=username,
            password=password
        )
        conn.close()
        results["localhost"] = True
    except Exception as e:
        results["error_message_localhost"] = str(e)
    
    # Thử kết nối với 127.0.0.1
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            port=port,
            dbname=database,
            user=username,
            password=password
        )
        conn.close()
        results["127.0.0.1"] = True
    except Exception as e:
        results["error_message_127"] = str(e)
    
    return results

if __name__ == "__main__":
    print("PostgreSQL Helper - Công cụ kiểm tra kết nối PostgreSQL")
    
    test_results = test_postgres_connection()
    print("\nKết quả kiểm tra kết nối PostgreSQL:")
    print(f"- PostgreSQL container đang chạy: {test_results['container_running']}")
    print(f"- Kết nối với localhost: {'Thành công' if test_results['localhost'] else 'Thất bại'}")
    print(f"- Kết nối với 127.0.0.1: {'Thành công' if test_results['127.0.0.1'] else 'Thất bại'}")
    
    if not (test_results['localhost'] or test_results['127.0.0.1']):
        print("\nGợi ý khắc phục:")
        print("1. Khởi động PostgreSQL container: cd postgre-compose && docker-compose up -d")
        print("2. Kiểm tra log container: docker logs postgres_container")
        print("3. Kiểm tra cấu hình kết nối:")
        print("   - Port đúng là 5433")
        print("   - Username/password là postgres/postgres")
    else:
        print("\nKết nối thành công! Bạn có thể sử dụng PostgreSQL.")
