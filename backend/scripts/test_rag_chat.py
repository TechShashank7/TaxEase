import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from main import app

def test_rag_chat():
    print("=" * 60)
    print("  TaxEase — Sprint 4: RAG Orchestration & Citations Test")
    print("=" * 60)

    client = TestClient(app)

    # 1. Test Chat Endpoint with RAG Grounding
    print("\n[1] Testing POST /api/v1/ai/chat with Section 80C query...")
    payload = {
        "message": "What is the maximum limit for Section 80C deductions under the Income Tax Act?",
        "context": "Name: Rahul, Age: 30, Annual Income: 1200000, Tax Regime: Old"
    }
    res = client.post("/api/v1/ai/chat", json=payload)
    print(f"    HTTP Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"

    data = res.json()
    reply = data.get("reply", "")
    citations = data.get("citations", [])

    print(f"    AI Reply ({len(reply)} chars):")
    print(f"    {reply[:350]}...\n")

    print(f"    Citations Attached: {len(citations)}")
    for i, cit in enumerate(citations, 1):
        print(f"    [{i}] Section: {cit.get('section_number')} | Page: {cit.get('page_number')} | Score: {cit.get('relevance_score')}")
        print(f"        Excerpt: {cit.get('excerpt')[:100]}...")

    assert len(citations) > 0, "Expected at least 1 citation attached to RAG response!"
    assert any("80C" in str(c.get("section_number")) for c in citations), "Expected Section 80C in citations!"
    print("\n    [PASS] Chat endpoint successfully returned grounded answer with citations!")

    # 2. Test Explain Endpoint with Recommendations
    print("\n[2] Testing POST /api/v1/ai/explain with mock recommendations...")
    explain_payload = {
        "name": "Rahul",
        "total_benefit": 45000.0,
        "recommendations": [
            {
                "scheme_id": "sec_80c",
                "scheme_name": "Section 80C (PPF/ELSS/EPF)",
                "category": "Deduction",
                "priority_score": 10,
                "triggered_rule": "sec_80c_unclaimed",
                "threshold_used": 150000.0,
                "current_investment": 50000.0,
                "gap_amount": 100000.0,
                "potential_tax_benefit": 31200.0,
                "recommendation": "Invest remaining ₹1,00,000 in PPF/ELSS to claim full 80C benefit.",
                "explanation": "Section 80C allows deductions up to ₹1.5 Lakh.",
                "references": ["Income Tax Act, 1961 - Section 80C"]
            },
            {
                "scheme_id": "sec_80d",
                "scheme_name": "Section 80D (Health Insurance)",
                "category": "Health",
                "priority_score": 8,
                "triggered_rule": "sec_80d_unclaimed",
                "threshold_used": 25000.0,
                "current_investment": 0.0,
                "gap_amount": 25000.0,
                "potential_tax_benefit": 7800.0,
                "recommendation": "Purchase health insurance to claim up to ₹25,000 under Section 80D.",
                "explanation": "Health insurance premium deduction.",
                "references": ["Income Tax Act, 1961 - Section 80D"]
            }
        ]
    }
    exp_res = client.post("/api/v1/ai/explain", json=explain_payload)
    print(f"    HTTP Status: {exp_res.status_code}")
    assert exp_res.status_code == 200, f"Expected 200, got {exp_res.status_code}"

    exp_data = exp_res.json()
    exp_text = exp_data.get("explanation", "")
    exp_cits = exp_data.get("citations", [])

    print(f"    Explanation ({len(exp_text)} chars):")
    print(f"    {exp_text[:350]}...\n")

    print(f"    Citations Attached: {len(exp_cits)}")
    for i, cit in enumerate(exp_cits, 1):
        print(f"    [{i}] Section: {cit.get('section_number')} | Page: {cit.get('page_number')} | Score: {cit.get('relevance_score')}")

    assert len(exp_cits) > 0, "Expected citations in explanation endpoint!"
    print("\n    [PASS] Explain endpoint successfully returned statutory explanation with citations!")

    print("\n" + "=" * 60)
    print("  Sprint 4 Orchestration Tests PASSED Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_rag_chat()
