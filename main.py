import os
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# Load biến môi trường
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = "gemini-3.6-flash"

client = genai.Client(api_key=GEMINI_API_KEY)
app = FastAPI(title="Student Manager AI")

class Student(BaseModel):
    id: str = Field(description="Mã số sinh viên, ví dụ: 524H0114")
    fullName: str = Field(description="Họ và tên")
    major: str = Field(description="Chuyên ngành")
    gpa: float = Field(description="Điểm GPA hệ 4.0")
    status: str = Field(description="Trạng thái học tập")

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

def get_student_by_id(student_id: str) -> dict:
    global last_called_fn
    last_called_fn = f"get_student_by_id('{student_id}')"
    for s in students_db:
        if s.id.lower() == student_id.strip().lower():
            return s.model_dump()
    return {"error": "Không tìm thấy"}

def get_students_by_major(major_keyword: str) -> list:
    global last_called_fn
    last_called_fn = f"get_students_by_major('{major_keyword}')"
    return [s.model_dump() for s in students_db if major_keyword.strip().lower() in s.major.lower()]

def get_all_students() -> list:
    global last_called_fn
    last_called_fn = "get_all_students()"
    return [s.model_dump() for s in students_db]

@app.get("/api/students", response_model=List[Student])
def list_students():
    return students_db

@app.post("/api/students", response_model=Student) 
def add_student_manual(student: Student):
    global students_db
    # Xóa sinh viên cũ nếu trùng MSSV, sau đó thêm mới
    students_db = [s for s in students_db if s.id.lower() != student.id.lower()]
    students_db.append(student)
    return student

@app.post("/api/ai/chat")
def chat_with_ai(req: ChatRequest):
    global last_called_fn
    last_called_fn = "Không dùng hàm"
    try:
        chat = client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction="Bạn là AI tra cứu sinh viên. Luôn dùng Tool để lấy dữ liệu trước khi trả lời.",
                tools=[get_student_by_id, get_students_by_major, get_all_students],
                temperature=0.2,
            )
        )
        response = chat.send_message(req.message)
        return {"answer": response.text, "functionCalled": last_called_fn}
        
    except Exception as e:
        error_msg = str(e)
        # 2. CƠ CHẾ DEMO FALLBACK: Bắt ngay lỗi 503 và trả về kết quả giả lập để UI không bị treo
        if "503" in error_msg:
            return {
                "answer": "⚠️ [Chế độ Fallback] Máy chủ Google hiện đang nghẽn. Tuy nhiên, luồng gọi hàm đã được thiết lập thành công. Hãy thử bấm gửi lại nhé!",
                "functionCalled": "Lỗi 503 (Server Quá Tải)"
            }
        raise HTTPException(status_code=400, detail=error_msg)

@app.post("/api/ai/analyze-doc", response_model=Student)
def analyze_document(req: DocAnalysisRequest):
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=f"Trích xuất JSON từ đơn:\n{req.documentText}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Student,
                temperature=0.1,
            ),
        )
        student = Student.model_validate_json(response.text)
        global students_db
        students_db = [s for s in students_db if s.id.lower() != student.id.lower()]
        students_db.append(student)
        return student
    except Exception as e:
        # Cơ chế Fallback cho Document Analysis
        if "503" in str(e):
            raise HTTPException(status_code=503, detail="⚠️ Máy chủ Google đang nghẽn. Vui lòng bấm thử lại.")
        raise HTTPException(status_code=400, detail=str(e))

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_home():
    return FileResponse("static/index.html")