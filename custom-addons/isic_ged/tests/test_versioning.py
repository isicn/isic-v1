import base64

from .common import IsicGedCase


class TestVersioning(IsicGedCase):
    """Tests for document versioning."""

    def test_first_upload_no_version(self):
        """Creating a new file should not create a version (no previous content)."""
        f = self._create_file()
        self.assertEqual(f.current_version, 0)
        self.assertEqual(f.version_count, 0)

    def test_content_update_creates_version(self):
        """Updating content should create a version snapshot of the previous content."""
        f = self._create_file(content=base64.b64encode(b"version 1"))
        original_checksum = f.checksum

        # Update content
        f.write({"content": base64.b64encode(b"version 2")})

        self.assertEqual(f.version_count, 1)
        self.assertEqual(f.current_version, 1)

        version = f.version_ids[0]
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.checksum, original_checksum)
        self.assertEqual(version.name, "test_file.pdf")

    def test_multiple_updates_increment_versions(self):
        """Multiple content updates should create sequential versions."""
        f = self._create_file(content=base64.b64encode(b"v1"))
        f.write({"content": base64.b64encode(b"v2")})
        f.write({"content": base64.b64encode(b"v3")})

        self.assertEqual(f.version_count, 2)
        self.assertEqual(f.current_version, 2)

        versions = f.version_ids.sorted("version_number")
        self.assertEqual(versions[0].version_number, 1)
        self.assertEqual(versions[1].version_number, 2)

    def test_non_content_write_no_version(self):
        """Writing non-content fields should not create a version."""
        f = self._create_file()
        f.write({"reference": "REF-001"})

        self.assertEqual(f.version_count, 0)
        self.assertEqual(f.current_version, 0)

    def test_restore_version(self):
        """Restoring a version should save current state and restore old content."""
        f = self._create_file(content=base64.b64encode(b"original content"))
        f.write({"content": base64.b64encode(b"new content")})

        self.assertEqual(f.version_count, 1)
        version_to_restore = f.version_ids[0]

        # Restore
        f.with_context(restore_version_id=version_to_restore.id).action_restore_version()

        # Current content should be restored
        self.assertEqual(base64.b64decode(f.content), b"original content")
        # Should have created another version (saving "new content" before restore)
        self.assertEqual(f.version_count, 2)

    def test_skip_version_context_flag(self):
        """The _isic_skip_version context flag should prevent version creation."""
        f = self._create_file(content=base64.b64encode(b"v1"))
        f.with_context(_isic_skip_version=True).write({"content": base64.b64encode(b"v2")})

        self.assertEqual(f.version_count, 0)

    def test_version_author(self):
        """Version should record the author."""
        f = self._create_file(content=base64.b64encode(b"v1"))
        f.write({"content": base64.b64encode(b"v2")})

        version = f.version_ids[0]
        self.assertEqual(version.author_id, self.env.user)

    def test_version_display_name(self):
        """Version display_name should include version number and date."""
        f = self._create_file(content=base64.b64encode(b"v1"))
        f.write({"content": base64.b64encode(b"v2")})

        version = f.version_ids[0]
        self.assertIn("v1", version.display_name)
