# Cấu hình ModelAPI và Gemini cho Lab19

## Cấu hình đã chạy thành công

```dotenv
LLM_PROVIDER=openai
EMBEDDING_PROVIDER=gemini
OPENAI_BASE_URL=https://api.modelapi.vn/v1
OPENAI_CHAT_API=responses
OPENAI_CHAT_MODEL=gpt-6.1-sol
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_EMBEDDING_MIN_INTERVAL=0.8
OPENAI_CHAT_INPUT_USD_PER_M=1.8
OPENAI_CHAT_OUTPUT_USD_PER_M=9
OPENAI_CHAT_CACHED_INPUT_USD_PER_M=0.09
GEMINI_EMBEDDING_INPUT_USD_PER_M=0
```

`OPENAI_API_KEY` chứa API token ModelAPI, `GEMINI_API_KEY` chứa key Gemini. Key chỉ lưu trong `.env` được Git bỏ qua. Provider `openai` chọn SDK tương thích; chat gửi tới ModelAPI qua Responses API. Embedding dùng Gemini riêng, không dựa vào khả năng embedding của gói API Codex.

Hướng dẫn gateway: [GenZShop API Codex](https://genzshop.vn/pages/docs.php?product=codex). Mã đổi thưởng dùng để nạp ví; API token được tạo trong tài khoản ModelAPI. HTTP 401 có thể do token sai, thu hồi hoặc sai dịch vụ, không tự chứng minh đó là mã đổi thưởng.

## Kết quả xác minh

Benchmark `bench_kg.py --judge` đã hoàn thành indexing, Flat RAG và GraphRAG cho 6 câu hỏi, có đủ 12 câu trả lời và điểm judge trong `ket_qua_benchmark_kg.txt`. Dữ liệu gồm 176 chunks; graph đầy đủ có 207 nodes và 392 relationships. Recall/judge trung bình: Flat `0.57 / 1.50`, Graph `0.94 / 1.83`.

Lần `--check` trước benchmark đạt 7 mục `[OK]`, với graph nhỏ gồm luật và một bài báo: 148 nodes / 294 relationships, đường xuyên KB dài 2 cạnh, context có 30 dữ kiện và Điều 251. Không dùng số lượng graph nhỏ thay cho số lượng benchmark đầy đủ.

Kiểm thử offline: 52 tests passed (48 test gốc + 4 test gateway). Các test bổ sung kiểm tra cấu hình SDK, usage Responses, chi phí cached input và retry embedding theo RetryInfo.

## Chi phí và giới hạn

Đơn giá đã đối chiếu ngày 05/10/2026 tại [ModelAPI pricing](https://modelapi.vn/pricing): `gpt-6.1-sol`, nhóm `codex_không_lag`, bậc standard dưới 272K token; input 1.8, output 9, cached input 0.09 trên 1M token. Đây là ước tính USD/credit danh nghĩa của gateway, không phải số tiền VND mua credit hay hóa đơn. Gemini embedding dùng free tier nên giá cấu hình bằng 0.

SDK embedding không cung cấp usage trong lần chạy này; code ghi fallback 0 token. Không diễn giải 0 là không tiêu thụ token. Tổng token benchmark chưa gồm phần embedding không được báo về. Chi phí và độ trễ trong file kết quả không bao gồm LLM-as-judge.

Lần chạy đầu gặp HTTP 429 với quota Gemini 100 requests/phút. `src/llm.py` đã thêm khoảng cách 0.8 giây giữa request và tối đa 3 lần retry khi có RetryInfo phù hợp. Cơ chế này không vượt quota ngày; lỗi quota không có thời gian retry vẫn được báo ra. Benchmark sau đó đã chạy thành công; cấu hình hiện tại đủ để hoàn thiện báo cáo.