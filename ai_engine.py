import os
import re
from google import genai
from google.genai import types 
from pypdf import PdfReader
from docx import Document 
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    """Hàm lấy client duy nhất cho toàn bộ ứng dụng để tối ưu kết nối."""
    global _client
    if _client is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            _client = genai.Client(api_key=api_key)
    return _client

def configure_gemini():
    """Kiểm tra cấu hình Gemini."""
    return get_client() is not None

def get_file_text(uploaded_file):
    """Trích xuất văn bản từ file PDF/Docx và đánh dấu nguồn (Trang/Đoạn)."""
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
    except Exception as e:
        print(f"Lỗi đọc file {filename}: {e}")
    return content_with_tags

def create_source_map(text):
    source_map = {}
    parts = re.split(r'(\[SOURCE: .*?\])', text)
    current_full_key = None
    current_doan_key = None

    for part in parts:
        if part.startswith('[SOURCE:'):
            match = re.search(
                r"SOURCE:\s*(.*?)\s*\|\s*(TRANG|DOAN):\s*(\d+)",
                part
            )
            if match:
                fname, type_tag, num = match.groups()
                clean_type = "Trang" if type_tag == "TRANG" else "Trích đoạn"
                current_full_key = f"{fname} - {clean_type} {num}"
                current_doan_key = f"DOAN {num}" if type_tag == "DOAN" else None

        elif current_full_key and part.strip():
            content = part.strip()
            source_map[current_full_key] = content
            if current_doan_key:
                source_map[current_doan_key] = content

    return source_map


def ask_gemini_stream(content, prompt, mode="strict"):
    try:
        client = get_client()
        if not client:
            def error_key(): yield "Lỗi: Chưa cấu hình API Key trong file .env"
            return error_key(), ""

        # QUY TẮC TRÍCH DẪN BẮT BUỘC
        citation_rule = (
            "BẠN ĐANG LÀM VIỆC TRONG HỆ THỐNG NGHIÊN CỨU KHOA HỌC KHẮT KHE.\n"  
            "1. ƯU TIÊN NGUỒN: Luôn ưu tiên trích dẫn từ 'DỮ LIỆU TÀI LIỆU (CONTEXT)' trước. Chỉ dùng Google Search khi thông tin không có trong tài liệu.\n\n"      
            "2. VỊ TRÍ ĐẶT NHÃN: CHỈ trích dẫn một lần duy nhất khi kết thúc một ý hoàn chỉnh hoặc một đoạn văn. KHÔNG trích dẫn sau mỗi câu đơn lẻ.\n\n"           
            "3. ĐỊNH DẠNG TÀI LIỆU NỘI BỘ (BẮT BUỘC): (Nguồn: TênFile - Trang X) hoặc (Nguồn: TênFile - Đoạn X).\n"
            "   - Ví dụ: (Nguồn: Bao_cao_2025.pdf - Trang 12).\n"
            "   - TUYỆT ĐỐI KHÔNG gộp trang kiểu 'Trang 11, 12'. Phải tách riêng từng nhãn.\n\n"
            "4. ĐỊNH DẠNG NGUỒN INTERNET (BẮT BUỘC): (Nguồn: Google Search - [Tiêu đề trang] - [Link URL]).\n"
            "   - Ví dụ: (Nguồn: Google Search - Xu hướng AI 2026 - https://example.com/article).\n"
            "   - Link URL phải bắt đầu bằng http hoặc https và là link thực tế từ kết quả tìm kiếm.\n\n"     
            "5. CHỐNG ẢO GIÁC (HALLUCINATION):\n"
            "   - KHÔNG tự bịa đặt số trang nếu không thấy trong nhãn [SOURCE: ...] của Context.\n"
            "   - KHÔNG tự ý chế URL hoặc thêm các ký tự rác vào cuối URL. Nếu không có link thực, ghi: (Nguồn: Kiến thức hệ thống).\n"
            "   - Tuyệt đối không bịa đặt thông tin không có thật.\n\n"
        )

        # AI Xây dựng prompt
        mode_instruction = (
            "CHẾ ĐỘ TRA CỨU CHÍNH XÁC: Chỉ trả lời dựa trên Context. Không suy diễn." 
            if mode == "strict" else 
            "CHẾ ĐỘ TƯ DUY & SÁNG TẠO: Khai thác file gốc và dùng Google Search để mở rộng luận điểm."
        )

        meta_prompt_query = (
            f"BẠN LÀ CHUYÊN GIA THIẾT KẾ PROMPT KHOA HỌC.\n"
            f"NHIỆM VỤ: Hãy viết một bản 'System Instruction' tối ưu để một AI khác giải quyết câu hỏi: '{prompt}'\n"
            f"YÊU CẦU VỀ CHẾ ĐỘ: {mode_instruction}\n"
            f"YÊU CẦU VỀ TRÍCH DẪN:\n{citation_rule}\n"
            "CHỈ TRẢ VỀ NỘI DUNG BẢN CHỈ DẪN TỐI ƯU."
        )

       
        res_step1 = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=meta_prompt_query,
            config=types.GenerateContentConfig(temperature=0.7) 
        )
        optimized_instructions = res_step1.text

        #  AI THỰC THI 
        my_tools = None 
        temp = 0.0 if mode == "strict" else 0.65
        if mode != "strict":
            my_tools = [types.Tool(google_search=types.GoogleSearch())]

        full_query = (
            f"=== BẢN CHỈ DẪN HỆ THỐNG ===\n{optimized_instructions}\n\n"
            f"--- DỮ LIỆU TÀI LIỆU (CONTEXT) ---\n{content}\n\n"
            f"--- CÂU HỎI TỪ NGƯỜI DÙNG ---\n{prompt}"
        )

        response_stream = client.models.generate_content_stream(
            model='gemini-2.5-flash', 
            contents=full_query,
            config=types.GenerateContentConfig(temperature=temp, tools=my_tools)
        )
        
        return response_stream, optimized_instructions

    except Exception as e:
        error_message = str(e) 
        class ErrorChunk:
            def __init__(self, msg):
                self.text = msg

        def error_gen():
            yield ErrorChunk(f"❌ Lỗi hệ thống AI: {error_message}")           
        return error_gen(), ""