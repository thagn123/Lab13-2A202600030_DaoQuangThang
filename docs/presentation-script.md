# Kịch Bản Thuyết Trình Lab 13 - Observability
**Người trình bày:** Đào Quang Thắng (Thành viên 1)

---

## Phần 1: Giới thiệu Tổng quan (Mở bài)
> **Lời thoại gợi ý:** "Chào Thầy/Cô, nhóm chúng em xin trình bày về bài Lab 13: Cấu hình Khả năng Quan sát (Observability) cho một Trợ lý ảo AI (FastAPI Agent). Hệ thống của chúng em được chia làm 2 lớp quan sát chính: Lớp thứ nhất là **Local Logging** (Ghi log cục bộ dạng JSON siêu tốc qua thư viện Structlog) và lớp thứ hai là **Cloud Tracing** (Theo dõi chi phí USD và đỗ trễ của LLM trên mây qua nền tảng Langfuse)."

**Kiến thức Thắng cần hiểu để GV hỏi:** 
- *Tại sao AI lại cần Observability?* Vì AI tốn tiền (Cost), hay bị lag (Latency P95), và đôi khi output sinh ra bị ngáo (Quality). Phải có hệ thống soi chiếu bằng dữ liệu thật thì mới scale-up lên phục vụ 1000 người được.

---

## Phần 2: Đi sâu vào Phần của Thắng (Core Logging & PII) - Điểm Cộng Chính
*Đây là phần Thắng chịu trách nhiệm code và cấu hình. Hãy trình bày tự tin nhất!*

### 1. Kỹ Thuật Correlation ID (Truy vết thẻ ID)
> **Lời thoại:** "Trách nhiệm đầu tiên của em là đảm bảo các dòng Log rời rạc không bị lạc mất nhau. Em đã can thiệp vào `middleware.py` của FastAPI để tự động sinh ra một thẻ định danh (Correlation ID - gồm 8 kí tự Hex) cho mỗi khi có người chat với con bot. Thẻ này được nhúng thẳng vào Headers trả về cho Client."

**Kiến thức Thắng cần hiểu:** 
- Khi có 1000 người chat cùng lúc, Terminal sẽ nổ tung bởi hàng triệu dòng log đan xen nhau. 
- Nhờ cái mã `req-xxxx` dán vào mọi hàm, ta chỉ cần ấn `Ctrl + F` tìm đúng mã đó là sẽ xâu chuỗi được toàn bộ quá trình: Bot nhận tin -> Chạy RAG -> Mất bao nhiêu lâu -> Sinh ra câu trả lời gì.

### 2. Kỹ Thuật Log Enrichment (Làm giàu Log)
> **Lời thoại:** "Tiếp theo ở `main.py`, em dùng hàm `bind_contextvars` để nhét sẵn các biến toàn cục như `user_id_hash`, môi trường `env: dev` vào mọi dòng log của tiến trình đó. Devops sau này đọc log bắt hỏng hóc sẽ không cần phải join db, họ nhìn phát là biết user nào đang dùng Model gì."

**Kiến thức Thắng cần hiểu:** 
- Thay vì mỗi lần `log.info` phải gõ thủ công báo cáo tên User, nhờ `structlog.contextvars`, cứ gọi log là tự động các thông tin râu ria (Metadata) kia sẽ tự nhảy gộp vào định dạng JSON log.

### 3. Kỹ Thuật PII Scrubbing (Bảo vệ thông tin cá nhân)
> **Lời thoại:** "Đây là chốt chặn quan trọng nhất của em. Trước khi tệp Log được kết xuất lưu vào ổ cứng hay đẩy lên Cloud, em đã cài cắm một bộ vi xử lý (Processor) trong `logging_config.py` kết hợp với Regex ở `pii.py`. Bất cứ khi nào Khách hàng lỡ chat số Điện thoại VN hay rò rỉ mã số Hộ Chiếu (Passport), bộ đếm Regex sẽ phát hiện và mã hoá nó thành chữ `[REDACTED_PHONE_VN]`."

**Kiến thức Thắng cần hiểu:** 
- Rất nhiều công ty bị phạt hàng triệu đô vì kĩ sư sơ ý lưu cả mật khẩu, thẻ tín dụng và SĐT của user vào file log dạng Text rồi đẩy file log lên máy chủ AWS (hoặc Elasticsearch) kém bảo mật. 
- Việc mã hóa phải xảy ra ở RAM ngay tắp lự.

---

## Phần 3: Hoạt động của hai người đồng đội (Đọc qua để hiểu Hệ thống)
Nếu thầy cô hỏi "Thế phần Langfuse bọn em chạy ra sao?":

- Của **Thành viên 2**: Bạn kia gắn cái móc `@observe()` (của Langfuse) vào các hàm `agent.run` và `MockRAG.retrieve`. Thế nên khi bot chạy, thời gian chạy tới đâu, số Lượng Token sinh ra tốn bao nhiêu (Usage) sẽ được Langfuse đo lại chi li đến hàng Mili-giây và vẽ ra sơ đồ Cây (Trace Waterfall).
- Của **Thành viên 3**: Bạn ấy vào Langfuse, xếp 6 tấm bảng báo cáo dựa vào lượng Log Thắng và Thành viên 2 đã đẩy lên. Kịch bản lỗi 500 hay Lỗi quá dòng tiền (Cost Spike) được nhóm dùng vòng lặp Script Python `test_runner.py` để nhồi ép Server phải bộc lộ yếu điểm. Sau đó bạn ấy lập cấu hình `yaml` báo động khẩn cấp (Alerting).

---

## Phần 4: Nhấn mạnh vào Khó khăn & Sửa lỗi (Khoe kĩ năng giải quyết vấn đề)
> **Lời thoại:** "Trong lúc làm Lab, nhóm em gặp một sự cố khá khoai với Langfuse. Tài liệu Lab dùng bộ cài cũ (v2), nhưng mặc định bọn em cài thư viện mới nhất (v3). Điều này dẫn tới code ở `agent.py` bị xung đột biến `usage_details` (của bản 3) không lọt qua vòng kiểm tra của version 2, làm Server gặp lỗi 500 ẩn và Tracing Langfuse chết đứng (xanh lè không đo được lỗi)."

**Cách em giải quyết:**
"Em đã chủ động lùi version (Downgrade) Python của Langfuse về đúng bản `2.53.8` thuần tuý, đồng thời sửa lại tham số truyền payload của Observer. Cuối cùng, để cho an toàn 100%, em ép thêm lệnh `Langfuse.flush()` ở `test_runner.py` để đảm bảo khi Load Testing xong, RAM sẽ vắt cạn dữ liệu tống thẳng lên Server Langfuse mới chịu sập máy. Kết quả là đo lường rực rỡ và đếm được chính xác P95 Latency của Mock Rag."

---
*Chúc Thắng có một buổi bảo vệ Lab thật mượt mà!*
