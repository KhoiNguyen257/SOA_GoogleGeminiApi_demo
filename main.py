import os
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Danh sách 2 model khả dụng trên tài khoản của bạn (tự động dự phòng nếu 1 model bị 503)
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash"]

client = genai.Client(api_key=GEMINI_API_KEY)
app = FastAPI(title="Student Manager AI Microservice")

class Student(BaseModel):
    id: str = Field(description="Mã số sinh viên (nếu văn bản không có thì để rỗng '')")
    fullName: str = Field(description="Họ và tên sinh viên (nếu văn bản không có thì để rỗng '')")
    major: str = Field(description="Chuyên ngành học (nếu văn bản không có thì để rỗng '')")
    gpa: float = Field(description="Điểm GPA hệ 4.0 (nếu văn bản không có thì để -1)")
    status: str = Field(description="Trạng thái học tập (nếu văn bản không có thì để rỗng '')")

class ChatRequest(BaseModel):
    message: str

class DocAnalysisRequest(BaseModel):
    documentText: str

students_db: List[Student] = [
    Student(id="524H0114", fullName="Võ Khôi Nguyên", major="Kỹ thuật Phần mềm", gpa=3.75, status="Đang học"),
    Student(id="524H0135", fullName="Nguyễn Phan Anh Tuấn", major="Kỹ thuật Phần mềm", gpa=3.68, status="Đang học"),
    Student(id="524H0201", fullName="Phạm Duy Khang", major="Hệ thống Thông tin", gpa=3.50, status="Đang học"),
    Student(id="524H0309", fullName="Lê Minh Châu", major="Khoa học Máy tính", gpa=3.92, status="Đạt học bổng"),
]

last_called_fn = ""

# =====================================================================
# HÀM KIỂM TRA: CHẶN TRÙNG MSSV (KHÔNG GHI ĐÈ) & CHẶN THIẾU THUỘC TÍNH
# =====================================================================
def validate_student(student: Student, raw_text: str = None):
    invalid_values = {"", "n/a", "none", "null", "unknown", "không có", "524h0000"}

    # 1. Nếu có MSSV, kiểm tra xem MSSV đã tồn tại trên bảng chưa (Cấm ghi đè)
    clean_id = student.id.strip()
    if clean_id.lower() not in invalid_values:
        for existing in students_db:
            if existing.id.strip().lower() == clean_id.lower():
                raise HTTPException(
                    status_code=400,
                    detail=f"Lỗi trùng lặp: Mã số sinh viên '{existing.id}' ({existing.fullName}) đã tồn tại trên bảng, không được phép ghi đè!"
                )

    # 2. Kiểm tra bắt buộc phải nhập đủ cả 5 thuộc tính
    missing = []
    if clean_id.lower() in invalid_values or (raw_text and clean_id.lower() not in raw_text.lower()):
        missing.append("MSSV")
    if student.fullName.strip().lower() in invalid_values:
        missing.append("Họ tên")
    if student.major.strip().lower() in invalid_values:
        missing.append("Ngành học")
    if student.gpa < 0 or student.gpa > 4.0:
        missing.append("GPA (0.0 - 4.0)")
    if student.status.strip().lower() in invalid_values:
        missing.append("Trạng thái")

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Lỗi thiếu thuộc tính: Vui lòng cung cấp đầy đủ thông tin (Đang thiếu: {', '.join(missing)})!"
        )

# Các hàm nội bộ cho Gemini Function Calling
def get_student_by_id(student_id: str) -> dict:
    """Tìm và trả về thông tin chi tiết của một sinh viên theo mã số sinh viên (MSSV)."""
    global last_called_fn
    last_called_fn = f"get_student_by_id('{student_id}')"
    for s in students_db:
        if s.id.lower() == student_id.strip().lower():
            return s.model_dump()
    return {"error": f"Không tìm thấy sinh viên có mã {student_id}"}

def get_students_by_major(major_keyword: str) -> list:
    """Lọc danh sách các sinh viên theo tên ngành học."""
    global last_called_fn
    last_called_fn = f"get_students_by_major('{major_keyword}')"
    return [s.model_dump() for s in students_db if major_keyword.strip().lower() in s.major.lower()]

def get_all_students() -> list:
    """Lấy toàn bộ danh sách sinh viên hiện có để thống kê GPA, tìm thủ khoa hoặc tra cứu."""
    global last_called_fn
    last_called_fn = "get_all_students()"
    return [s.model_dump() for s in students_db]

@app.get("/api/students", response_model=List[Student])
def list_students():
    return students_db

@app.post("/api/students", response_model=Student)
def add_student_manual(student: Student):
    validate_student(student)
    students_db.append(student)
    return student

@app.post("/api/ai/chat")
def chat_with_ai(req: ChatRequest):
    global last_called_fn
    last_called_fn = "Trả lời trực tiếp (Không gọi hàm)"
    last_err = None
    for model_name in MODELS:
        try:
            chat = client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Bạn là trợ lý AI quản lý sinh viên. Luôn dùng các hàm (Tools) được cung cấp để tra cứu dữ liệu "
                        "mới nhất từ hệ thống trước khi trả lời. Nếu người dùng chỉ gõ mã số sinh viên, hãy gọi hàm get_student_by_id."
                    ),
                    tools=[get_student_by_id, get_students_by_major, get_all_students],
                    temperature=0.2,
                )
            )
            response = chat.send_message(req.message)
            return {"answer": response.text, "functionCalled": last_called_fn}
        except Exception as e:
            last_err = e
            continue
    raise HTTPException(status_code=400, detail=str(last_err))

@app.post("/api/ai/analyze-doc", response_model=Student)
def analyze_document(req: DocAnalysisRequest):
    last_err = None
    student = None
    for model_name in MODELS:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=(
                    "Phân tích văn bản đơn từ sau và trích xuất thông tin sinh viên. "
                    "Lưu ý: Chỉ trích xuất thông tin có thật trong văn bản, trường nào không có thì để chuỗi rỗng '' (hoặc -1 cho GPA):\n"
                    f"{req.documentText}"
                ),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Student,
                    temperature=0.1,
                ),
            )
            student = Student.model_validate_json(response.text)
            break
        except Exception as e:
            last_err = e
            continue

    if student is None:
        raise HTTPException(status_code=400, detail=str(last_err))

    validate_student(student, raw_text=req.documentText)
    students_db.append(student)
    return student

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_home():
    return FileResponse("static/index.html")