// Q-A: kg_count.png
MATCH (n) RETURN labels(n)[0] AS label, count(*) AS n ORDER BY n DESC;

// Q-B: kg_cross_kb.png
MATCH p=(:Person)-[:INVOLVED_IN]->(:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article)
RETURN p LIMIT 25;

// Q-D: kg_my_case.png. Kiểm tra tên sau khi build; chạy :clear trước mỗi ảnh.
MATCH p=(:Person {name:'Cái Quang Huy'})-[:INVOLVED_IN]->(k:Case)-[:CHARGED_WITH]->(:Crime)<-[:DEFINES]-(:Article)
OPTIONAL MATCH q=(k)-[:INVOLVES|LOCATED_IN]->()
RETURN p, q;

// E1: đối chiếu bài nguồn để xác định có thực sự thiếu tội.
MATCH (k:Case) WHERE NOT (k)-[:CHARGED_WITH]->() RETURN k.name, k.doc_id;

// E3: kiểm tra tên chất đồng nghĩa.
MATCH (s:Substance) RETURN s.name ORDER BY toLower(s.name);

// E6: thuộc tính thiếu có thể hợp lý, cần đọc lại bài nguồn.
MATCH (p:Person)-[r:INVOLVED_IN]->(k:Case)
WHERE coalesce(r.charge, '') = ''
RETURN p.name, r.role, k.name, k.doc_id;

// Q6: đối chiếu aggregation với câu trả lời GraphRAG.
MATCH (k:Case)-[r:INVOLVES]->(:Substance {name:'MDMA'})
OPTIONAL MATCH (p:Person)-[:INVOLVED_IN]->(k)
RETURN k.name, k.doc_id, r.amount, collect(p.name) AS people;
