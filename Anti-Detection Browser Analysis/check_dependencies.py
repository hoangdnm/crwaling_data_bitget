import subprocess
import sys
import os
import importlib.util

def check_package(package_name):
    """Kiểm tra xem gói đã được cài đặt chưa"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name):
    """Cài đặt gói Python"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def check_and_install_dependencies():
    """Kiểm tra và cài đặt các thư viện phụ thuộc cần thiết"""
    dependencies = {
        "selenium": "selenium",
        "webdriver_manager": "webdriver-manager",
        "requests": "requests",
        "fake_useragent": "fake-useragent"
    }
    
    missing_packages = []
    
    print("Đang kiểm tra các thư viện phụ thuộc...")
    for module_name, package_name in dependencies.items():
        if not check_package(module_name):
            missing_packages.append((module_name, package_name))
    
    if missing_packages:
        print("\nCác thư viện sau cần được cài đặt:")
        for module_name, package_name in missing_packages:
            print(f"- {package_name}")
        
        install = input("\nBạn có muốn cài đặt ngay không? (y/n): ")
        if install.lower() == 'y':
            print("\nĐang cài đặt các thư viện cần thiết...")
            for module_name, package_name in missing_packages:
                print(f"Đang cài đặt {package_name}...")
                if install_package(package_name):
                    print(f"✓ Đã cài đặt {package_name}")
                else:
                    print(f"✗ Không thể cài đặt {package_name}")
            
            # Kiểm tra lại sau khi cài đặt
            still_missing = []
            for module_name, package_name in missing_packages:
                if not check_package(module_name):
                    still_missing.append(package_name)
            
            if still_missing:
                print("\nMột số thư viện vẫn chưa được cài đặt. Vui lòng cài đặt thủ công:")
                print(f"pip install {' '.join(still_missing)}")
                return False
            else:
                print("\nTất cả thư viện đã được cài đặt thành công!")
                return True
        else:
            print("\nVui lòng cài đặt thủ công trước khi chạy chương trình:")
            print(f"pip install {' '.join([p[1] for p in missing_packages])}")
            return False
    else:
        print("✓ Tất cả thư viện phụ thuộc đã được cài đặt!")
        return True

if __name__ == "__main__":
    check_and_install_dependencies()
