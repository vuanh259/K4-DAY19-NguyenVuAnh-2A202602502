# Báo cáo Day 19 — Flat RAG vs GraphRAG

**Họ tên:** Nguyễn Vũ Anh  **MSSV:** 2A202602502  **Ngày:** 05/10/2026

**Trạng thái:** benchmark `--judge` hoàn thành đủ 3 phần và 6 câu hỏi; đã lưu ảnh Neo4j Q-A, Q-B, Q-D tại `report/img/`.

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

Chọn ít nhất 2 nhóm lỗi trong E1–E6 (`LAB_GUIDE.md` Bước 8.4). Sao chép khung dưới đây cho mỗi lỗi.

### Lỗi E3: Trùng thực thể vụ án

- **Hiện tượng:** Cùng người Cái Quang Huy nối tới hai node `Case` có tên và tiêu đề khác nhau, dù hai bài báo mô tả vụ vận chuyển từ Đức qua Nội Bài.
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

- **Nguyên nhân:** `MERGE (k:Case {name: $name})` dùng tên do LLM sinh làm khóa; tiêu đề/tóm tắt khác nhau giữa bài báo khiến Neo4j tạo hai node.
- **Đề xuất sửa:** giữ nguồn `doc_id` để truy vết, thêm bước entity resolution cho vụ án trùng nguồn bằng người, địa điểm, thời gian và chất/khối lượng; chỉ gộp khi có đủ bằng chứng để tránh gộp nhầm hai vụ khác nhau.

### Lỗi E4: Recall và judge đo khác nhau

- **Hiện tượng:** Q6 có Flat recall `0.00` nhưng judge `1`; Graph recall `0.67` nhưng judge cũng `1`.
- **Bằng chứng:** `data/benchmark_kg.json` đòi các từ khóa `Cái Quang Huy`, `Lê Minh Thành`, `Pháp y tâm thần`. Câu trả lời Flat nêu “Vụ Đạt…”, “Vụ Thành…” và “Vụ Đức…” nhưng không khớp nguyên văn từ khóa bắt buộc; câu trả lời Graph nêu Huy và Lê Minh Thành nhưng bỏ sót Pháp y tâm thần. Trong `ket_qua_benchmark_kg.txt`, judge cho cả hai câu Q6 điểm 1.
- **Nguyên nhân:** recall là so khớp chuỗi cứng với toàn bộ `must_include`, nên cách gọi rút gọn hoặc câu trả lời đúng một phần có thể nhận 0. Judge đánh giá ngữ nghĩa và cho điểm một phần; cả hai đều phụ thuộc vào LLM.
- **Đề xuất sửa:** giữ cả hai phép đo, giải thích định nghĩa trong báo cáo và kiểm tra câu trả lời cùng đáp án chuẩn thủ công. Nếu cải tiến benchmark, chuẩn hóa alias và tách keyword thành các ý nghĩa cần có thay vì so chuỗi nguyên văn.

## 4. Kết luận (5 điểm)

Flat RAG đủ cho single-hop (Q1–Q2: cả hai judge 2) và rẻ hơn rõ rệt. GraphRAG đáng cân nhắc cho câu hỏi xuyên KB hoặc multi-hop: thắng judge ở Q4–Q5, recall trung bình tăng từ 0.57 lên 0.94, nhưng chi phí mỗi câu tăng 4.95× và thời gian tăng 1.28×. Indexing Graph tốn thêm $0.15441 một lần; vì chi phí truy vấn Graph cũng cao hơn, không có điểm hòa vốn về tiền trong phép đo này — lựa chọn KG là đánh đổi chi phí lấy độ đầy đủ của câu trả lời xuyên KB. Q6 vẫn là hạn chế: Graph chưa tìm đủ mọi vụ MDMA và cả hai cách đo chỉ cho thấy câu trả lời đúng một phần.

## 5. Tự kiểm (5 điểm)

```
$ .venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider
52 passed in 2.92s
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
