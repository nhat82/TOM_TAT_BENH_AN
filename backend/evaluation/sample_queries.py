"""
Vietnamese sample queries for RAGAS evaluation.

Ground truths are derived directly from Sample_20BN.csv fields.
Queries without ground_truth use reference-free metrics only
(faithfulness + answer_relevancy + citation_accuracy).

Patient population: oncology cases (cancer hospital dataset).
"""

SAMPLE_QUERIES: list[dict] = [
    # ── Diagnosis ─────────────────────────────────────────────────────────────
    {
        "patient_id": "BN0003",
        "question": "Chẩn đoán ra viện của bệnh nhân là gì?",
        "ground_truth": "Ung thư đại tràng Sigma pT4N2M1 - giai đoạn IV",
        "category": "diagnosis",
    },
    {
        "patient_id": "BN0064",
        "question": "Bệnh nhân được chẩn đoán mắc bệnh gì và giai đoạn nào?",
        "ground_truth": "Ung thư phổi phải T4N2M1, di căn gan, phổi, xương, giai đoạn IV",
        "category": "diagnosis",
    },
    {
        "patient_id": "BN0056",
        "question": "Chẩn đoán chính lúc ra viện của bệnh nhân là gì?",
        "ground_truth": "Ung thư tụy pT4N0M0 giai đoạn III",
        "category": "diagnosis",
    },
    {
        "patient_id": "BN0051",
        "question": "Bệnh nhân nhập viện với chẩn đoán ban đầu là gì?",
        "ground_truth": "Ung thư trực tràng trung bình cT3NxM1 có di căn phổi và gan, giai đoạn IV; kèm hẹp môn vị",
        "category": "diagnosis",
    },

    # ── Reason for admission ──────────────────────────────────────────────────
    {
        "patient_id": "BN0056",
        "question": "Lý do bệnh nhân đến khám ban đầu là gì?",
        "ground_truth": "U đầu tụy nghi K biểu mô tuyến tụy, sỏi đường mật trong gan",
        "category": "reason_for_admission",
    },
    {
        "patient_id": "BN0052",
        "question": "Lý do bệnh nhân đến khám là gì?",
        "ground_truth": "U ác của phế quản và phổi, đau lưng, suy kiệt, táo bón",
        "category": "reason_for_admission",
    },
    {
        "patient_id": "BN0003",
        "question": "Tại sao bệnh nhân được nhập viện?",
        "ground_truth": "Ung thư đại tràng, tiểu máu",
        "category": "reason_for_admission",
    },

    # ── Discharge plan / treatment direction ──────────────────────────────────
    {
        "patient_id": "BN0064",
        "question": "Hướng điều trị tiếp theo khi ra viện của bệnh nhân là gì?",
        "ground_truth": "Điều trị giảm nhẹ, giảm đau morphine, chăm sóc triệu chứng",
        "category": "discharge_plan",
    },
    {
        "patient_id": "BN0051",
        "question": "Bệnh nhân được chuyển đến đâu và kế hoạch điều trị tiếp theo là gì?",
        "ground_truth": "Chuyển Bệnh viện Thanh Nhàn điều trị, hẹn ổn định quay lại Bệnh viện Ung bướu Hà Nội",
        "category": "discharge_plan",
    },
    {
        "patient_id": "BN0003",
        "question": "Bệnh nhân ra viện theo hướng nào?",
        "ground_truth": "Bệnh nhân không tiếp tục điều trị, xin ra viện",
        "category": "discharge_plan",
    },

    # ── Vitals ────────────────────────────────────────────────────────────────
    {
        "patient_id": "BN0003",
        "question": "Các chỉ số sinh hiệu của bệnh nhân được ghi nhận như thế nào?",
        "ground_truth": "Huyết áp tâm thu 164 mmHg, cân nặng 55 kg, chiều cao 152 cm",
        "category": "vitals",
    },
    {
        "patient_id": "BN0051",
        "question": "Huyết áp và cân nặng của bệnh nhân là bao nhiêu?",
        "ground_truth": "Huyết áp tâm thu 120 mmHg, cân nặng 52 kg, chiều cao 170 cm",
        "category": "vitals",
    },

    # ── Medications ───────────────────────────────────────────────────────────
    {
        "patient_id": "BN0064",
        "question": "Bệnh nhân đã được sử dụng những loại thuốc nào trong quá trình điều trị?",
        "ground_truth": None,
        "category": "medication",
    },
    {
        "patient_id": "BN0056",
        "question": "Liệt kê các thuốc chính được sử dụng cho bệnh nhân.",
        "ground_truth": None,
        "category": "medication",
    },

    # ── Imaging / lab ─────────────────────────────────────────────────────────
    {
        "patient_id": "BN0003",
        "question": "Kết quả chụp chiếu hình ảnh của bệnh nhân cho thấy điều gì?",
        "ground_truth": "Không thấy bất thường trên phim chụp",
        "category": "imaging",
    },
    {
        "patient_id": "BN0056",
        "question": "Kết quả chẩn đoán hình ảnh dạ dày của bệnh nhân như thế nào?",
        "ground_truth": "Miệng nối dạ dày lưu thông tốt xuống các quai ruột",
        "category": "imaging",
    },
    {
        "patient_id": "BN0052",
        "question": "Kết quả xét nghiệm máu của bệnh nhân có điểm nào đáng chú ý không?",
        "ground_truth": None,
        "category": "labs",
    },

    # ── Hallucination guard — questions with no answer in the record ──────────
    {
        "patient_id": "BN0003",
        "question": "Bệnh nhân có tiền sử dị ứng thuốc không?",
        "ground_truth": "Thông tin về dị ứng thuốc không có trong hồ sơ",
        "category": "hallucination_guard",
    },
    {
        "patient_id": "BN0064",
        "question": "Bệnh nhân có phẫu thuật lần nào trước đây không?",
        "ground_truth": "Thông tin về tiền sử phẫu thuật không có trong hồ sơ",
        "category": "hallucination_guard",
    },
]
