import requests

# Địa chỉ API Java (Backend)
BASE_URL = "http://localhost:8080/api"

def get_all_folders():
    """Lấy danh sách các đề tài/thư mục """
    try:
        response = requests.get(f"{BASE_URL}/folders")
        if response.status_code == 200:
            return response.json() # Trả về danh sách folder (id, name...)
        return []
    except Exception as e:
        print(f"Lỗi lấy danh sách folder: {e}")
        return []

def create_new_folder(name, description=""):
    """Gửi yêu cầu tạo thư mục mới """
    try:
        # Gửi dữ liệu dưới dạng Form Data
        params = {'name': name, 'desc': description}
        response = requests.post(f"{BASE_URL}/folders", params=params)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi tạo folder: {e}")
        return False

def upload_file_to_java(uploaded_file, folder_id=None):
    """Gửi file + ID thư mục """
    try:
        files = {
            'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        data = {}
        # Nếu người dùng chọn folder, gửi kèm folderId
        if folder_id:
            data['folderId'] = folder_id
            
        response = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi upload file: {e}")
        return False