# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Nguyễn Vũ Anh  **MSSV:** 2A202602502  **Ngày:** 05/10/2026

**Trạng thái:** benchmark `--judge` hoàn thành đủ 3 phần và 6 câu hỏi; có ảnh Neo4j Q-A, Q-B, Q-D tại `report/img/`, nhưng còn cần chụp lại toàn cửa sổ theo quy cách (xem cuối báo cáo).

**Cấu hình benchmark:** chat dùng ModelAPI Responses (`gpt-6.1-sol`), embedding dùng Gemini (`gemini-embedding-001`); xem `SETUP_MODELAPI.md`. Số liệu dưới đây lấy từ `ket_qua_benchmark_kg.txt`. Chi phí và độ trễ không bao gồm các lần gọi LLM-as-judge.

> Kỳ vọng và thang điểm: `SUBMISSION.md`. Mọi số liệu phải khớp với `ket_qua_benchmark_kg.txt`. Bản thiết kế ontology nộp riêng ở `report/ONTOLOGY.md`.

## 1. Chi phí (10 điểm)

Thông số lần chạy: `top_k=3`, `chunk_size=800`, 176 chunks, graph có 207 nodes / 392 relationships.

**Indexing (one-off)** — số liệu nguyên từ `ket_qua_benchmark_kg.txt`:

| Pipeline | Calls | In tokens | Out tokens | USD | Giây |
| --- | ---: | ---: | ---: | ---: | ---: |
| Flat | 176 | 0 | 0 | 0.00000 | 141.5 |
| Graph | 196 | 120,426 | 8,101 | 0.15441 | 466.1 |

**Querying (trung bình mỗi câu):**

| Pipeline | Recall | Judge | In tokens | Out tokens | USD | Giây |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Flat | 0.57 | 1.50 | 4,945 | 90 | 0.00293 | 7.48 |
| Graph | 0.94 | 1.83 | 10,443 | 170 | 0.01449 | 9.55 |

| Chỉ số | Flat | Graph | Graph / Flat |
| --- | --- | --- | --- |
| Indexing USD | 0.00000 | 0.15441 | Không xác định (Flat = 0) |
| Indexing giây | 141.5 | 466.1 | 3.29× |
| Mỗi câu: USD | 0.00293 | 0.01449 | 4.95× |
| Mỗi câu: giây | 7.48 | 9.55 | 1.28× |
| Mỗi câu: in_tok | 4,945 | 10,443 | 2.11× |

**Chi phí tăng thêm đến từ đâu?** Flat indexing chỉ embedding bằng Gemini free tier nên được tính $0. Graph indexing thêm 20 lượt trích xuất tin bằng chat và tạo 120,426 input tokens; khi truy vấn, GraphRAG đưa thêm dữ kiện graph vào prompt, làm input trung bình tăng 2.11× và USD mỗi câu tăng 4.95×. Độ trễ Graph cao hơn do bước trích xuất khi dựng graph và prompt lớn hơn khi hỏi.

**Giới hạn đo lường:** `0` token ở Flat indexing là giá trị fallback khi SDK embedding không cung cấp usage, không có nghĩa embedding không tiêu thụ token. Các tổng token chỉ gồm usage được báo về, chưa bao gồm token embedding bị thiếu. USD là ước tính theo đơn giá cấu hình: Gemini embedding free tier bằng 0; ModelAPI tính cả cached input với giá riêng. Đây là USD/credit danh nghĩa của gateway, không phải hóa đơn hoặc số tiền VND mua credit. Các tỷ lệ trên chỉ đúng với cấu hình và lần chạy này.

## 2. Từng câu hỏi (10 điểm)

| Câu | Loại | Flat recall / judge | Graph recall / judge | Thắng | Vì sao (1 câu) |
| --- | --- | --- | --- | --- | --- |
| Q1 | single-hop-law | 1.00 / 2 | 1.00 / 2 | Hòa | Cả hai đều trả lời đúng định nghĩa tiền chất; Graph nêu rõ khoản 4 Điều 2. |
| Q2 | single-hop-news | 1.00 / 2 | 1.00 / 2 | Hòa | Cả hai nêu đúng Trần Thanh Tuấn và Trần Minh Tâm; Graph thêm tội danh và Điều 251. |
| Q3 | cross-kb | 0.67 / 2 | 1.00 / 2 | Hòa theo judge; Graph recall cao hơn | Cả hai đúng, nhưng Flat thiếu một keyword bắt buộc trong khi Graph đủ mức án, điều và khung cơ bản. |
| Q4 | cross-kb | 0.33 / 1 | 1.00 / 2 | Graph | Graph nối tội danh của Hoàng Nato với Điều 255 và khung tối đa; Flat không có căn cứ luật trong ngữ cảnh. |
| Q5 | cross-kb-multi-hop | 0.40 / 1 | 1.00 / 2 | Graph | Graph nối người, tội, MDMA, Điều 250 và khối lượng với khoản 4; Flat thiếu điều luật và khung phạt. |
| Q6 | aggregation | 0.00 / 1 | 0.67 / 1 | Hòa theo judge; Graph recall cao hơn | Cả hai chỉ được judge một phần; Graph nêu được Huy và Lê Minh Thành nhưng thiếu cụm “Pháp y tâm thần”. |

Recall là tỷ lệ các từ khóa `must_include` có mặt; judge chấm 0–2 mức đúng/đủ. Q3 và Q6 cho thấy hai phép đo có thể khác nhau (phân tích ở mục 3).

## 3. Phân tích lỗi (20 điểm)

Phân tích hai nhóm E3 và E4, đối chiếu graph, bài nguồn và câu trả lời trong benchmark.

### Lỗi E3: Trùng thực thể vụ án

- **Hiện tượng:** Cùng người Cái Quang Huy nối tới hai node `Case` có tên khác nhau cho vụ vận chuyển từ Đức qua Nội Bài; một nguồn là bài chính, nguồn còn lại chứa đoạn giới thiệu tin liên quan.
- **Bằng chứng:** truy vấn dưới đây trả về hai vụ riêng cho cùng người:

```cypher
MATCH (p:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)
RETURN k.name AS case, k.doc_id AS doc
ORDER BY k.doc_id;
```

```
Vụ vận chuyển hơn 10kg ma túy từ Đức về Việt Nam qua sân bay Nội Bài
  news-100260917203001265
Vụ vận chuyển hơn 9,6kg MDMA và gần 406g Ketamine qua sân bay Nội Bài
  news-100260918080821054
```

- **Đối chiếu nguồn:** `news-100260917203001265` có tiêu đề “Từ mối quen biết tại nhà hàng ở Berlin đến những kiện hàng chứa hơn 10kg ma túy về Việt Nam”. `news-100260918080821054` có tiêu đề “Góp 14 triệu đồng mua ma túy rồi nói đã ‘rút lui’, 3 thanh niên kháng cáo kêu oan”; đoạn cuối bản crawl nhắc Huy, 9,6kg MDMA và gần 406g Ketamine như tin liên quan, không phải nội dung chính về ba thanh niên.
- **Nguyên nhân:** dữ liệu crawl lẫn tin liên quan khiến LLM trích thêm vụ; `MERGE (k:Case {name: $name})` dùng tên do LLM sinh làm khóa nên hai cách diễn đạt tạo hai node. Đây là suy luận từ nội dung nguồn và cách tạo khóa trong code.
- **Đề xuất sửa:** lọc phần tin liên quan trước khi trích xuất; giữ nguồn `doc_id` để truy vết, thêm entity resolution bằng người, địa điểm, thời gian và chất/khối lượng. Chỉ gộp khi đủ bằng chứng; kiểm tra lại benchmark sau thay đổi dữ liệu.

### Lỗi E4: Recall và judge đo khác nhau

- **Hiện tượng:** Q3 Flat có recall `0.67` nhưng judge `2`, dù câu trả lời có đầy đủ mức án, điều luật và khung cơ bản.
- **Bằng chứng nguyên văn** từ `ket_qua_benchmark_kg.txt`:

> Lê Minh Thành bị tuyên **36 tháng tù** về tội **mua bán trái phép chất ma túy**. Tội này được quy định tại **Điều 251 Bộ luật Hình sự**; khung hình phạt cơ bản là **từ 2 năm đến 7 năm tù**.

`must_include` của Q3 là `36 tháng`, `Điều 251`, `02 năm đến 07 năm`. Hai chuỗi đầu khớp; chuỗi cuối không khớp `2 năm đến 7 năm`, nên recall bằng `2/3 = 0.67`. Judge đánh giá ngữ nghĩa nên cho `2`.

- **Bằng chứng bổ sung Q6:** Graph khớp `Cái Quang Huy` và `Lê Minh Thành`, không khớp `Pháp y tâm thần`, nên recall `0.67`, judge `1`. Tuy nhiên câu trả lời có nhắc Sầm Sơn và “các buồng điều trị”; thiếu chuỗi bắt buộc chưa đủ chứng minh thiếu toàn bộ vụ về mặt ngữ nghĩa. Câu trả lời còn lặp vụ Huy với hai tên khác nhau như E3.
- **Nguyên nhân:** `keyword_recall` tính `sum(k.lower() in answer.lower() for k in keywords) / len(keywords)`, là phép đo xác định, không gọi LLM. Judge là một lượt gọi LLM riêng đánh giá ngữ nghĩa, có thể dao động. Recall không tự chuẩn hóa số có số 0 đầu hoặc tên gọi tương đương.
- **Đề xuất sửa:** giữ cả hai phép đo, giải thích định nghĩa trong báo cáo và kiểm tra câu trả lời cùng đáp án chuẩn thủ công. Nếu cải tiến benchmark, chuẩn hóa alias và tách keyword thành các ý nghĩa cần có thay vì so chuỗi nguyên văn.

## 4. Kết luận (5 điểm)

Flat RAG đủ cho single-hop trong bộ sáu câu này (Q1–Q2: cả hai judge 2) và rẻ hơn rõ rệt. GraphRAG đáng cân nhắc cho câu hỏi xuyên KB hoặc multi-hop: thắng judge ở Q4–Q5, recall trung bình tăng từ 0.57 lên 0.94, nhưng chi phí mỗi câu tăng 4.95× và thời gian tăng 1.28×. Indexing Graph tốn thêm $0.15441 một lần; vì chi phí truy vấn Graph cũng cao hơn, không có điểm hòa vốn về tiền trong phép đo này. Q6 chỉ đạt judge 1, có trùng vụ và thiếu keyword; cần đối chiếu từng vụ với nguồn trước khi kết luận độ bao phủ. Truy vấn MDMA trong `report/queries.cypher` trả về 5 node Case, còn câu trả lời liệt kê 4 mục; số node không đồng nghĩa số vụ thực tế do lỗi trùng và lẫn tin liên quan.

## 5. Tự kiểm (5 điểm)

```
$ .venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
52 passed in 1.25s
(chạy với -p no:cacheprovider để không ghi cache trong sandbox)

$ python bench_kg.py --check
[OK] Dữ liệu: 18 điều luật, 20 bài báo
[OK] KG-1 link_entity
[OK] Neo4j kết nối được
[provider] chat = openai:gpt-6.1-sol | embedding = gemini:gemini-embedding-001
[OK] KG-2 build_graph: 148 node / 294 cạnh, đường xuyên 2 KB dài 2 cạnh
[OK] KG-3 context: 30 dữ kiện, có Điều 251
[OK] KG-4 GraphRAGAgent.answer
[OK] Chi phí check: 1 lần gọi LLM, $0.01495.
```

Graph check chỉ có luật + 1 bài báo; số liệu benchmark đầy đủ nằm trong `ket_qua_benchmark_kg.txt`. Judge được gọi riêng và không tính trong các cột chi phí ở file kết quả.

Ảnh Neo4j: `report/img/kg_count.png`, `report/img/kg_cross_kb.png`, `report/img/kg_my_case.png`. Q-D dùng Cái Quang Huy. Các truy vấn đã lưu trong `report/queries.cypher`.

## Vấn đề gặp phải (không tính điểm)

Benchmark hoàn tất sau khi bổ sung giới hạn tốc độ và retry cho embedding Gemini trong `src/llm.py`. Chi phí trong file benchmark không bao gồm judge; đơn giá gateway/embedding phụ thuộc cấu hình provider.

**Ảnh còn cần bổ sung trước khi chấm:** ba ảnh hiện có thể hiện nội dung Neo4j nhưng chỉ chụp viewport, chưa có thanh trình duyệt như quy cách Bước 8.2. Công cụ chụp cửa sổ gặp lỗi `Computer Use native pipe is unavailable` và vẫn lỗi sau khi khởi động lại. Cần chụp nguyên cửa sổ trình duyệt cho Q-A, Q-B, Q-D, thấy ô truy vấn và Results overview, không cắt/chỉnh sửa; chạy `:clear` trước mỗi truy vấn. Đây là phần chưa hoàn tất quy cách nộp, không ảnh hưởng kết quả benchmark.
