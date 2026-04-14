import os
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from google import genai

app = FastAPI(title="AI Advisor Pro - Multi-Risk Analysis")

# 1. KHỞI TẠO CLIENT (Tự động lấy GEMINI_API_KEY từ Environment Variable)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. ĐỊNH NGHĨA CẤU TRÚC DỮ LIỆU
class StudentInput(BaseModel):
    student_id: str
    risk_reasons: str

class AdviceResponse(BaseModel):
    student_id: str
    analysis: str

# 3. HÀM XỬ LÝ AI 
def generate_comprehensive_advice(reasons: str):
    prompt = f"""
    Bạn là một AI hỗ trợ cố vấn học tập chuyên nghiệp. Hãy phân tích các rủi ro sau: "{reasons}".
    
    Yêu cầu:
    - Trả về câu mở đầu ngẫu nhiên, phù hợp với nội dung hỗ trợ cố vấn học tập.
    - Xác định đúng các vấn đề có trong nội dung trên.
    - Đưa ra lời khuyên cụ thể chi tiết, hành động được ngay cho từng vấn đề. 
    - Văn phong hỗ trợ, chuyên nghiệp, ngắn gọn dành cho giảng viên cố vấn.
    - Không tạo ra các kí hiệu không cần thiết
    - Phải động viên, thúc đầy tin thần cố vấn
    """
    
    try:
     
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Lỗi xử lý AI: {str(e)}"

# 4. API ENDPOINTS
@app.post("/predict", response_model=AdviceResponse)
async def predict_single(data: StudentInput):
    analysis = generate_comprehensive_advice(data.risk_reasons)
    return {
        "student_id": data.student_id,
        "analysis": analysis
    }

@app.post("/predict_batch", response_model=List[AdviceResponse])
async def predict_batch(input_list: List[StudentInput]):
    results = []
    for item in input_list:
        analysis = generate_comprehensive_advice(item.risk_reasons)
        results.append({
            "student_id": item.student_id,
            "analysis": analysis
        })
    return results

@app.get("/")
def home():
    return {"message": "AI Advisor is live with google-genai library!"}
