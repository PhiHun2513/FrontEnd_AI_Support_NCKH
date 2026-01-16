import os
from google import genai # <--- Thư viện mới
from pypdf import PdfReader
from docx import Document 
import re
from dotenv import load_dotenv

# Load biến môi trường ngay tại đây để đảm bảo có API Key
load_dotenv()

def configure_gemini():
    """Kiểm tra xem API Key có tồn tại không"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        return True
    return False

def get_file_text(uploaded_file):
    """Trích xuất văn bản và đánh dấu vị trí (Giữ nguyên logic cũ)"""
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    content_with_tags = ""
    
    try:
        if file_extension == ".pdf":
            reader = PdfReader(uploaded_file)
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                content_with_tags += f"\n[TRANG_{i+1}]\n{text}\n"
        
        elif file_extension == ".docx":
            doc = Document(uploaded_file)
            for i, para in enumerate(doc.paragraphs):
                if para.text.strip():
                    content_with_tags += f"\n[DOAN_{i+1}]\n{para.text}\n"
        
        elif file_extension == ".txt":
            text = uploaded_file.getvalue().decode("utf-8")
            content_with_tags = text
            
        return content_with_tags
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return ""

def ask_gemini(content, prompt):
    """Gửi truy vấn đến Gemini bằng SDK MỚI (google-genai)"""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "Lỗi: Chưa cấu hình GOOGLE_API_KEY"

        # --- CẤU HÌNH THEO SDK MỚI ---
        client = genai.Client(api_key=api_key)
        
        system_prompt = (
            "Bạn là trợ lý nghiên cứu khoa học chuyên nghiệp. "
            "Nhiệm vụ: Trả lời câu hỏi dựa trên nội dung tài liệu được cung cấp dưới đây.\n\n"
            "QUY TẮC QUAN TRỌNG:\n"
            "1. Nếu tài liệu là PDF (có thẻ [TRANG_X]), hãy trích dẫn nguồn dạng: (Trang X).\n"
            "2. Nếu tài liệu là Word/Text (có thẻ [DOAN_X]), hãy trích dẫn nguồn dạng: (Trích đoạn X).\n"
            "3. Tuyệt đối không bịa đặt thông tin không có trong tài liệu.\n"
            "4. Nếu không tìm thấy thông tin, hãy trả lời trung thực là không có."
        )
        
        full_query = f"{system_prompt}\n\n--- TÀI LIỆU ---\n{content}\n\n--- CÂU HỎI ---\n{prompt}"
        
        # Gọi model (Dùng gemini-2.5-flash cho nhanh và rẻ)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_query
        )
        
        return response.text
    except Exception as e:
        return f"Lỗi AI: {e}"

def create_source_map(text):
    """Tạo bản đồ dữ liệu (Giữ nguyên logic cũ)"""
    source_map = {}
    
    # 1. Xử lý PDF (Trang)
    chunks = re.split(r"\[TRANG_(\d+)\]", text)
    for i in range(1, len(chunks), 2):
        page_num = chunks[i]
        content = chunks[i+1].strip()
        if content:
            source_map[f"Trang {page_num}"] = content

    # 2. Xử lý Word (Đoạn -> Trích đoạn)
    chunks_doc = re.split(r"\[DOAN_(\d+)\]", text)
    for i in range(1, len(chunks_doc), 2):
        para_num = chunks_doc[i]
        content = chunks_doc[i+1].strip()
        if content:
            # Lưu key khớp với logic hiển thị mới là "Trích đoạn"
            source_map[f"Trích đoạn {para_num}"] = content
            # Lưu thêm key cũ "Đoạn" để đề phòng tương thích ngược
            source_map[f"Đoạn {para_num}"] = content
            
    return source_map