import random
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from thefuzz import process, fuzz
import re

# --- 1. KHỞI TẠO APP ---
app = FastAPI(
    title="AI Advisor Assistant",
    description="Hệ thống gợi ý giải pháp cho Cố vấn học tập (Phong cách đồng nghiệp)",
    version="1.0.0"
)

# --- 2. CẤU TRÚC DỮ LIỆU (SCHEMA) ---
class StudentRiskInput(BaseModel):
    student_id: str
    risk_reasons: str  # Nhập các lý do cách nhau bằng dấu phẩy

class AdviceResponse(BaseModel):
    student_id: str
    original_risks: List[str]
    ai_recommendation: str
    priority: str

# --- 3. KNOWLEDGE BASE (LÝ DO & LỜI KHUYÊN) ---
colleague_templates = {
    'Chuyên cần thấp': [
        "Mình để ý em này vắng mặt khá nhiều. Thầy thử nhắn tin hỏi thăm xem em ấy có vướng lịch trình cá nhân nào không nhé.",
        "Tỉ lệ lên lớp của em này đang ở mức báo động. Nhờ Thầy nhắc nhở em ấy về quy chế cấm thi để em ấy tập trung hơn.",
        "Em này hay nghỉ học quá, mình sợ sẽ hổng kiến thức. Thầy có thể trò chuyện riêng để tìm nguyên nhân không?"
    ],
    'Mất gốc/Điểm cũ thấp': [
        "Nền tảng kiến thức của em này có vẻ đang hổng nặng. Thầy nên gợi ý em ấy tham gia các lớp phụ đạo hoặc tìm Thầy học kèm nhé.",
        "Kết quả cũ khá thấp, có lẽ em ấy đang nản. Một lời động viên và lộ trình học lại từ đầu của Thầy sẽ giúp ích rất nhiều đấy.",
        "Mình thấy em ấy đang đuối so với mặt bằng chung. Thầy hướng dẫn em ấy tập trung vào các học phần cốt lõi trước nhé."
    ],
    'Tự học ít': [
        "Thời gian tự học của em này quá ít. Thầy thử hướng dẫn em ấy cách lập thời khóa biểu và kỹ năng tự nghiên cứu xem sao.",
        "Có vẻ em ấy chưa biết cách tự học. Thầy gợi ý em ấy thử phương pháp Pomodoro hoặc học nhóm để cải thiện nhé."
    ],
    'Thiếu ngủ/Thể trạng kém': [
        "Sức khỏe em này không ổn, hay thiếu ngủ. Thầy khuyên em ấy nên cân đối lại giờ giấc, sức khỏe tốt học mới vào được.",
        "Nhìn em ấy có vẻ mệt mỏi. Thầy thử tâm sự xem em ấy có đang ôm đồm việc làm thêm hay thức đêm quá đà không nhé.",
        "Thể trạng kém sẽ ảnh hưởng lâu dài đến kết quả. Mình nghĩ Thầy nên nhắc em ấy chú trọng ăn uống và ngủ đủ giấc hơn."
    ],
    'Động lực học tập hiện tại suy giảm đáng kể': [
        "Dạo này em ấy có vẻ mất định hướng. Thầy thử chia sẻ về cơ hội nghề nghiệp tương lai để truyền thêm lửa cho em ấy nhé.",
        "Mình cảm thấy em ấy đang bị 'burn-out'. Thầy có thể dành chút thời gian nghe em ấy trải lòng về mục tiêu hiện tại không?"
        "Động lực của em này đang chạm đáy. Cần một cú hích từ cố vấn để em ấy tìm lại lý do tại sao mình bắt đầu ngành học này."
    ],
    'Có áp lực về điều kiện tài chính gia đình': [
        "Gia đình em ấy đang gặp khó khăn kinh tế. Thầy hướng dẫn em ấy thủ tục vay vốn hoặc các học bổng vượt khó nhé.",
        "Áp lực tài chính dễ làm SV nản lòng. Thầy thử kết nối em ấy với các công việc part-time trong trường xem sao.",
        "Mình nghe nói em ấy đang lo lắng về học phí. Thầy kiểm tra xem em ấy có thuộc diện được miễn giảm hay hỗ trợ đặc biệt nào không."
    ],
    'Khoảng cách di chuyển quá xa ảnh hưởng sức khỏe': [
        "Nhà em này ở xa quá, đi lại vất vả dễ gây nản. Thầy xem có thể sắp xếp cho em ấy vào ký túc xá hoặc trọ gần trường không?",
        "Việc di chuyển xa ảnh hưởng nhiều đến sức khỏe. Thầy thử gợi ý em ấy chọn các ca học tập trung để đỡ đi lại nhé."
    ],
    'Thiếu thốn tài nguyên/thiết bị phục vụ học tập': [
        "Em ấy đang thiếu thiết bị học tập. Thầy thử hỏi xem thư viện mình có chính sách cho mượn máy hoặc hỗ trợ học liệu không.",
        "Không có thiết bị thực hành thì khó tiến bộ. Thầy giới thiệu em ấy đến các phòng lab của trường để tận dụng máy móc nhé."
    ],
    'Chịu ảnh hưởng tiêu cực từ môi trường Thầy bè': [
        "Có vẻ em ấy đang chơi với nhóm Thầy không chăm chỉ lắm. Thầy thử khuyên em ấy giao lưu nhiều hơn với các nhóm học thuật.",
        "Môi trường Thầy bè ảnh hưởng lớn đến em này. Thầy nên gợi ý em ấy tham gia CLB chuyên môn để thay đổi môi trường."
    ],
    'Chưa tương thích với phương pháp giảng dạy': [
        "Em ấy chưa bắt nhịp được với cách dạy hiện tại. Thầy thử hướng dẫn em ấy cách ghi chép hoặc tiếp cận bài giảng kiểu mới.",
        "Có lẽ phương pháp hiện tại chưa phù hợp. Thầy thử trao đổi với giảng viên bộ môn để có sự điều chỉnh nhẹ nhàng nhé."
    ]
}

# --- 4. LOGIC XỬ LÝ CHÍNH ---
def clean_text(text: str):
    """Xóa bỏ số, ký tự đặc biệt và đưa về chữ thường để chuẩn hóa"""
    text = text.lower().strip()
    text = re.sub(r'\d+(\.\d+)?%?', '', text) # Xóa số và %
    return text

def generate_human_advice(risk_string: str):
    reasons = [r.strip() for r in risk_string.split(',')]
    selected_parts = []
    
    intros = [
        "Chào đồng nghiệp, mình vừa rà soát dữ liệu của em này.",
        "Chào Thầy, mình có vài lưu ý nhỏ muốn chia sẻ với Thầy về trường hợp này.",
        "Gửi Thầy, đây là vài phân tích từ hệ thống để hỗ trợ buổi tư vấn của Thầy."
    ]
    
     # Lời kết đoạn
    outros = [
        "Chúc Thầy có một buổi làm việc hiệu quả với em ấy!",
        "Nếu cần thêm thông tin gì, cứ báo mình nhé. Chúc em ấy sớm tiến bộ!",
        "Hy vọng sự can thiệp kịp thời của Thầy sẽ giúp em ấy vượt qua giai đoạn này."
    ]
    
    # Danh sách các từ khóa chuẩn trong Knowledge Base
    standard_keys = list(colleague_templates.keys())
    
    for r in reasons:
        cleaned_r = clean_text(r)
        if not cleaned_r: continue
        # Tìm từ khóa chuẩn gần giống nhất với từ người dùng nhập
        # limit=1: lấy 1 kết quả tốt nhất
        match, score = process.extractOne(cleaned_r, standard_keys, scorer=fuzz.token_set_ratio)
        
        # Nếu độ giống nhau > 65%, chấp nhận đó là lý do đó
        if score > 65:
            detected_keys.append(match)
            selected_parts.append(random.choice(colleague_templates[match]))
    # Loại bỏ các gợi ý trùng lặp nếu có
    selected_parts = list(dict.fromkeys(selected_parts))
    detected_keys = list(dict.fromkeys(detected_keys))
    if not selected_parts:
        return reasons, f"Không nhận diện được lý do: {r} (Score: {score})"
    
    # Ghép câu
    full_advice = f"{random.choice(intros)} " + " ".join(selected_parts) + f" {random.choice(outros)}"
    priority = "High" if len(reasons) >= 3 or "Chuyên cần" in risk_string else "Medium"
    
    return reasons, full_advice, priority

# --- 5. ENDPOINTS (CÁC ĐƯỜNG DẪN API) ---

@app.get("/", tags=["General"])
def read_root():
    return {"message": "Hệ thống AI Advisor đang chạy. Thêm '/docs' vào URL để kiểm thử."}

@app.post("/predict", response_model=AdviceResponse, tags=["AI Core"])
async def predict_advice(input_data: StudentRiskInput):
    reasons_list, advice, priority_level = generate_human_advice(input_data.risk_reasons)
    
    return {
        "student_id": input_data.student_id,
        "original_risks": reasons_list,
        "ai_recommendation": advice,
        "priority": priority_level
    }

@app.post("/predict_batch", response_model=List[AdviceResponse], tags=["AI Core"])
async def predict_batch_advice(input_list: List[StudentRiskInput]):
    """
    Endpoint này cho phép gửi một danh sách nhiều sinh viên cùng lúc.
    Định dạng JSON: [ {student_id: "..."}, {student_id: "..."} ]
    """
    results = []
    
    for item in input_list:
        # Gọi lại hàm logic đã viết cho từng sinh viên
        reasons_list, advice, priority_level = generate_human_advice(item.risk_reasons)
        
        results.append({
            "student_id": item.student_id,
            "original_risks": reasons_list,
            "ai_recommendation": advice,
            "priority": priority_level
        })
    
    return results

# --- CHẠY LOCAL ---
# Chạy lệnh: uvicorn main:app --reload
