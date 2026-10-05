# Cấu hình GenZShop / ModelAPI cho Lab19

Đối chiếu ngày 05/10/2026 với hướng dẫn API Codex được liên kết từ https://genzshop.vn/pages/docs.php?product=codex.

## Cấu hình đã áp dụng trong .env

```dotenv
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=gemini
OPENAI_BASE_URL=https://api.modelapi.vn/v1
OPENAI_CHAT_API=responses
OPENAI_CHAT_MODEL=gpt-6.1-sol
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_MIN_INTERVAL=0.8
```

OPENAI_API_KEY hiện có được giữ nguyên, không sao chép vào tài liệu. Tên provider `openai` ở đây chỉ SDK tương thích; request được gửi tới ModelAPI. `src/llm.py` đã hỗ trợ base URL riêng và Responses API. Cấu hình Codex của máy không bị sửa.

## Kết quả kiểm tra mới nhất

Key ModelAPI mới đã gọi chat thành công. Key Gemini đã tạo embedding thành công trong lúc indexing benchmark. `bench_kg.py --check` đạt đủ 7 `[OK]`: 148 node, 294 cạnh, đường xuyên KB dài 2 cạnh; context có 30 dữ kiện và Điều 251.

Lần benchmark đầu dừng ở embedding với HTTP 429: Gemini free tier giới hạn 100 yêu cầu/phút, server yêu cầu thử lại sau 23 giây. Code đã thêm khoảng cách 0.8 giây giữa các yêu cầu Gemini và thử lại tối đa 3 lần khi server trả RetryInfo. Các lỗi quota không có thời gian thử lại vẫn được báo ra. Lệnh chạy lại benchmark bị từ chối quyền thực thi ngoài sandbox; chưa có kết quả đầy đủ.

Giá chat được đối chiếu trực tiếp tại https://modelapi.vn/pricing ngày 05/10/2026: `gpt-6.1-sol`, nhóm `codex_không_lag`, bậc standard dưới 272K token: input 1.8, output 9, cached input 0.09 trên 1M token. Đã cấu hình các mức này trong .env và hỗ trợ tính token cache. Đây là ước tính theo USD/credit hiển thị của gateway, không phải số tiền VND thực tế mua credit hoặc hóa đơn. Gemini embedding dùng free tier (xác định từ tên quota server trả) nên đơn giá cấu hình là 0.

## Lịch sử xử lý

1. Kiểm tra danh sách model tại đúng gateway bằng key hiện tại nhận HTTP 401. Chưa gọi chat hoặc embedding thành công.
2. Theo hướng dẫn shop: mã đơn hàng là **mã đổi thưởng**. Đăng nhập modelapi.vn → Quản lý ví để đổi mã → Quản lý mã thông báo để tạo API token. Token này mới điền vào OPENAI_API_KEY. HTTP 401 không đủ để khẳng định key hiện tại chính là mã đổi thưởng; cũng có thể key sai, bị thu hồi hoặc khác dịch vụ.
3. Hướng dẫn Codex không xác nhận embedding. Hiện embedding vẫn là mặc định text-embedding-3-small tại gateway, **chưa xác minh được hỗ trợ**. Nếu không có, cần chọn provider embedding riêng và key tương ứng (GEMINI_API_KEY hoặc OPENROUTER_API_KEY), rồi đổi EMBEDDING_PROVIDER. Không dùng mock embedding để giả kết quả benchmark thật.
4. Bảng giá trong code không có giá gateway cho gpt-6.1-sol; hàm price hiện trả 0 cho model chưa biết. Không diễn giải giá trị đó là API miễn phí. Phải có giá thực tế của gói và bổ sung cách đo phù hợp trước khi hoàn thiện phần chi phí.

## Kiểm tra đã thực hiện

`python -m pytest tests/ -q -p no:cacheprovider`: 52 passed (48 test gốc + 4 test gateway). Các test thêm kiểm tra cấu hình SDK, đo token Responses, tính chi phí token cache và thử lại embedding theo RetryInfo.

Không cần cấu hình thêm để thử chạy. Khi có quyền kết nối API, chạy `bench_kg.py --judge` để lấy số liệu cuối cùng. Benchmark chưa chạy thành công; báo cáo và ảnh chưa đủ điều kiện nộp.
