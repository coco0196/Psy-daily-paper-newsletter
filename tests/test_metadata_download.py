import unittest
from unittest.mock import patch

from Paper_metadata_download import _deduplicate_papers, _parse_pubmed_xml_batch, metadata_pilot


class PubMedMetadataTests(unittest.TestCase):
    def test_article_publication_date_precedes_pubmed_index_date_and_doi_is_parsed(self):
        xml = b'''<?xml version="1.0"?>
        <PubmedArticleSet><PubmedArticle>
          <MedlineCitation><PMID>12345</PMID><Article>
            <Journal><ISSN>1438-8871</ISSN><JournalIssue><PubDate><Year>2026</Year><Month>08</Month><Day>30</Day></PubDate></JournalIssue><Title>Journal of Medical Internet Research</Title><ISOAbbreviation>J Med Internet Res</ISOAbbreviation></Journal>
            <ArticleTitle>A mental health intervention</ArticleTitle>
            <ArticleDate DateType="Electronic"><Year>2026</Year><Month>08</Month><Day>24</Day></ArticleDate>
            <Abstract><AbstractText>Abstract text.</AbstractText></Abstract>
          </Article></MedlineCitation>
          <PubmedData><History><PubMedPubDate PubStatus="pubmed"><Year>2026</Year><Month>09</Month><Day>02</Day></PubMedPubDate></History><ArticleIdList><ArticleId IdType="doi">https://doi.org/10.1000/Example</ArticleId></ArticleIdList></PubmedData>
        </PubmedArticle></PubmedArticleSet>'''
        records = _parse_pubmed_xml_batch(xml)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["published_at"], "2026-08-24")
        self.assertEqual(records[0]["publication_date_source"], "article")
        self.assertEqual(records[0]["doi"], "10.1000/example")

    def test_doi_dedup_merges_pubmed_and_crossref_provenance(self):
        papers = [
            {"paper": {"id": "1", "pmid": "1", "doi": "10.1000/example", "title": "A Study", "summary": "x", "authors": [{"name": "Ada Lovelace"}], "journal": "Journal A", "issns": ["1234-5678"], "publishedAt": "2026-08-24", "source": "PubMed", "sources": ["PubMed"]}},
            {"paper": {"id": "10.1000/example", "doi": "https://doi.org/10.1000/Example", "title": "A study.", "summary": "x", "authors": [{"name": "Ada Lovelace"}], "journal": "Journal A", "issns": ["1234-5678"], "publishedAt": "2026-08-24", "source": "Crossref", "sources": ["Crossref"]}},
        ]
        merged = _deduplicate_papers(papers, "test")
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["paper"]["doi"], "10.1000/example")
        self.assertEqual(merged[0]["paper"]["sources"], ["PubMed", "Crossref"])

    def test_same_title_with_different_bibliography_is_not_merged(self):
        papers = [
            {"paper": {"id": "1", "title": "Editorial", "summary": "x", "authors": [{"name": "Ada Lovelace"}], "journal": "Journal A", "issns": ["1111-1111"], "publishedAt": "2026-08-24", "source": "PubMed"}},
            {"paper": {"id": "2", "title": "Editorial", "summary": "x", "authors": [{"name": "Grace Hopper"}], "journal": "Journal B", "issns": ["2222-2222"], "publishedAt": "2026-08-24", "source": "Crossref"}},
        ]
        self.assertEqual(len(_deduplicate_papers(papers, "test")), 2)

    def test_metadata_pilot_does_not_write_or_call_deepseek(self):
        sample = {
            "paper": {
                "id": "1", "pmid": "1", "doi": "10.1000/pilot",
                "title": "A digital mental health intervention for anxiety",
                "summary": "A randomized psychological intervention assessed anxiety and wellbeing.",
                "authors": [{"name": "Ada Lovelace"}],
                "journal": "Journal of Medical Internet Research",
                "issns": ["1438-8871"], "publishedAt": "2026-08-24",
                "source": "PubMed", "sources": ["PubMed"],
            }
        }
        with patch(
            "Paper_metadata_download.download_papers_for_date",
            side_effect=[[sample], []],
        ):
            result = metadata_pilot("2026-08-24", "2026-08-25")
        self.assertEqual(result["mode"], "dry-run")
        self.assertFalse(result["writes_files"])
        self.assertFalse(result["calls_deepseek"])
        self.assertEqual(result["weekly_source_after_dedup"], 1)
        self.assertEqual(result["deepseek_candidate_count"], 1)


if __name__ == "__main__":
    unittest.main()
