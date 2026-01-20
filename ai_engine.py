import os
import time  # <--- THÊM THƯ VIỆN NÀY ĐỂ TÍNH GIỜ CHỜ
from google import genai
from google.genai import types 
from pypdf import PdfReader
from docx import Document 
import re
from dotenv import load_dotenv

load_dotenv()

def configure_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    return True if api_key else False

def get_file_text(uploaded_file):
    # (Giữ nguyên hàm này như cũ, không thay đổi)
    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    filename = uploaded_file.name
    content_with_tags = ""
    try:
        if file_extension == ".pdf":
            reader = PdfReader(uploaded_file)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and len(text.strip()) > 50:
                    content_with_tags += f"\n[SOURCE: {filename} | TRANG: {i+1}]\n{text}\n"
        elif file_extension == ".docx":
            doc = Document(uploaded_file)
            for i, para in enumerate(doc.paragraphs):
                text = para.text.strip()
                if len(text) > 30:
                    content_with_tags += f"\n[SOURCE: {filename} | DOAN: {i+1}]\n{text}\n"
        elif file_extension == ".txt":
            text = uploaded_file.getvalue().decode("utf-8")
            content_with_tags += f"\n[SOURCE: {filename} | DOAN: 1]\n{text}\n"
        return content_with_tags
    except Exception as e:
        print(f"Lỗi đọc file: {e}")
        return ""

def create_source_map(text):
    # (Giữ nguyên hàm này như cũ)
    source_map = {}
    parts = text.split("[SOURCE: ")
    for part in parts:
        if not part.strip(): continue
        try:
            if "]\n" in part:
                header, content = part.split("]\n", 1)
            else: continue 
            file_info, position_info = header.split(" | ")
            type_, number = position_info.split(": ")
            label_type = "Trang" if type_ == "TRANG" else "Trích đoạn"
            key = f"{file_info} - {label_type} {number}"
            if content.strip(): source_map[key] = content.strip()
        except Exception: continue 
    return source_map

def ask_gemini(content, prompt, mode="strict"):
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key: return "Lỗi: Thiếu API Key"

        client = genai.Client(api_key=api_key)
        
        # QUY TẮC ĐỊNH DẠNG 
        citation_rule = (
            "\nQUY TẮC ĐỊNH DẠNG KỸ THUẬT (TUÂN THỦ 100%) \n"
            "1. ĐỊNH DẠNG TRÍCH DẪN DUY NHẤT: (Nguồn: TênFile - Trích đoạn X) hoặc (Nguồn: TênFile - Trang Y).\n"
            "   - Tuyệt đối KHÔNG dùng: [SOURCE...], 'Đoạn...', 'DOAN...', 'Theo tài liệu...'\n"
            "2. VỊ TRÍ TRÍCH DẪN: Đặt ngay cuối mỗi câu hoặc đoạn văn chứa thông tin từ tài liệu.\n"
            "3. PHẦN KẾT LUẬN: Bắt buộc phải có trích dẫn nguồn lại một lần nữa để tổng hợp.\n"
            "4. KHÔNG viết định dạng Markdown link (như [text](url)), chỉ viết text thuần theo mẫu trên.\n"
            "----------------------------------------------------------------------------\n"
        )
        
        if mode == "strict":
            # CHẾ ĐỘ 1: TRA CỨU CHÍNH XÁC
            system_prompt = (
                "BẠN LÀ TRỢ LÝ TRA CỨU HỌC THUẬT NGHIÊM TÚC.\n"
                "NHIỆM VỤ: Trả lời câu hỏi CHỈ DỰA TRÊN dữ liệu cung cấp. Trung thực, khách quan, không thêm bớt.\n"
                "TƯ DUY XỬ LÝ:\n"
                "- Rà soát toàn bộ tài liệu để tìm thông tin khớp với câu hỏi.\n"
                "- Nếu thông tin rải rác, hãy tổng hợp lại thành câu trả lời mạch lạc.\n"
                "- Nếu không có thông tin, hãy trả lời thẳng: 'Tài liệu không đề cập'.\n"
                f"{citation_rule}"
            )
            temp = 0.0
        else:
            # CHẾ ĐỘ 2: TƯ DUY & SÁNG TẠO 
            system_prompt = (
                "BẠN LÀ CHUYÊN GIA TƯ VẤN VÀ PHẢN BIỆN KHOA HỌC CẤP CAO.\n"
                "NHIỆM VỤ: Không chỉ trả lời, hãy Phân tích sâu - Mở rộng - Phản biện vấn đề dựa trên tài liệu.\n"
                "\n"
                "QUY TRÌNH TƯ DUY (Chain of Thought):\n"
                "1. **Phân tích ngữ nghĩa:** Hiểu rõ câu hỏi và bối cảnh của các đoạn tài liệu liên quan.\n"
                "2. **Liên kết dữ liệu:** Kết nối các ý tưởng rời rạc trong tài liệu để tìm ra các 'Pattern' (mô hình/xu hướng) ẩn.\n"
                "3. **Phát hiện khoảng trống:** Chỉ ra những điểm tài liệu chưa nói rõ hoặc còn hạn chế.\n"
                "4. **Đề xuất giả thuyết:** Dựa trên kiến thức của bạn, đề xuất các hướng nghiên cứu mới hoặc giải pháp thực tiễn (Ghi rõ: 'Đây là đề xuất của tôi').\n"
                "\n"
                "CẤU TRÚC TRẢ LỜI MONG MUỐN:\n"
                "- Phân tích trực tiếp câu hỏi.\n"
                "- Các luận điểm chính (kèm trích dẫn).\n"
                "- Góc nhìn mở rộng/Phản biện.\n"
                "- Kết luận & Đề xuất.\n"
                f"{citation_rule}"
            )
            temp = 0.7 
        
        full_query = f"{system_prompt}\n\n--- DỮ LIỆU TÀI LIỆU ---\n{content}\n\n--- CÂU HỎI NGƯỜI DÙNG ---\n{prompt}"
        
        # --- CƠ CHẾ TỰ ĐỘNG THỬ LẠI KHI SERVER QUÁ TẢI (FIX LỖI 503) ---
        max_retries = 3 # Thử lại tối đa 3 lần
        
        for attempt in range(max_retries):
            try:
                # Gọi Google Gemini (Giữ nguyên model gemini-2.5-flash như bạn yêu cầu)
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=full_query,
                    config=types.GenerateContentConfig(temperature=temp)
                )
                return response.text
            
            except Exception as e:
                error_msg = str(e).lower()
                # Kiểm tra nếu lỗi là 503 (Overloaded) hoặc 429 (Too Many Requests)
                if "503" in error_msg or "overloaded" in error_msg or "429" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = 3 * (attempt + 1) # Lần 1 chờ 3s, lần 2 chờ 6s...
                        print(f"⚠️ Server Google đang bận. Đang thử lại lần {attempt + 1} sau {wait_time}s...")
                        time.sleep(wait_time)
                        continue # Quay lại đầu vòng lặp để thử lại
                
                # Nếu là lỗi khác hoặc đã hết lượt thử
                return f"Lỗi AI: {e}"

    except Exception as e:
        return f"Lỗi hệ thống: {e}"