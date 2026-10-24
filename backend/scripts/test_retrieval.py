import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.rag.retrieval import retrieval_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("test_retrieval")

def run_tests():
    print("=" * 60)
    print("  TaxEase — Sprint 3: Retrieval Service Verification")
    print("=" * 60)

    # 1. Test vector collection status
    status = retrieval_service.get_status()
    print("\n[1] Vector Collection Status:")
    for k, v in status.items():
        print(f"    - {k}: {v}")

    assert status["status"] in ("green", "CollectionStatus.GREEN"), f"Unexpected status: {status['status']}"
    assert status["points_count"] == 4082, f"Expected 4082 points, got {status['points_count']}"
    print("    [PASS] Qdrant collection is online with all 4,082 chunks.")

    # 2. Test semantic query: Section 80C
    print("\n[2] Semantic Query: 'Deductions for investments under Section 80C'")
    chunks_80c = retrieval_service.retrieve_context(
        query="Deductions for investments under Section 80C life insurance and provident fund",
        top_k=3
    )
    print(f"    Retrieved {len(chunks_80c)} chunks:")
    for i, chunk in enumerate(chunks_80c, 1):
        print(f"    Chunk {i}: Score={chunk.score:.4f} | Section={chunk.metadata.section_number} | Page={chunk.metadata.page_number}")
        print(f"    Preview: {chunk.text[:120]}...\n")
    assert len(chunks_80c) > 0, "No chunks returned for 80C query!"
    print("    [PASS] 80C semantic retrieval succeeded.")

    # 3. Test semantic query: Section 80D (Health Insurance)
    print("\n[3] Semantic Query: 'Health insurance deduction Section 80D for senior citizens'")
    chunks_80d = retrieval_service.retrieve_context(
        query="Health insurance deduction Section 80D for senior citizens",
        top_k=3
    )
    print(f"    Retrieved {len(chunks_80d)} chunks:")
    for i, chunk in enumerate(chunks_80d, 1):
        print(f"    Chunk {i}: Score={chunk.score:.4f} | Section={chunk.metadata.section_number} | Page={chunk.metadata.page_number}")
        print(f"    Preview: {chunk.text[:120]}...\n")
    assert len(chunks_80d) > 0, "No chunks returned for 80D query!"
    print("    [PASS] 80D semantic retrieval succeeded.")

    # 4. Test Section Filtering
    print("\n[4] Section-Filtered Query: 'limits' with section_filter='80C'")
    chunks_filtered = retrieval_service.retrieve_context(
        query="limits on deduction",
        top_k=3,
        section_filter="80C"
    )
    print(f"    Retrieved {len(chunks_filtered)} chunks filtered by section 80C:")
    for chunk in chunks_filtered:
        print(f"    Section={chunk.metadata.section_number} | Score={chunk.score:.4f} | Page={chunk.metadata.page_number}")
        assert chunk.metadata.section_number == "80C", f"Expected section 80C, got {chunk.metadata.section_number}"
    print("    [PASS] Section filtering verified.")

    # 5. Direct section lookup
    print("\n[5] Direct Section Lookup: ['80C', '80D']")
    direct_chunks = retrieval_service.retrieve_for_sections(section_ids=["80C", "80D"], top_k=4)
    print(f"    Retrieved {len(direct_chunks)} chunks for sections 80C & 80D:")
    for c in direct_chunks:
        print(f"    Section={c.metadata.section_number} | Page={c.metadata.page_number} | Title={c.metadata.chapter_title}")
    assert len(direct_chunks) > 0, "Direct section lookup returned no chunks!"
    print("    [PASS] Direct section lookup verified.")

    print("\n" + "=" * 60)
    print("  All Sprint 3 Retrieval Tests PASSED Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
