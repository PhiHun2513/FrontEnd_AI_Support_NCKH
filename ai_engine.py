import google.generativeai as genai
import os
from pypdf import PdfReader
from docx import Document 
import re

def configure_gemini():
    """Cấu hình API Key từ biến môi trường"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        return True
    return False

def get_file_text(uploaded_file):
    """Trích xuất văn bản và đánh dấu vị trí để truy vết"""
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
        return f"Lỗi đọc file: {e}"

def ask_gemini(content, prompt):
    """Gửi truy vấn đến Gemini và nhận câu trả lời"""
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    system_prompt = (
        "Bạn là trợ lý nghiên cứu khoa học chuyên nghiệp. "
    "Nhiệm vụ duy nhất của bạn là phân tích, tổng hợp và trả lời "
    "DỰA HOÀN TOÀN trên nội dung tài liệu mà người dùng đã cung cấp.\n\n"

    "QUY TẮC BẮT BUỘC:\n"
    "1. TUYỆT ĐỐI KHÔNG sử dụng kiến thức bên ngoài tài liệu.\n"
    "2. KHÔNG suy đoán, KHÔNG bịa đặt, KHÔNG bổ sung kiến thức nền.\n"
    "3. Nếu tài liệu KHÔNG đủ thông tin, hãy trả lời đúng câu sau và không nói thêm:\n"
    "   'Tài liệu không cung cấp đủ thông tin để trả lời câu hỏi này.'\n"
    "4. Mỗi ý trả lời BẮT BUỘC phải kèm trích dẫn nguồn.\n"
    "   Định dạng trích dẫn: (Trang X) hoặc (Đoạn Y)\n"
    "   dựa trên các thẻ [TRANG_X] hoặc [DOAN_Y] trong nội dung.\n"
    "5. Nếu không thể trích dẫn nguồn, KHÔNG được trả lời.\n"
    "6. Trả lời theo văn phong học thuật, khách quan, trung lập."
    )
    
    full_query = f"{system_prompt}\n\nNỘI DUNG:\n{content}\n\nCÂU HỎI: {prompt}"
    response = model.generate_content(full_query)
    return response.text

def create_source_map(text):
    """Tạo bản đồ dữ liệu để tra cứu nhanh khi bấm xem nguồn"""
    source_map = {}
    
    # Tìm nội dung theo trang (PDF) - Đã sửa lỗi biến pdf_parts
    pdf_parts = re.findall(r"\[TRANG_(\d+)\]\n(.*?)(?=\n\[TRANG_|\Z)", text, re.DOTALL)
    for num, content in pdf_parts: 
        source_map[f"Trang {num}"] = content.strip()
        
    # Tìm nội dung theo đoạn (Word)
    doc_parts = re.findall(r"\[DOAN_(\d+)\]\n(.*?)(?=\n\[DOAN_|\Z)", text, re.DOTALL)
    for num, content in doc_parts:
        source_map[f"Đoạn {num}"] = content.strip()
        
    return source_map