import os
import time 
from google import genai
from google.genai import types 
from pypdf import PdfReader
from docx import Document 
from dotenv import load_dotenv

load_dotenv()

def configure_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    return True if api_key else False

def get_file_text(uploaded_file):
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
            "\n=== QUY TẮC TRÍCH DẪN & DẪN LINK (TUÂN THỦ 100%) ===\n"
            "1. ĐỐI VỚI FILE TẢI LÊN (Nội bộ): \n"
            "   - Bắt buộc dùng định dạng text thuần: (Nguồn: TênFile - Trích đoạn X) hoặc (Nguồn: TênFile - Trang Y).\n"
            "   - Lý do: Để hệ thống hiển thị popup trích dẫn nội bộ.\n"
            "2. ĐỐI VỚI THÔNG TIN TỪ INTERNET (Google Search): \n"
            "   - BẮT BUỘC phải cung cấp đường dẫn truy cập (URL) cho mọi thông tin bên ngoài.\n"
            "   - ĐIỀU KIỆN QUAN TRỌNG: Chỉ sử dụng URL mà bạn THỰC SỰ TÌM THẤY qua công cụ Search. TUYỆT ĐỐI KHÔNG tự đoán hoặc bịa ra đường link.\n"
            "   - Định dạng: Sử dụng Markdown Link: [Tiêu đề bài viết - Nguồn](URL)\n"
            "   - Nếu không tìm thấy link chính xác, hãy dẫn link trang chủ (Ví dụ: [Trang chủ OpenAI](https://openai.com)).\n"
            "==========================================================\n"
        )
        
        my_tools = None 

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
            my_tools = [types.Tool(google_search=types.GoogleSearch())]
            
            system_prompt = (
                "BẠN LÀ CHUYÊN GIA TƯ VẤN CHIẾN LƯỢC & PHẢN BIỆN KHOA HỌC (ADAPTIVE EXPERT).\n"
                "NHIỆM VỤ: Sử dụng tư duy phân tích sâu sắc, trình bày vấn đề linh hoạt, NHƯNG phải tuyệt đối tuân thủ dữ liệu gốc.\n"
                "\n"
                "QUY TRÌNH XỬ LÝ (BẮT BUỘC TUÂN THỦ):\n"
                "1. **BƯỚC 1 - KHAI THÁC FILE GỐC (Ưu tiên tuyệt đối):**\n"
                "   - Trước khi sáng tạo, bạn PHẢI rà soát 'DỮ LIỆU TÀI LIỆU' để tìm câu trả lời.\n"
                "   - Mọi luận điểm đưa ra phải có bằng chứng từ file (dùng định dạng: (Nguồn: TênFile - Trích đoạn X)).\n"
                "   - Chỉ khi file không có thông tin, bạn mới được bỏ qua bước trích dẫn file.\n"
                "\n"
                "2. **BƯỚC 2 - MỞ RỘNG & PHẢN BIỆN (Google Search):**\n"
                "   - Sau khi đã có cốt lõi từ file, hãy dùng Google Search để tìm ví dụ thực tế, số liệu mới nhất để bổ sung.\n"
                "   - Thông tin từ Google bắt buộc phải có Link URL.\n"
                "\n"
                "3. **BƯỚC 3 - TRÌNH BÀY LINH HOẠT (Adaptive Style):**\n"
                "   - **Nếu hỏi 'Làm thế nào':** -> Quy trình từng bước (Step-by-step).\n"
                "   - **Nếu hỏi 'Giải thích/Tại sao':** -> Kể chuyện, ẩn dụ, so sánh.\n"
                "   - **Nếu hỏi 'Đánh giá':** -> Phân tích SWOT hoặc Bảng so sánh.\n"
                "\n"
                "TÓM LẠI: Sự sáng tạo nằm ở CÁCH TRÌNH BÀY, còn SỰ THẬT nằm ở FILE VÀ LINK GOOGLE.\n"
                f"{citation_rule}"
            )
            temp = 0.65
        
        full_query = f"{system_prompt}\n\n--- DỮ LIỆU TÀI LIỆU ---\n{content}\n\n--- CÂU HỎI NGƯỜI DÙNG ---\n{prompt}"
        
        # TỰ ĐỘNG THỬ LẠI KHI SERVER QUÁ TẢI (LỖI 503 và 429)
        max_retries = 3 
        for attempt in range(max_retries):
            try:
                generate_config = types.GenerateContentConfig(
                    temperature=temp,
                    tools=my_tools 
                )

                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=full_query,
                    config=generate_config
                )
                return response.text
            
            except Exception as e:
                error_msg = str(e).lower()
                if "503" in error_msg or "overloaded" in error_msg or "429" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = 3 * (attempt + 1) 
                        print(f"⚠️ Server Google đang bận. Đang thử lại lần {attempt + 1} sau {wait_time}s...")
                        time.sleep(wait_time)
                        continue 
                return f"Lỗi AI: {e}"

    except Exception as e:
        return f"Lỗi hệ thống: {e}"