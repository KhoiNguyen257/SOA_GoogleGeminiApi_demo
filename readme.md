# Google Gemini API Microservice

Dự án mẫu minh họa cách tích hợp **Google Gemini API** vào kiến trúc **Microservice (FastAPI)**, phục vụ bài báo cáo Seminar môn học. Ứng dụng giải quyết bài toán quản lý và tra cứu sinh viên thông minh thông qua 4 năng lực cốt lõi của AI:

1. **Text Generation (Sinh văn bản):** Tổng hợp dữ liệu từ hệ thống thành câu trả lời tự nhiên, mạch lạc.
2. **Document Analysis (Phân tích tài liệu):** Đọc hiểu văn bản đơn từ/hồ sơ sinh viên tự do mà không cần viết biểu thức chính quy (`Regex`).
3. **Structured Outputs (Đầu ra có cấu trúc):** Ép phản hồi của AI tuân thủ nghiêm ngặt `Pydantic Schema` (`JSON`) để lưu trực tiếp vào Database.
4. **Function Calling (Gọi hàm nội bộ):** Cho phép Gemini tự động chọn và kích hoạt các hàm Python truy vấn dữ liệu thời gian thực (tra cứu theo MSSV, lọc theo ngành học, thống kê GPA).

---

##  1. Yêu cầu hệ thống (Prerequisites)

Trước khi bắt đầu, hãy đảm bảo máy tính của bạn đã cài đặt:
* **Python 3.9 trở lên** (Kiểm tra bằng lệnh `python --version`).
* **Git** (Để clone dự án hoặc tải trực tiếp file `.zip` từ kho lưu trữ).
* Một tài khoản Google cá nhân để lấy khóa **Gemini API Key** miễn phí.

---

##  2. Hướng dẫn cài đặt tuần 

### Bước 1: Clone dự án về máy
Mở Terminal (hoặc Command Prompt / PowerShell) và chạy lệnh sau để tải mã nguồn về máy:
```bash
git clone <ĐƯỜNG_DẪN_GITHUB_HOẶC_GIẢI_NÉN_FILE_ZIP>
cd gemini-fastapi
```

### Bước 2: Tạo môi trường ảo Python
* **Trên Windows:**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
* **Trên macOS / Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Bước 3: Cài đặt các thư viện cần thiết
Chạy lệnh sau để cài đặt toàn bộ thư viện khai báo trong `requirements.txt` (`fastapi`, `uvicorn`, `google-genai`, `pydantic`, `python-dotenv`):
```bash
pip install -r requirements.txt
```

### Bước 4: Lấy Google Gemini API Key & Cấu hình file `.env`
1. Truy cập [Google AI Studio](https://aistudio.google.com/apikey) và đăng nhập tài khoản Google.
2. Nhấn nút **Create API key** $\rightarrow$ Copy chuỗi khóa vừa tạo.
3. Tại thư mục gốc của dự án (`gemini-fastapi/`), tạo một file tên là `.env` (nằm ngang hàng với `main.py`) và dán nội dung sau vào:
   ```env
   GEMINI_API_KEY=Dán_Mã_API_Key_Của_Bạn_Vào_Đây
   ```

### Bước 5: Khởi chạy Microservice
Chạy lệnh sau trên Terminal để bật máy chủ FastAPI:
```bash
python -m uvicorn main:app --reload
```
Khi Terminal hiển thị dòng `INFO: Application startup complete.`, hãy mở trình duyệt và truy cập:
* 🌐 **Giao diện Web ứng dụng:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* 📄 **Tài liệu REST API (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📂 3. Cấu trúc thư mục dự án

```text
gemini-fastapi/
├── .env                  # Lưu trữ biến môi trường GEMINI_API_KEY (Bảo mật, không đẩy lên Git)
├── requirements.txt      # Danh sách các gói thư viện Python
├── README.md             # Tài liệu hướng dẫn cài đặt và tái sử dụng
├── main.py               # Toàn bộ mã nguồn Backend FastAPI & tích hợp Google Gemini SDK
└── static/
    └── index.html        # Giao diện người dùng (Thêm SV, Chat Function Calling, Nhập đơn từ)
```

---

## 🔌 4. Đặc tả các REST API Endpoints

Microservice cung cấp các HTTP Endpoints chuẩn JSON để dễ dàng tích hợp với bất kỳ Frontend hoặc Backend nào khác:

| Phương thức | Đường dẫn (Endpoint) | Mô tả chức năng |
| :--- | :--- | :--- |
| `GET` | `/api/students` | Lấy toàn bộ danh sách sinh viên hiện có trong hệ thống. |
| `POST` | `/api/students` | Thêm mới một sinh viên thủ công vào hệ thống (nhận JSON chuẩn `Student`). |
| `POST` | `/api/ai/chat` | Nhận câu hỏi tự nhiên, tự động kích hoạt **Function Calling** và trả về câu trả lời bằng **Text Generation**. |
| `POST` | `/api/ai/analyze-doc` | Nhận văn bản đơn từ tự do, thực hiện **Document Analysis** và ép kiểu **Structured Outputs** để lưu sinh viên mới. |

---
