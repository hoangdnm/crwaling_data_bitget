import os
import datetime
import shutil
import zipfile

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

def delete_profile():
    """Xóa một profile Chrome"""
    profiles = list_profiles()
    
    if not profiles:
        print("Không tìm thấy profile nào để xóa.")
        return
    
    print("\nCác profile hiện có:")
    for i, profile in enumerate(profiles):
        print(f"{i+1}. {profile}")
    
    choice = input("\nChọn profile cần xóa (nhập số), hoặc 0 để hủy: ")
    try:
        choice = int(choice)
        if choice == 0:
            return
        elif 1 <= choice <= len(profiles):
            profile_to_delete = profiles[choice-1]
            
            confirm = input(f"Bạn có chắc chắn muốn xóa profile '{profile_to_delete}'? (y/n): ")
            if confirm.lower() != 'y':
                print("Đã hủy thao tác xóa.")
                return
            
            try:
                import shutil
                profile_path = get_profile_directory(profile_to_delete)
                
                # Kiểm tra xem thư mục có tồn tại không
                if not os.path.exists(profile_path):
                    print(f"Không tìm thấy thư mục profile: {profile_path}")
                    return
                
                # Xóa thư mục profile
                shutil.rmtree(profile_path)
                print(f"Đã xóa profile: {profile_to_delete}")
            except Exception as e:
                print(f"Lỗi khi xóa profile: {str(e)}")
        else:
            print("Lựa chọn không hợp lệ.")
    except ValueError:
        print("Vui lòng nhập một số.")

def rename_profile():
    """Đổi tên một profile Chrome"""
    profiles = list_profiles()
    
    if not profiles:
        print("Không tìm thấy profile nào để đổi tên.")
        return
    
    print("\nCác profile hiện có:")
    for i, profile in enumerate(profiles):
        print(f"{i+1}. {profile}")
    
    choice = input("\nChọn profile cần đổi tên (nhập số), hoặc 0 để hủy: ")
    try:
        choice = int(choice)
        if choice == 0:
            return
        elif 1 <= choice <= len(profiles):
            old_profile = profiles[choice-1]
            
            # Không cho phép đổi tên profile Default
            if old_profile == "Default":
                print("Không thể đổi tên profile mặc định (Default).")
                return
            
            # Chỉ cho phép đổi tên các profile định dạng "Profile X"
            if not old_profile.startswith("Profile "):
                print("Chỉ có thể đổi tên các profile có định dạng 'Profile X'.")
                return
            
            new_name = input("Nhập tên mới cho profile (phải có định dạng 'Profile X'): ")
            if not new_name.startswith("Profile "):
                print("Tên profile mới phải có định dạng 'Profile X'.")
                return
            
            if new_name in profiles:
                print(f"Profile có tên '{new_name}' đã tồn tại.")
                return
            
            try:
                import shutil
                old_path = get_profile_directory(old_profile)
                new_path = get_profile_directory(new_name)
                
                # Kiểm tra xem thư mục cũ có tồn tại không
                if not os.path.exists(old_path):
                    print(f"Không tìm thấy thư mục profile: {old_path}")
                    return
                
                # Kiểm tra xem thư mục mới đã tồn tại chưa
                if os.path.exists(new_path):
                    print(f"Thư mục profile mới đã tồn tại: {new_path}")
                    return
                
                # Di chuyển thư mục profile
                shutil.move(old_path, new_path)
                print(f"Đã đổi tên profile từ '{old_profile}' thành '{new_name}'")
            except Exception as e:
                print(f"Lỗi khi đổi tên profile: {str(e)}")
        else:
            print("Lựa chọn không hợp lệ.")
    except ValueError:
        print("Vui lòng nhập một số.")

def backup_profile():
    """Sao lưu một profile Chrome"""
    profiles = list_profiles()
    
    if not profiles:
        print("Không tìm thấy profile nào để sao lưu.")
        return
    
    print("\nCác profile hiện có:")
    for i, profile in enumerate(profiles):
        print(f"{i+1}. {profile}")
    
    choice = input("\nChọn profile cần sao lưu (nhập số), hoặc 0 để hủy: ")
    try:
        choice = int(choice)
        if choice == 0:
            return
        elif 1 <= choice <= len(profiles):
            profile_to_backup = profiles[choice-1]
            
            # Tạo thư mục sao lưu nếu chưa tồn tại
            backup_dir = os.path.join(os.path.expanduser("~"), "ChromeProfileBackups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Tạo tên file sao lưu với timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{profile_to_backup.replace(' ', '_')}_{timestamp}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            print(f"Đang sao lưu profile '{profile_to_backup}'...")
            profile_path = get_profile_directory(profile_to_backup)
            
            try:
                import shutil
                
                # Kiểm tra xem thư mục có tồn tại không
                if not os.path.exists(profile_path):
                    print(f"Không tìm thấy thư mục profile: {profile_path}")
                    return
                
                # Tạo file ZIP từ thư mục profile
                shutil.make_archive(backup_path[:-4], 'zip', profile_path)
                print(f"Đã sao lưu profile vào: {backup_path}")
            except Exception as e:
                print(f"Lỗi khi sao lưu profile: {str(e)}")
        else:
            print("Lựa chọn không hợp lệ.")
    except ValueError:
        print("Vui lòng nhập một số.")

def restore_profile():
    """Khôi phục một profile Chrome từ bản sao lưu"""
    # Tìm thư mục sao lưu
    backup_dir = os.path.join(os.path.expanduser("~"), "ChromeProfileBackups")
    if not os.path.exists(backup_dir):
        print("Không tìm thấy thư mục sao lưu profile.")
        return
    
    # Liệt kê các file sao lưu
    backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.zip')]
    if not backup_files:
        print("Không tìm thấy file sao lưu nào.")
        return
    
    print("\nCác bản sao lưu hiện có:")
    for i, backup in enumerate(backup_files):
        print(f"{i+1}. {backup}")
    
    choice = input("\nChọn bản sao lưu cần khôi phục (nhập số), hoặc 0 để hủy: ")
    try:
        choice = int(choice)
        if choice == 0:
            return
        elif 1 <= choice <= len(backup_files):
            backup_to_restore = backup_files[choice-1]
            backup_path = os.path.join(backup_dir, backup_to_restore)
            
            # Xử lý tên profile từ tên file sao lưu
            try:
                profile_name = backup_to_restore.split('_')[0].replace('_', ' ')
                if not profile_name.startswith("Profile") and profile_name != "Default":
                    profile_name = "Profile " + profile_name
            except:
                profile_name = input("Không thể xác định tên profile từ file sao lưu. Nhập tên profile (vd: Profile 1): ")
            
            # Kiểm tra xem profile đã tồn tại chưa
            if profile_name in list_profiles():
                overwrite = input(f"Profile '{profile_name}' đã tồn tại. Ghi đè? (y/n): ")
                if overwrite.lower() != 'y':
                    new_name = input("Nhập tên mới cho profile (vd: Profile 5): ")
                    profile_name = new_name
            
            profile_path = get_profile_directory(profile_name)
            
            try:
                import shutil
                
                # Tạo thư mục profile nếu chưa tồn tại
                os.makedirs(profile_path, exist_ok=True)
                
                # Giải nén file sao lưu vào thư mục profile
                import zipfile
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    zip_ref.extractall(profile_path)
                
                print(f"Đã khôi phục profile '{profile_name}' thành công.")
            except Exception as e:
                print(f"Lỗi khi khôi phục profile: {str(e)}")
        else:
            print("Lựa chọn không hợp lệ.")
    except ValueError:
        print("Vui lòng nhập một số.")

def show_profile_info():
    """Hiển thị thông tin chi tiết về một profile Chrome"""
    profiles = list_profiles()
    
    if not profiles:
        print("Không tìm thấy profile nào.")
        return
    
    print("\nCác profile hiện có:")
    for i, profile in enumerate(profiles):
        print(f"{i+1}. {profile}")
    
    choice = input("\nChọn profile để xem thông tin (nhập số), hoặc 0 để hủy: ")
    try:
        choice = int(choice)
        if choice == 0:
            return
        elif 1 <= choice <= len(profiles):
            profile_name = profiles[choice-1]
            profile_path = get_profile_directory(profile_name)
            
            if not os.path.exists(profile_path):
                print(f"Không tìm thấy thư mục profile: {profile_path}")
                return
            
            print(f"\n=== THÔNG TIN PROFILE: {profile_name} ===")
            print(f"Đường dẫn: {profile_path}")
            
            # Kiểm tra kích thước thư mục
            try:
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(profile_path):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp)
                
                # Chuyển đổi kích thước sang MB
                size_mb = total_size / (1024 * 1024)
                print(f"Kích thước: {size_mb:.2f} MB")
            except Exception as e:
                print(f"Không thể tính kích thước: {str(e)}")
            
            # Kiểm tra thời gian chỉnh sửa cuối cùng
            try:
                last_modified = os.path.getmtime(profile_path)
                last_modified_date = datetime.datetime.fromtimestamp(last_modified)
                print(f"Chỉnh sửa lần cuối: {last_modified_date.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                print(f"Không thể xác định thời gian chỉnh sửa: {str(e)}")
            
            # Liệt kê các file cookies và lịch sử
            cookies_file = os.path.join(profile_path, "Network", "Cookies")
            history_file = os.path.join(profile_path, "History")
            
            print("\nCác file quan trọng:")
            if os.path.exists(cookies_file):
                print(f"- Cookies: Có")
            else:
                print(f"- Cookies: Không tìm thấy")
            
            if os.path.exists(history_file):
                print(f"- History: Có")
            else:
                print(f"- History: Không tìm thấy")
            
            # Kiểm tra các extension đã cài đặt
            extensions_path = os.path.join(profile_path, "Extensions")
            if os.path.exists(extensions_path):
                try:
                    extensions = os.listdir(extensions_path)
                    print(f"\nSố lượng extensions: {len(extensions)}")
                except Exception as e:
                    print(f"Không thể đọc thông tin extensions: {str(e)}")
            else:
                print("\nKhông tìm thấy thư mục Extensions")
        else:
            print("Lựa chọn không hợp lệ.")
    except ValueError:
        print("Vui lòng nhập một số.")