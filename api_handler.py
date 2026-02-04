import requests

# Địa chỉ API Backend
BASE_URL = "http://localhost:8080/api"


#XỬ LÝ USER 
def login(username, password):
    """Gửi yêu cầu đăng nhập"""
    try:
        data = {"username": username, "password": password}
        response = requests.post(f"{BASE_URL}/users/login", json=data)
        if response.status_code == 200:
            return response.json() 
        return None
    except Exception as e:
        print(f"Lỗi login: {e}")
        return None

def register(username, password):
    """Gửi yêu cầu đăng ký"""
    try:
        data = {"username": username, "password": password}
        response = requests.post(f"{BASE_URL}/users/register", json=data)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Lỗi register: {e}")
        return None

# XỬ LÝ FOLDER 
def get_all_folders(user_id):
    """Lấy danh sách folder của RIÊNG user đó"""
    try:
        response = requests.get(f"{BASE_URL}/folders?userId={user_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Lỗi lấy danh sách folder: {e}")
        return []

def create_new_folder(name, description, user_id):
    """Tạo folder mới gắn với user_id"""
    try:
        params = {'name': name, 'desc': description, 'userId': user_id}
        response = requests.post(f"{BASE_URL}/folders", params=params)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi tạo folder: {e}")
        return False

def update_folder(folder_id, new_name, new_desc=""):
    """Cập nhật tên/mô tả folder"""
    try:
        params = {'name': new_name, 'desc': new_desc}
        response = requests.put(f"{BASE_URL}/folders/{folder_id}", params=params)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi update folder: {e}")
        return False

def delete_folder(folder_id):
    """Xóa folder"""
    try:
        response = requests.delete(f"{BASE_URL}/folders/{folder_id}")
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi delete folder: {e}")
        return False

# XỬ LÝ DOCUMENT & CHAT
def upload_file_to_java(uploaded_file, folder_id=None, extracted_text=""):
    try:
        files = {
            'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)
        }
        data = {'extractedText': extracted_text}
        if folder_id:
            data['folderId'] = folder_id
            
        response = requests.post(f"{BASE_URL}/documents/upload", files=files, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi upload file: {e}")
        return False

def get_folder_context(folder_id):
    try:
        if not folder_id: return ""
        response = requests.get(f"{BASE_URL}/documents/folder/{folder_id}/context")
        if response.status_code == 200:
            return response.text
        return ""
    except Exception as e:
        print(f"Lỗi lấy context: {e}")
        return ""

def get_files_in_folder(folder_id):
    try:
        response = requests.get(f"{BASE_URL}/documents/folder/{folder_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Lỗi lấy danh sách file: {e}")
        return []

def delete_file(file_id):
    try:
        response = requests.delete(f"{BASE_URL}/documents/{file_id}")
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi xóa file: {e}")
        return False

def get_chat_history(folder_id):
    try:
        response = requests.get(f"{BASE_URL}/chat/history/{folder_id}")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Lỗi lấy lịch sử chat: {e}")
        return []

def save_chat_message(folder_id, role, content, optimized_prompt=None):
    """Gửi yêu cầu lưu tin nhắn kèm Prompt tối ưu (nếu có) sang Backend Java"""
    try:
        data = {
            "folderId": folder_id, 
            "role": role, 
            "content": content,
            "optimizedPrompt": optimized_prompt
        }
        requests.post(f"{BASE_URL}/chat/save", json=data)
        return True
    except Exception as e:
        print(f"Lỗi lưu tin nhắn: {e}")
        return False
# ADMIN
def get_admin_stats():
    """Lấy thống kê hệ thống từ Backend"""
    try:
        response = requests.get(f"{BASE_URL}/admin/stats")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Lỗi lấy stats: {e}")
        return None

def get_all_users():
    """Lấy danh sách tất cả user"""
    try:
        response = requests.get(f"{BASE_URL}/admin/users")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Lỗi lấy danh sách user: {e}")
        return []

def delete_user_by_admin(user_id):
    """Admin xóa user theo ID"""
    try:
        response = requests.delete(f"{BASE_URL}/admin/users/{user_id}")
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi xóa user: {e}")
        return False
def get_all_documents_admin():
    """Admin lấy danh sách toàn bộ file hệ thống"""
    try:
        response = requests.get(f"{BASE_URL}/documents/admin/all")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Lỗi lấy all docs: {e}")
        return []

def download_document_bytes(doc_id):
    """Tải nội dung file dưới dạng bytes"""
    try:
        response = requests.get(f"{BASE_URL}/documents/download/{doc_id}")
        if response.status_code == 200:
            return response.content 
        return None
    except Exception as e:
        print(f"Lỗi download: {e}")
        return None