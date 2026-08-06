"""
Unit & Integration Tests for End-to-End Metadata Propagation.
Verifies that metadata (document_type, pmid, source_url, publication_year, etc.)
survives the pipeline from Adapter -> Schema -> Chunker -> Extractor without
fabricating missing fields (e.g. fake dates, fake publishers, fake journals).
"""
import pytest
from app.services.dataset_construction.adapters.pubmedqa import PubMedQAAdapter
from app.services.dataset_construction.adapters.hotpotqa import HotpotQAAdapter
from app.services.dataset_construction.adapters.techqa import TechQAAdapter
from app.services.document_processor import chunk_document
from app.services.rrfe.extractors.source_credibility import SourceCredibilityExtractor


class TestMetadataPropagation:
    credibility_extractor = SourceCredibilityExtractor()

    def test_pubmedqa_metadata_propagation_with_pmid(self):
        """PubMedQA with PMID derived from record_id pubmedqa_39085."""
        adapter = PubMedQAAdapter()
        raw_record = {
            "id": "pubmedqa_39085",
            "question": "Is trial valid?",
            "response": "Yes",
            "documents": ["Randomized controlled trial evidence..."],
            "metadata": {
                "source": "PubMedQA",
                "url": "https://pubmedqa.github.io/",
                "publication_year": 2024
            }
        }
        
        # 1. Adapter step
        unified = adapter.extract(raw_record)
        assert unified.metadata["document_type"] == "academic_paper"
        assert unified.metadata["pmid"] == "39085"
        assert unified.metadata["source_url"] == "https://pubmed.ncbi.nlm.nih.gov/39085/"
        assert unified.metadata["publication_year"] == 2024
        # Verify NO fabricated fields exist:
        assert "publisher" not in unified.metadata
        assert "journal" not in unified.metadata
        assert "publication_date" not in unified.metadata

        # 2. Chunker step
        chunks = chunk_document(
            unified.documents[0],
            filename="pubmedqa_doc.txt",
            extra_metadata=unified.metadata
        )
        assert len(chunks) == 1
        chunk_meta = chunks[0].metadata
        assert chunk_meta["document_type"] == "academic_paper"
        assert chunk_meta["pmid"] == "39085"
        assert chunk_meta["source_url"] == "https://pubmed.ncbi.nlm.nih.gov/39085/"

        # 3. Extractor step
        res = self.credibility_extractor.extract("q", chunks)
        # academic_paper base (0.95) + trusted_domain (.ncbi. in source_url +0.04) - no_date (-0.05) = 0.94
        assert res.score == 0.94
        assert "type=academic_paper(0.95)" in res.reason
        assert "trusted_domain+0.04" in res.reason
        assert "no_date-0.05" in res.reason

    def test_hotpotqa_metadata_propagation(self):
        """HotpotQA metadata propagation without fabrication."""
        adapter = HotpotQAAdapter()
        raw_record = {
            "id": "5a732ab25542991f29ee2d25",
            "question": "Who founded Rome?",
            "response": "Romulus",
            "documents": ["Romulus and Remus founded Rome in 753 BC."],
            "metadata": {
                "source": "HotpotQA",
                "url": "https://hotpotqa.github.io/",
                "publication_year": 2024
            }
        }
        
        unified = adapter.extract(raw_record)
        assert unified.metadata["document_type"] == "official_report"
        assert unified.metadata["source_url"] == "https://hotpotqa.github.io/"
        assert "publisher" not in unified.metadata

        chunks = chunk_document(
            unified.documents[0],
            filename="hotpotqa_doc.txt",
            extra_metadata=unified.metadata
        )
        res = self.credibility_extractor.extract("q", chunks)
        # official_report (0.85) - no_date (-0.05) = 0.80
        assert res.score == 0.80
        assert "type=official_report(0.85)" in res.reason
        assert "no_date-0.05" in res.reason

    def test_techqa_metadata_propagation(self):
        """TechQA metadata propagation."""
        adapter = TechQAAdapter()
        raw_record = {
            "id": "t_303",
            "question_text": "How to configure DB2?",
            "answer": "Set DB2COMM=tcpip",
            "documents": [{"text": "DB2 Configuration Guide page 12."}],
            "metadata": {
                "url": "https://www.ibm.com/support"
            }
        }
        
        unified = adapter.extract(raw_record)
        assert unified.metadata["document_type"] == "technical_documentation"
        assert unified.metadata["source_url"] == "https://www.ibm.com/support"

        chunks = chunk_document(
            unified.documents[0],
            filename="techqa_doc.txt",
            extra_metadata=unified.metadata
        )
        res = self.credibility_extractor.extract("q", chunks)
        # technical_documentation (0.80) - no_date (-0.05) = 0.75
        assert res.score == 0.75

    def test_untyped_doc_graceful_fallback(self):
        """Doc with no extra metadata falls back to unknown (0.45)."""
        chunks = chunk_document("Plain text document", filename="untyped_doc.txt")
        assert "document_type" not in chunks[0].metadata
        res = self.credibility_extractor.extract("q", chunks)
        assert res.score == 0.45
        assert "type=unknown(0.50)" in res.reason
