import requests

# Địa chỉ API Java từ mã nguồn của bạn
JAVA_BACKEND_URL = "http://localhost:8080/api/documents/upload"

def upload_file_to_java(uploaded_file):
    """Gửi file sang Java Backend để lưu trữ vào Database"""
    try:
        files = {
            'file': (uploaded_file.name, uploaded_file.getvalue(), 'application/pdf')
        }
        response = requests.post(JAVA_BACKEND_URL, files=files)
        return response.status_code == 200
    except Exception as e:
        print(f"Lỗi kết nối Java: {e}")
        return False