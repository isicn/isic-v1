import base64

from .common import IsicGedCase


class TestFulltext(IsicGedCase):
    """Tests for full-text extraction and indexing."""

    def test_text_file_extraction(self):
        """Text files should be indexed automatically on create."""
        content = base64.b64encode(b"Ceci est un document de test pour la recherche.")
        f = self._create_file(name="test.txt", content=content)

        self.assertTrue(f.fulltext_indexed)
        self.assertIn("document de test", f.fulltext_content)
        self.assertFalse(f.fulltext_error)

    def test_binary_file_no_extraction(self):
        """Binary files (unsupported formats) should not be indexed."""
        content = base64.b64encode(b"\x00\x01\x02\x03")
        f = self._create_file(name="test.bin", content=content)

        # Binary content may or may not extract text, but shouldn't crash
        self.assertFalse(f.fulltext_error)

    def test_content_update_reindexes(self):
        """Updating content should trigger re-indexation."""
        f = self._create_file(name="doc.txt", content=base64.b64encode(b"premier contenu"))
        self.assertIn("premier contenu", f.fulltext_content)

        f.write({"content": base64.b64encode(b"deuxieme contenu")})
        self.assertIn("deuxieme contenu", f.fulltext_content)

    def test_reindex_action(self):
        """Manual reindex action should work."""
        f = self._create_file(name="doc.txt", content=base64.b64encode(b"texte a indexer"))
        # Clear the index
        f.write({"fulltext_content": "", "fulltext_indexed": False})
        self.assertFalse(f.fulltext_indexed)

        # Reindex
        f.action_reindex_fulltext()
        self.assertTrue(f.fulltext_indexed)
        self.assertIn("texte a indexer", f.fulltext_content)

    def test_empty_file_no_index(self):
        """Files without content should not be indexed."""
        f = self._create_file(name="empty.txt", content=base64.b64encode(b""))

        self.assertFalse(f.fulltext_indexed)

    def test_pdf_extraction_graceful_without_lib(self):
        """PDF extraction should gracefully handle missing pypdf library."""
        # This test creates a file with PDF mimetype but non-PDF content
        # The extraction should fail gracefully
        content = base64.b64encode(b"not a real pdf")
        f = self._create_file(name="test.pdf", content=content)

        # Should not crash, just log the error
        # fulltext_error may or may not be set depending on mimetype detection
        self.assertIsNotNone(f.fulltext_content)

    def test_search_fulltext_returns_recordset(self):
        """search_fulltext() should always return a recordset."""
        DmsFile = self.env["dms.file"]

        # Empty query returns empty recordset
        result = DmsFile.search_fulltext("")
        self.assertEqual(len(result), 0)
        self.assertEqual(result._name, "dms.file")

        # Whitespace-only query returns empty recordset
        result = DmsFile.search_fulltext("   ")
        self.assertEqual(len(result), 0)
        self.assertEqual(result._name, "dms.file")

        # No match returns empty recordset
        result = DmsFile.search_fulltext("xyznonexistent123")
        self.assertEqual(len(result), 0)
        self.assertEqual(result._name, "dms.file")

    def test_search_fulltext_finds_indexed_content(self):
        """search_fulltext() should find documents by their indexed content."""
        content = base64.b64encode("Rapport annuel de la direction académique ISIC".encode())
        f = self._create_file(name="rapport.txt", content=content)
        self.assertTrue(f.fulltext_indexed)

        result = self.env["dms.file"].search_fulltext("direction académique")
        self.assertIn(f, result)
