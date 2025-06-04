from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import os
import sys
import random
import json
import datetime
from pathlib import Path

# Import functions from cấu_tạo.py
from cấu_tạo import delete_profile, rename_profile, backup_profile, restore_profile, show_profile_info
from cấu_tạo import list_profiles, get_profile_directory  # Add this line to import these functions too

# Thêm các thư viện cần thiết để tự động quản lý ChromeDriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService

# Thêm thư viện cho proxy rotation và user-agent
import requests
try:
    from fake_useragent import FakeUserAgent as UserAgent # type: ignore
except ImportError:
    print("Thư viện fake-useragent chưa được cài đặt. Một số tính năng có thể không hoạt động.")
    print("Bạn có thể cài đặt nó bằng lệnh: pip install fake-useragent")
    # Tạo lớp UserAgent giả để tránh lỗi khi thư viện không được cài đặt
    class UserAgent:
        @property
        def random_desktop(self):
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        @property
        def random_mobile(self):
            return "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
        @property
        def random_tablet(self):
            return "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"

# Danh sách User-Agent theo thiết bị
USER_AGENTS = {
    "desktop": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
    ],
    "mobile": [
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1"
    ],
    "tablet": [
        "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 11; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36"
    ]
}

# Timezone danh sách
TIMEZONES = [
    "America/New_York", "America/Los_Angeles", "Europe/London", 
    "Europe/Paris", "Asia/Tokyo", "Asia/Singapore", "Australia/Sydney"
]

# Thư mục cấu hình
CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
PROXY_CONFIG_FILE = os.path.join(CONFIG_DIR, "proxies.json")
USERAGENT_CONFIG_FILE = os.path.join(CONFIG_DIR, "useragents.json")

# Đảm bảo thư mục cấu hình tồn tại
try:
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
except Exception as e:
    print(f"Không thể tạo thư mục cấu hình: {e}")
    print(f"Sử dụng thư mục hiện tại làm thư mục cấu hình...")
    # Redefine config paths without using global
    CONFIG_DIR = os.path.join(os.getcwd(), "config")
    PROXY_CONFIG_FILE = os.path.join(CONFIG_DIR, "proxies.json")
    USERAGENT_CONFIG_FILE = os.path.join(CONFIG_DIR, "useragents.json")
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        print(f"Đã tạo thư mục cấu hình tại: {CONFIG_DIR}")
    except Exception as e2:
        print(f"Vẫn không thể tạo thư mục cấu hình: {e2}")
        print("Chương trình sẽ tiếp tục nhưng không thể lưu cấu hình.")

# Khởi tạo biến global để theo dõi các driver đang mở
driver_pool = []

def cleanup_drivers():
    """Đóng tất cả các driver Chrome đang mở"""
    global driver_pool
    for driver in driver_pool:
        try:
            if driver and driver.service.is_connectable():
                driver.quit()
                print("Đã đóng một phiên Chrome.")
        except Exception:
            pass
    driver_pool = []

# Hàm quản lý proxy
def load_proxies():
    """Tải danh sách proxy từ file cấu hình"""
    if os.path.exists(PROXY_CONFIG_FILE):
        try:
            with open(PROXY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi khi tải danh sách proxy: {str(e)}")
    return {"http": [], "socks5": []}

def save_proxies(proxies):
    """Lưu danh sách proxy vào file cấu hình"""
    try:
        with open(PROXY_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(proxies, f, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu danh sách proxy: {str(e)}")

def get_random_proxy(proxy_type="all"):
    """Lấy một proxy ngẫu nhiên từ danh sách"""
    proxies = load_proxies()
    if proxy_type == "all":
        all_proxies = proxies["http"] + proxies["socks5"]
        return random.choice(all_proxies) if all_proxies else None
    else:
        return random.choice(proxies[proxy_type]) if proxies[proxy_type] else None

def test_proxy(proxy):
    """Kiểm tra xem proxy có hoạt động không"""
    try:
        print(f"Đang kiểm tra proxy {proxy}...")
        proxy_type, proxy_address = proxy.split("://")
        proxy_dict = {proxy_type: proxy}
        
        # Giảm timeout để tránh chờ quá lâu khi proxy không hoạt động
        response = requests.get("https://www.google.com", 
                               proxies=proxy_dict, 
                               timeout=5,
                               headers={"User-Agent": get_random_useragent()})
        
        if response.status_code == 200:
            print("Proxy hoạt động tốt!")
            return True
        else:
            print(f"Proxy trả về mã trạng thái: {response.status_code}")
            return False
    except requests.exceptions.ConnectTimeout:
        print("Kiểm tra proxy thất bại: Kết nối bị timeout")
        return False
    except requests.exceptions.ProxyError:
        print("Kiểm tra proxy thất bại: Lỗi proxy")
        return False 
    except requests.exceptions.RequestException as e:
        print(f"Kiểm tra proxy thất bại: {str(e)}")
        return False
    except Exception as e:
        print(f"Lỗi không xác định khi kiểm tra proxy: {str(e)}")
        return False

def manage_proxies():
    """Menu quản lý proxy"""
    while True:
        print("\n=== QUẢN LÝ PROXY ===")
        print("1. Xem danh sách proxy")
        print("2. Thêm proxy mới")
        print("3. Xóa proxy")
        print("4. Kiểm tra proxy")
        print("5. Nhập danh sách proxy từ file")
        print("0. Quay lại")
        
        choice = input("\nChọn tính năng (nhập số): ")
        try:
            choice = int(choice)
            if choice == 0:
                return
            elif choice == 1:
                # Xem danh sách proxy
                proxies = load_proxies()
                print("\nDanh sách proxy HTTP:")
                for i, proxy in enumerate(proxies["http"]):
                    print(f"{i+1}. {proxy}")
                print("\nDanh sách proxy SOCKS5:")
                for i, proxy in enumerate(proxies["socks5"]):
                    print(f"{i+1}. {proxy}")
                if not proxies["http"] and not proxies["socks5"]:
                    print("Không có proxy nào.")
            elif choice == 2:
                # Thêm proxy mới
                proxies = load_proxies()
                proxy_type = input("\nChọn loại proxy (http/socks5): ").lower()
                if proxy_type not in ["http", "socks5"]:
                    print("Loại proxy không hợp lệ. Chỉ hỗ trợ HTTP và SOCKS5.")
                    continue
                
                proxy = input(f"Nhập địa chỉ proxy {proxy_type.upper()} (định dạng: địa_chỉ:cổng hoặc người_dùng:mật_khẩu@địa_chỉ:cổng): ")
                if not proxy:
                    continue
                
                full_proxy = f"{proxy_type}://{proxy}"
                print(f"Đang kiểm tra proxy {full_proxy}...")
                if test_proxy(full_proxy):
                    proxies[proxy_type].append(full_proxy)
                    save_proxies(proxies)
                    print("Proxy hoạt động và đã được thêm vào danh sách.")
                else:
                    add_anyway = input("Proxy không hoạt động. Bạn có muốn thêm vào danh sách không? (y/n): ")
                    if add_anyway.lower() == 'y':
                        proxies[proxy_type].append(full_proxy)
                        save_proxies(proxies)
                        print("Đã thêm proxy vào danh sách.")
            elif choice == 3:
                # Xóa proxy
                proxies = load_proxies()
                print("\nDanh sách proxy HTTP:")
                for i, proxy in enumerate(proxies["http"]):
                    print(f"{i+1}. {proxy}")
                print("\nDanh sách proxy SOCKS5:")
                for i, proxy in enumerate(proxies["socks5"]):
                    print(f"{i+1}. {proxy}")
                
                if not proxies["http"] and not proxies["socks5"]:
                    print("Không có proxy nào để xóa.")
                    continue
                
                proxy_type = input("\nChọn loại proxy để xóa (http/socks5): ").lower()
                if proxy_type not in ["http", "socks5"]:
                    print("Loại proxy không hợp lệ.")
                    continue
                
                if not proxies[proxy_type]:
                    print(f"Không có proxy {proxy_type.upper()} nào.")
                    continue
                
                index = input(f"Nhập số thứ tự proxy {proxy_type.upper()} cần xóa (1-{len(proxies[proxy_type])}): ")
                try:
                    index = int(index) - 1
                    if 0 <= index < len(proxies[proxy_type]):
                        deleted_proxy = proxies[proxy_type].pop(index)
                        save_proxies(proxies)
                        print(f"Đã xóa proxy: {deleted_proxy}")
                    else:
                        print("Số thứ tự không hợp lệ.")
                except ValueError:
                    print("Vui lòng nhập một số.")
            elif choice == 4:
                # Kiểm tra proxy
                proxies = load_proxies()
                all_proxies = proxies["http"] + proxies["socks5"]
                
                if not all_proxies:
                    print("Không có proxy nào để kiểm tra.")
                    continue
                
                check_all = input("Kiểm tra tất cả các proxy? (y/n): ")
                if check_all.lower() == 'y':
                    print("\nĐang kiểm tra tất cả các proxy...")
                    working = 0
                    for proxy in all_proxies:
                        print(f"Kiểm tra {proxy}...", end=" ")
                        if test_proxy(proxy):
                            print("Hoạt động")
                            working += 1
                        else:
                            print("Không hoạt động")
                    
                    print(f"\nKết quả: {working}/{len(all_proxies)} proxy đang hoạt động.")
                else:
                    proxy_type = input("\nChọn loại proxy để kiểm tra (http/socks5): ").lower()
                    if proxy_type not in ["http", "socks5"]:
                        print("Loại proxy không hợp lệ.")
                        continue
                    
                    if not proxies[proxy_type]:
                        print(f"Không có proxy {proxy_type.upper()} nào.")
                        continue
                    
                    for i, proxy in enumerate(proxies[proxy_type]):
                        print(f"{i+1}. {proxy}")
                    
                    index = input(f"Nhập số thứ tự proxy cần kiểm tra (1-{len(proxies[proxy_type])}): ")
                    try:
                        index = int(index) - 1
                        if 0 <= index < len(proxies[proxy_type]):
                            proxy = proxies[proxy_type][index]
                            print(f"Đang kiểm tra {proxy}...")
                            if test_proxy(proxy):
                                print("Proxy hoạt động.")
                            else:
                                print("Proxy không hoạt động.")
                        else:
                            print("Số thứ tự không hợp lệ.")
                    except ValueError:
                        print("Vui lòng nhập một số.")
            elif choice == 5:
                # Nhập danh sách proxy từ file
                file_path = input("Nhập đường dẫn đến file chứa danh sách proxy: ")
                if not os.path.exists(file_path):
                    print("File không tồn tại.")
                    continue
                
                proxy_type = input("Chọn loại proxy trong file (http/socks5): ").lower()
                if proxy_type not in ["http", "socks5"]:
                    print("Loại proxy không hợp lệ.")
                    continue
                
                try:
                    proxies = load_proxies()
                    count = 0
                    with open(file_path, 'r') as f:
                        for line in f:
                            proxy = line.strip()
                            if proxy:
                                full_proxy = f"{proxy_type}://{proxy}"
                                if full_proxy not in proxies[proxy_type]:
                                    proxies[proxy_type].append(full_proxy)
                                    count += 1
                    
                    save_proxies(proxies)
                    print(f"Đã thêm {count} proxy mới vào danh sách.")
                except Exception as e:
                    print(f"Lỗi khi nhập proxy từ file: {str(e)}")
            else:
                print("Lựa chọn không hợp lệ.")
        except ValueError:
            print("Vui lòng nhập một số.")

# Quản lý User-Agent
def load_useragents():
    """Tải danh sách user-agent tùy chỉnh từ file cấu hình"""
    if os.path.exists(USERAGENT_CONFIG_FILE):
        try:
            with open(USERAGENT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi khi tải danh sách user-agent: {str(e)}")
    return {"desktop": [], "mobile": [], "tablet": []}

def save_useragents(useragents):
    """Lưu danh sách user-agent tùy chỉnh vào file cấu hình"""
    try:
        with open(USERAGENT_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(useragents, f, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu danh sách user-agent: {str(e)}")

def get_random_useragent(device_type="desktop", use_custom=True):
    """Lấy một user-agent ngẫu nhiên theo loại thiết bị"""
    # Xác thực device_type
    if device_type not in ["desktop", "mobile", "tablet"]:
        print(f"Loại thiết bị không hợp lệ: {device_type}. Sử dụng desktop làm mặc định.")
        device_type = "desktop"
        
    try:
        if use_custom:
            custom_useragents = load_useragents()
            if custom_useragents.get(device_type) and len(custom_useragents[device_type]) > 0:
                return random.choice(custom_useragents[device_type])
        
        # Nếu không có user-agent tùy chỉnh hoặc use_custom=False
        if device_type in USER_AGENTS and USER_AGENTS[device_type]:
            return random.choice(USER_AGENTS[device_type])
        
        # Fallback: sử dụng fake_useragent
        try:
            ua = UserAgent()
            if device_type == "mobile":
                return ua.random_mobile
            elif device_type == "tablet":
                return ua.random_tablet
            else:
                return ua.random_desktop
        except Exception as e:
            print(f"Lỗi khi sử dụng fake_useragent: {str(e)}")
            # Fallback to built-in list if fake_useragent fails
            return random.choice(USER_AGENTS["desktop"])
    except Exception as e:
        print(f"Lỗi khi lấy User-Agent ngẫu nhiên: {str(e)}")
        # Final fallback - a common desktop User-Agent
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def manage_useragents():
    """Menu quản lý user-agent"""
    while True:
        print("\n=== QUẢN LÝ USER-AGENT ===")
        print("1. Xem danh sách User-Agent")
        print("2. Thêm User-Agent mới")
        print("3. Xóa User-Agent")
        print("4. Nhập danh sách User-Agent từ file")
        print("0. Quay lại")
        
        choice = input("\nChọn tính năng (nhập số): ")
        try:
            choice = int(choice)
            if choice == 0:
                return
            elif choice == 1:
                # Xem danh sách user-agent
                useragents = load_useragents()
                print("\nDanh sách User-Agent Desktop:")
                for i, ua in enumerate(useragents["desktop"]):
                    print(f"{i+1}. {ua}")
                print("\nDanh sách User-Agent Mobile:")
                for i, ua in enumerate(useragents["mobile"]):
                    print(f"{i+1}. {ua}")
                print("\nDanh sách User-Agent Tablet:")
                for i, ua in enumerate(useragents["tablet"]):
                    print(f"{i+1}. {ua}")
                
                if not useragents["desktop"] and not useragents["mobile"] and not useragents["tablet"]:
                    print("Không có User-Agent tùy chỉnh nào.")
                    print("Sẽ sử dụng User-Agent mặc định.")
            elif choice == 2:
                # Thêm user-agent mới
                useragents = load_useragents()
                device_type = input("\nChọn loại thiết bị (desktop/mobile/tablet): ").lower()
                if device_type not in ["desktop", "mobile", "tablet"]:
                    print("Loại thiết bị không hợp lệ.")
                    continue
                
                ua = input(f"Nhập User-Agent cho thiết bị {device_type}: ")
                if not ua:
                    continue
                
                if ua not in useragents[device_type]:
                    useragents[device_type].append(ua)
                    save_useragents(useragents)
                    print("Đã thêm User-Agent vào danh sách.")
                else:
                    print("User-Agent này đã tồn tại trong danh sách.")
            elif choice == 3:
                # Xóa user-agent
                useragents = load_useragents()
                device_type = input("\nChọn loại thiết bị để xóa User-Agent (desktop/mobile/tablet): ").lower()
                if device_type not in ["desktop", "mobile", "tablet"]:
                    print("Loại thiết bị không hợp lệ.")
                    continue
                
                if not useragents[device_type]:
                    print(f"Không có User-Agent nào cho thiết bị {device_type}.")
                    continue
                
                print(f"\nDanh sách User-Agent cho thiết bị {device_type}:")
                for i, ua in enumerate(useragents[device_type]):
                    print(f"{i+1}. {ua}")
                
                index = input(f"Nhập số thứ tự User-Agent cần xóa (1-{len(useragents[device_type])}): ")
                try:
                    index = int(index) - 1
                    if 0 <= index < len(useragents[device_type]):
                        deleted_ua = useragents[device_type].pop(index)
                        save_useragents(useragents)
                        print(f"Đã xóa User-Agent: {deleted_ua}")
                    else:
                        print("Số thứ tự không hợp lệ.")
                except ValueError:
                    print("Vui lòng nhập một số.")
            elif choice == 4:
                # Nhập danh sách User-Agent từ file
                file_path = input("Nhập đường dẫn đến file chứa danh sách User-Agent: ")
                if not os.path.exists(file_path):
                    print("File không tồn tại.")
                    continue
                
                device_type = input("Chọn loại thiết bị cho User-Agent trong file (desktop/mobile/tablet): ").lower()
                if device_type not in ["desktop", "mobile", "tablet"]:
                    print("Loại proxy không hợp lệ.")
                    continue
                
                try:
                    useragents = load_useragents()
                    count = 0
                    with open(file_path, 'r') as f:
                        for line in f:
                            ua = line.strip()
                            if ua and ua not in useragents[device_type]:
                                useragents[device_type].append(ua)
                                count += 1
                    
                    save_useragents(useragents)
                    print(f"Đã thêm {count} User-Agent mới vào danh sách.")
                except Exception as e:
                    print(f"Lỗi khi nhập User-Agent từ file: {str(e)}")
            else:
                print("Lựa chọn không hợp lệ.")
        except ValueError:
            print("Vui lòng nhập một số.")

# Quản lý Cookie
def manage_cookies(driver=None):
    """Menu quản lý cookie"""
    if driver is None:
        print("Cần mở Chrome trước khi quản lý cookie.")
        return
    
    while True:
        print("\n=== QUẢN LÝ COOKIE ===")
        print("1. Xem tất cả cookie")
        print("2. Xóa tất cả cookie")
        print("3. Xóa cookie theo tên")
        print("4. Xóa cookie theo domain")
        print("5. Xuất cookie ra file")
        print("6. Nhập cookie từ file")
        print("0. Quay lại")
        
        choice = input("\nChọn tính năng (nhập số): ")
        try:
            choice = int(choice)
            if choice == 0:
                return
            elif choice == 1:
                # Xem tất cả cookie
                cookies = driver.get_cookies()
                if not cookies:
                    print("Không có cookie nào.")
                else:
                    print(f"\nTìm thấy {len(cookies)} cookie:")
                    for i, cookie in enumerate(cookies):
                        print(f"{i+1}. {cookie.get('name')} - Domain: {cookie.get('domain')} - Path: {cookie.get('path')}")
                        print(f"   Giá trị: {cookie.get('value')[:30]}{'...' if len(cookie.get('value', '')) > 30 else ''}")
                        print(f"   HttpOnly: {cookie.get('httpOnly', False)} - Secure: {cookie.get('secure', False)}")
                        print(f"   Expires: {datetime.datetime.fromtimestamp(cookie.get('expiry', 0)).strftime('%Y-%m-%d %H:%M:%S') if cookie.get('expiry') else 'Session'}")
                        print()
            elif choice == 2:
                # Xóa tất cả cookie
                confirm = input("Bạn có chắc chắn muốn xóa tất cả cookie? (y/n): ")
                if confirm.lower() == 'y':
                    driver.delete_all_cookies()
                    print("Đã xóa tất cả cookie.")
            elif choice == 3:
                # Xóa cookie theo tên
                cookies = driver.get_cookies()
                if not cookies:
                    print("Không có cookie nào để xóa.")
                    continue
                
                print("\nDanh sách cookie:")
                cookie_names = [cookie.get('name') for cookie in cookies]
                for i, name in enumerate(cookie_names):
                    print(f"{i+1}. {name}")
                
                name = input("\nNhập tên cookie cần xóa (hoặc số thứ tự): ")
                try:
                    index = int(name) - 1
                    if 0 <= index < len(cookie_names):
                        name = cookie_names[index]
                except ValueError:
                    pass
                
                if name in cookie_names:
                    driver.delete_cookie(name)
                    print(f"Đã xóa cookie: {name}")
                else:
                    print(f"Không tìm thấy cookie có tên: {name}")
            elif choice == 4:
                # Xóa cookie theo domain
                cookies = driver.get_cookies()
                if not cookies:
                    print("Không có cookie nào để xóa.")
                    continue
                
                domains = set(cookie.get('domain') for cookie in cookies)
                print("\nDanh sách domain:")
                domain_list = list(domains)
                for i, domain in enumerate(domain_list):
                    print(f"{i+1}. {domain}")
                
                domain_input = input("\nNhập domain cần xóa cookie (hoặc số thứ tự): ")
                try:
                    index = int(domain_input) - 1
                    if 0 <= index < len(domain_list):
                        domain = domain_list[index]
                    else:
                        print("Số thứ tự không hợp lệ.")
                        continue
                except ValueError:
                    domain = domain_input
                
                if domain not in domains:
                    print(f"Không tìm thấy cookie cho domain: {domain}")
                    continue
                
                count = 0
                for cookie in list(cookies):  # Create a copy to avoid issues when deleting
                    if cookie.get('domain') == domain:
                        driver.delete_cookie(cookie.get('name'))
                        count += 1
                
                print(f"Đã xóa {count} cookie thuộc domain {domain}.")
            elif choice == 5:
                # Xuất cookie ra file
                cookies = driver.get_cookies()
                if not cookies:
                    print("Không có cookie nào để xuất.")
                    continue
                
                file_path = input("Nhập đường dẫn file để lưu cookie (mặc định: cookies.json): ")
                if not file_path:
                    file_path = "cookies.json"
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, indent=4)
                    print(f"Đã xuất {len(cookies)} cookie ra file: {file_path}")
                except Exception as e:
                    print(f"Lỗi khi xuất cookie: {str(e)}")
            elif choice == 6:
                # Nhập cookie từ file
                file_path = input("Nhập đường dẫn file cookie (mặc định: cookies.json): ")
                if not file_path:
                    file_path = "cookies.json"
                
                if not os.path.exists(file_path):
                    print(f"File không tồn tại: {file_path}")
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                    
                    if not isinstance(cookies, list):
                        print("Định dạng file cookie không hợp lệ.")
                        continue
                    
                    count = 0
                    for cookie in cookies:
                        try:
                            # Loại bỏ trường expiry nếu nó là None
                            if 'expiry' in cookie and cookie['expiry'] is None:
                                del cookie['expiry']
                            
                            driver.add_cookie(cookie)
                            count += 1
                        except Exception as e:
                            print(f"Lỗi khi thêm cookie: {str(e)}")
                    
                    print(f"Đã thêm {count}/{len(cookies)} cookie từ file.")
                except Exception as e:
                    print(f"Lỗi khi nhập cookie: {str(e)}")
            else:
                print("Lựa chọn không hợp lệ.")
        except ValueError:
            print("Vui lòng nhập một số.")
        except Exception as e:
            print(f"Lỗi: {str(e)}")

def get_profile_directory(profile_name):
    """Trả về đường dẫn thư mục profile dựa theo tên profile"""
    base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Google", "Chrome", "User Data")
    return os.path.join(base_dir, profile_name)

def list_profiles():
    """Liệt kê các profile hiện có"""
    base_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Google", "Chrome", "User Data")
    profiles = []
    
    # Kiểm tra xem thư mục Chrome User Data có tồn tại không
    if not os.path.exists(base_dir):
        print(f"Thư mục Chrome User Data không tồn tại tại: {base_dir}")
        return profiles
    
    # Tìm các thư mục profile (bắt đầu bằng "Profile " hoặc là "Default")
    for item in os.listdir(base_dir):
        if item == "Default" or item.startswith("Profile "):
            profiles.append(item)
    
    return profiles

def select_profile():
    """Hiển thị menu chọn profile hoặc tạo profile mới"""
    profiles = list_profiles()
    
    print("\n=== QUẢN LÝ PROFILE CHROME ===")
    if not profiles:
        print("Không tìm thấy profile nào.")
    else:
        print("Các profile hiện có:")
        for i, profile in enumerate(profiles):
            print(f"{i+1}. {profile}")
    
    print(f"{len(profiles)+1}. Tạo profile mới")
    print("0. Thoát")
    
    choice = input("\nChọn profile (nhập số): ")
    try:
        choice = int(choice)
        if choice == 0:
            sys.exit(0)
        elif 1 <= choice <= len(profiles):
            return profiles[choice-1]
        elif choice == len(profiles)+1:
            new_profile = create_new_profile()
            return new_profile
        else:
            print("Lựa chọn không hợp lệ.")
            return select_profile()
    except ValueError:
        print("Vui lòng nhập một số.")
        return select_profile()

def create_new_profile():
    """Tạo profile mới"""
    profiles = list_profiles()
    
    # Tìm số profile tiếp theo
    profile_numbers = [int(p.split(" ")[1]) for p in profiles if p.startswith("Profile ") and p.split(" ")[1].isdigit()]
    next_number = max(profile_numbers) + 1 if profile_numbers else 1
    
    new_profile = f"Profile {next_number}"
    print(f"\nĐã tạo profile mới: {new_profile}")
    return new_profile

def launch_chrome_with_profile(profile_name, url=None, proxy=None, anti_fingerprint=False, 
                              custom_useragent=None, device_type="desktop"):
    """Khởi chạy Chrome với profile và tùy chọn nâng cao được chỉ định"""
    try:
        profile_directory = get_profile_directory(profile_name)
        
        # Cập nhật đường dẫn Chrome
        chrome_binary = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        
        # Kiểm tra xem Chrome có tồn tại không
        if not os.path.exists(chrome_binary):
            print(f"Lỗi: Chrome không tồn tại tại đường dẫn: {chrome_binary}")
            return None
        
        # Khởi tạo tùy chọn cho Chrome
        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = chrome_binary
        
        # Các tùy chọn cơ bản
        chrome_options.add_experimental_option("detach", True)
        chrome_options.add_argument(f'--user-data-dir={profile_directory}')
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        
        # Thiết lập proxy nếu được chỉ định
        if proxy:
            chrome_options.add_argument(f'--proxy-server={proxy}')
            print(f"Đã thiết lập proxy: {proxy}")
        
        # Thiết lập User-Agent nếu được chỉ định
        if custom_useragent:
            chrome_options.add_argument(f'--user-agent={custom_useragent}')
            print(f"Đã thiết lập User-Agent: {custom_useragent}")
        else:
            # Sử dụng User-Agent ngẫu nhiên theo loại thiết bị
            random_ua = get_random_useragent(device_type)
            chrome_options.add_argument(f'--user-agent={random_ua}')
            print(f"Đã thiết lập User-Agent ngẫu nhiên: {random_ua}")
        
        # Chống fingerprinting nếu được yêu cầu
        if anti_fingerprint:
            # Chặn Canvas Fingerprinting
            chrome_options.add_argument("--disable-reading-from-canvas")
            
            # Chặn WebGL Fingerprinting
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-gpu")
            
            # Chặn WebRTC IP Leak
            chrome_options.add_argument("--disable-webrtc-encryption")
            chrome_options.add_argument("--disable-webrtc-hw-encoding")
            chrome_options.add_argument("--disable-webrtc-hw-decoding")
            chrome_options.add_argument("--enforce-webrtc-ip-permission-check")
            
            # Chọn múi giờ ngẫu nhiên
            random_timezone = random.choice(TIMEZONES)
            chrome_options.add_argument(f"--timezone={random_timezone}")
            print(f"Đã thiết lập múi giờ ngẫu nhiên: {random_timezone}")
            
            print("Đã bật chế độ chống fingerprinting nâng cao.")
        
        # Thiết lập các tùy chọn khác
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--password-store=basic")

        # Thiết lập các tùy chọn nâng cao
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })

        try:
            print("Đang tự động tải ChromeDriver phù hợp...")
            # Sử dụng webdriver-manager để tự động tải ChromeDriver đúng phiên bản
            service = ChromeService(ChromeDriverManager().install())
            
            print("Đang khởi động Chrome...")
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Thêm một khoảng dừng ngắn để đảm bảo Chrome đã khởi động đầy đủ
            time.sleep(2)
            
            # Thêm JavaScript để vô hiệu hóa fingerprinting nếu cần
            if anti_fingerprint:
                try:
                    anti_fingerprint_js = """
                    // Ghi đè canvas fingerprinting
                    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = function(type) {
                        if (this.width > 16 && this.height > 16) {
                            return originalToDataURL.apply(this, [type]);
                        }
                    };
                    
                    // Ghi đè webgl fingerprinting
                    const getParameterProto = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        // Giả mạo dữ liệu WebGL
                        if (parameter === 37445) {
                            return 'Intel Open Source Technology Center';
                        }
                        if (parameter === 37446) {
                            return 'Mesa DRI Intel(R) HD Graphics 520 (Skylake GT2)';
                        }
                        return getParameterProto.apply(this, arguments);
                    };
                    """
                    driver.execute_script(anti_fingerprint_js)
                except Exception as e:
                    print(f"Cảnh báo: Không thể thực thi script chống fingerprinting: {str(e)}")
            
            if url:
                print(f"Đang điều hướng đến {url}")
                driver.get(url)
                
            driver.maximize_window()
            
            # Kiểm tra xem Chrome có đang chạy không
            if driver.service.is_connectable():
                print("Chrome đã khởi động thành công")
            else:
                print("Chrome đã khởi động nhưng không thể kết nối")
                
            return driver
        except Exception as e:
            print(f"Lỗi khi khởi tạo Chrome: {str(e)}")
            
            # Thử phương pháp thay thế nếu webdriver-manager không hoạt động
            print("\nĐang thử phương pháp thay thế...")
            print("Vui lòng tải ChromeDriver phù hợp với phiên bản Chrome của bạn từ:")
            print("https://chromedriver.chromium.org/downloads")
            
            chromedriver_path = input("Nhập đường dẫn đến ChromeDriver mới: ")
            if os.path.exists(chromedriver_path):
                try:
                    service = Service(executable_path=chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    time.sleep(2)
                    
                    if url:
                        print(f"Đang điều hướng đến {url}")
                        driver.get(url)
                    
                    driver.maximize_window()
                    return driver
                except Exception as e2:
                    print(f"Vẫn không thể khởi động Chrome: {str(e2)}")
                    import traceback
                    print(traceback.format_exc())
                    return None
            else:
                print(f"Đường dẫn không hợp lệ: {chromedriver_path}")
                return None
            
    except Exception as e:
        print(f"Lỗi: {str(e)}")
        return None

# Hàm mở Chrome nâng cao với tùy chọn bổ sung
def open_chrome_advanced():
    """Mở Chrome với các tùy chọn nâng cao (proxy, anti-fingerprint, user-agent)"""
    # Chọn profile
    selected_profile = select_profile()
    if not selected_profile:
        return None
    
    # Tùy chọn URL
    open_url = input("\nNhập URL muốn mở (Enter để bỏ qua): ")
    url_to_open = open_url if open_url.strip() else None
    
    # Tùy chọn proxy
    use_proxy = input("\nSử dụng proxy? (y/n): ").lower() == 'y'
    proxy = None
    if use_proxy:
        proxy_type = input("Chọn loại proxy (http/socks5/random): ").lower()
        if proxy_type in ["http", "socks5"]:
            proxy = get_random_proxy(proxy_type)
        else:
            proxy = get_random_proxy()
        
        if not proxy:
            print("Không tìm thấy proxy. Tiếp tục không có proxy.")
            add_proxy = input("Bạn có muốn thêm proxy mới không? (y/n): ").lower()
            if add_proxy == 'y':
                manage_proxies()
                return open_chrome_advanced()
    
    # Tùy chọn Anti-fingerprinting
    anti_fingerprint = input("\nBật chế độ chống fingerprinting? (y/n): ").lower() == 'y'
    
    # Tùy chọn User-Agent
    custom_ua = None
    device_type = "desktop"
    custom_ua_option = input("\nTùy chỉnh User-Agent? (y/n): ").lower()
    if custom_ua_option == 'y':
        ua_option = input("1. Chọn từ danh sách\n2. Ngẫu nhiên theo thiết bị\n3. Nhập thủ công\nChọn (1-3): ")
        if ua_option == '1':
            useragents = load_useragents()
            all_uas = []
            for device in ["desktop", "mobile", "tablet"]:
                all_uas.extend([(device, ua) for ua in useragents[device]])
            
            if not all_uas:
                print("Không có User-Agent nào trong danh sách tùy chỉnh.")
                random_type = input("Chọn loại thiết bị cho User-Agent ngẫu nhiên (desktop/mobile/tablet): ").lower()
                if random_type in ["desktop", "mobile", "tablet"]:
                    device_type = random_type
                else:
                    print("Loại thiết bị không hợp lệ. Sử dụng desktop làm mặc định.")
            else:
                print("\nDanh sách User-Agent:")
                for i, (device, ua) in enumerate(all_uas):
                    print(f"{i+1}. [{device}] {ua[:50]}...")
                
                ua_index = input(f"Chọn User-Agent (1-{len(all_uas)}): ")
                try:
                    ua_index = int(ua_index) - 1
                    if 0 <= ua_index < len(all_uas):
                        device_type, custom_ua = all_uas[ua_index]
                    else:
                        print("Số thứ tự không hợp lệ. Sử dụng User-Agent ngẫu nhiên.")
                except ValueError:
                    print("Vui lòng nhập một số. Sử dụng User-Agent ngẫu nhiên.")
        elif ua_option == '2':
            device_type = input("Chọn loại thiết bị (desktop/mobile/tablet): ").lower()
            if device_type not in ["desktop", "mobile", "tablet"]:
                print("Loại thiết bị không hợp lệ. Sử dụng desktop làm mặc định.")
                device_type = "desktop"
        elif ua_option == '3':
            custom_ua = input("Nhập User-Agent tùy chỉnh: ")
            if not custom_ua:
                print("User-Agent không hợp lệ. Sử dụng User-Agent ngẫu nhiên.")
                custom_ua = None
        else:
            print("Lựa chọn không hợp lệ. Sử dụng User-Agent ngẫu nhiên theo desktop.")
    
    # Khởi động Chrome với các tùy chọn đã chọn
    driver = launch_chrome_with_profile(
        selected_profile, 
        url=url_to_open, 
        proxy=proxy, 
        anti_fingerprint=anti_fingerprint,
        custom_useragent=custom_ua,
        device_type=device_type
    )
    
    return driver

def manage_profiles():
    """Menu quản lý profile chính"""
    global driver_pool  # Đặt khai báo global ở đầu hàm
    
    # Khởi tạo biến để theo dõi driver hiện tại
    current_driver = None
    
    while True:
        print("\n=== QUẢN LÝ PROFILE CHROME ===")
        print("1. Mở Chrome với profile")
        print("2. Mở Chrome nâng cao (proxy, anti-fingerprint, user-agent)")
        print("3. Tạo profile mới")
        print("4. Xóa profile")
        print("5. Đổi tên profile")
        print("6. Sao lưu profile")
        print("7. Khôi phục profile")
        print("8. Xem thông tin profile")
        print("9. Quản lý proxy")
        print("10. Quản lý User-Agent")
        print("11. Quản lý cookie")
        print("0. Thoát")
        
        choice = input("\nChọn tính năng (nhập số): ")
        try:
            choice = int(choice)
            if choice == 0:
                print("Đang đóng tất cả các phiên Chrome...")
                cleanup_drivers()
                print("Tạm biệt!")
                return
            elif choice == 1:
                # Mở Chrome với profile
                selected_profile = select_profile()
                if selected_profile:
                    open_url = input("\nNhập URL muốn mở (Enter để bỏ qua): ")
                    url_to_open = open_url if open_url.strip() else None
                    driver = launch_chrome_with_profile(selected_profile, url_to_open)
                    
                    # Kiểm tra xem driver có được tạo thành công không
                    if driver:
                        # Thêm driver vào pool và thiết lập làm driver hiện tại
                        driver_pool.append(driver)
                        current_driver = driver
                        
                        print(f"Chrome đã mở với profile: {selected_profile}")
                        
                        # Giữ cho script chạy nếu cần
                        try:
                            while True:
                                cmd = input("\nNhập 'quit' để đóng trình duyệt, 'exit' để thoát, 'back' để quay lại menu, 'cookie' để quản lý cookie: ")
                                if cmd.lower() == 'quit':
                                    driver.quit()
                                    driver_pool.remove(driver)
                                    current_driver = None
                                    print("Đã đóng trình duyệt.")
                                    break
                                elif cmd.lower() == 'exit':
                                    cleanup_drivers()
                                    current_driver = None
                                    print("Đã thoát chương trình.")
                                    return
                                elif cmd.lower() == 'back':
                                    print("Quay lại menu chính.")
                                    break
                                elif cmd.lower() == 'cookie':
                                    manage_cookies(driver)
                        except Exception as e:
                            print(f"Lỗi trong vòng lặp lệnh: {str(e)}")
                            try:
                                driver.quit()
                                if driver in driver_pool:
                                    driver_pool.remove(driver)
                                current_driver = None
                            except Exception:
                                pass
                    else:
                        print("Không thể khởi động Chrome. Vui lòng kiểm tra lại cài đặt và thử lại.")
            elif choice == 2:
                # Mở Chrome nâng cao
                driver = open_chrome_advanced()
                if driver:
                    # Thêm driver vào pool và thiết lập làm driver hiện tại
                    driver_pool.append(driver)
                    current_driver = driver
                    
                    # Giữ cho script chạy nếu cần
                    try:
                        while True:
                            cmd = input("\nNhập 'quit' để đóng trình duyệt, 'exit' để thoát, 'back' để quay lại menu, 'cookie' để quản lý cookie: ")
                            if cmd.lower() == 'quit':
                                driver.quit()
                                driver_pool.remove(driver)
                                current_driver = None
                                print("Đã đóng trình duyệt.")
                                break
                            elif cmd.lower() == 'exit':
                                cleanup_drivers()
                                current_driver = None
                                print("Đã thoát chương trình.")
                                return
                            elif cmd.lower() == 'back':
                                print("Quay lại menu chính.")
                                break
                            elif cmd.lower() == 'cookie':
                                manage_cookies(driver)
                    except Exception as e:
                        print(f"Lỗi trong vòng lặp lệnh: {str(e)}")
                        try:
                            driver.quit()
                            if driver in driver_pool:
                                driver_pool.remove(driver)
                            current_driver = None
                        except Exception:
                            pass
                else:
                    print("Không thể khởi động Chrome. Vui lòng kiểm tra lại cài đặt và thử lại.")
            elif choice == 3:
                create_new_profile()
            elif choice == 4:
                delete_profile()
            elif choice == 5:
                rename_profile()
            elif choice == 6:
                backup_profile()
            elif choice == 7:
                restore_profile()
            elif choice == 8:
                show_profile_info()
            elif choice == 9:
                manage_proxies()
            elif choice == 10:
                manage_useragents()
            elif choice == 11:
                if current_driver and current_driver.service.is_connectable():
                    manage_cookies(current_driver)
                else:
                    print("Không có phiên Chrome nào đang mở. Vui lòng mở Chrome trước.")
            else:
                print("Lựa chọn không hợp lệ.")
        except ValueError:
            print("Vui lòng nhập một số.")
        except KeyboardInterrupt:
            print("\nChương trình đã bị ngắt bởi người dùng.")
            cleanup_drivers()
            current_driver = None
            return
        except Exception as e:
            print(f"Lỗi: {str(e)}")
            # Tiếp tục vòng lặp để người dùng có thể thử lại

# Chương trình chính
if __name__ == "__main__":
    try:
        # Kiểm tra các thư viện cần thiết
        missing_packages = []
        
        try:
            import selenium
        except ImportError:
            missing_packages.append("selenium")
            
        try:
            import webdriver_manager
        except ImportError:
            missing_packages.append("webdriver-manager")
        
        if missing_packages:
            print("\n=== THIẾU THƯ VIỆN PYTHON ===")
            print("Các thư viện sau cần được cài đặt:")
            for pkg in missing_packages:
                print(f"- {pkg}")
            print("\nVui lòng cài đặt bằng lệnh:")
            print(f"pip install {' '.join(missing_packages)}")
            
            install = input("\nBạn có muốn tự động cài đặt ngay bây giờ? (y/n): ")
            if install.lower() == 'y':
                import subprocess
                try:
                    print("\nĐang cài đặt các thư viện cần thiết...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                    print("Cài đặt thành công! Khởi động lại chương trình...")
                    # Khởi động lại chương trình
                    os.execv(sys.executable, ['python'] + sys.argv)
                except Exception as e:
                    print(f"Lỗi khi cài đặt: {e}")
                    print("Vui lòng cài đặt thủ công và chạy lại chương trình.")
                    sys.exit(1)
            else:
                print("Vui lòng cài đặt thủ công và chạy lại chương trình.")
                sys.exit(1)
        
        # Chạy chương trình chính
        manage_profiles()
    except KeyboardInterrupt:
        print("\nChương trình đã bị ngắt bởi người dùng.")
        cleanup_drivers()
    except Exception as e:
        print(f"Lỗi không xử lý được: {str(e)}")
        import traceback
        print(traceback.format_exc())  # In ra chi tiết lỗi để dễ gỡ lỗi
        cleanup_drivers()
    finally:
        print("Chương trình đã kết thúc.")
