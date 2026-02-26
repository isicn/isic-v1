from odoo.exceptions import ValidationError

from .common import CASTestCase


class TestCASGroupMappingMatch(CASTestCase):
    """Tests for CAS group mapping attribute matching."""

    def test_match_exact_value(self):
        """Exact value match."""
        mapping = self._create_mapping(cas_attribute="employeeType", cas_value="faculty")
        self.assertTrue(mapping.match_cas_attributes({"employeeType": "faculty"}))

    def test_match_wildcard(self):
        """Wildcard pattern matches."""
        mapping = self._create_mapping(cas_attribute="memberOf", cas_value="cn=enseignants,*")
        attrs = {"memberOf": "cn=enseignants,ou=Groups,dc=isic,dc=ac,dc=ma"}
        self.assertTrue(mapping.match_cas_attributes(attrs))

    def test_match_regex(self):
        """Regex mode matches."""
        mapping = self._create_mapping(
            cas_attribute="memberOf",
            cas_value=r"cn=direction,ou=Groups,.*",
            cas_value_is_regex=True,
        )
        attrs = {"memberOf": "cn=direction,ou=Groups,dc=isic,dc=ac,dc=ma"}
        self.assertTrue(mapping.match_cas_attributes(attrs))

    def test_match_case_insensitive(self):
        """Wildcard match is case-insensitive."""
        mapping = self._create_mapping(cas_attribute="employeeType", cas_value="Faculty")
        self.assertTrue(mapping.match_cas_attributes({"employeeType": "faculty"}))

    def test_match_list_attribute(self):
        """Attribute as a list (memberOf with multiple values)."""
        mapping = self._create_mapping(cas_attribute="memberOf", cas_value="cn=enseignants,*")
        attrs = {
            "memberOf": [
                "cn=staff,ou=Groups,dc=isic,dc=ac,dc=ma",
                "cn=enseignants,ou=Groups,dc=isic,dc=ac,dc=ma",
            ]
        }
        self.assertTrue(mapping.match_cas_attributes(attrs))

    def test_match_no_match(self):
        """Different value does not match."""
        mapping = self._create_mapping(cas_attribute="employeeType", cas_value="faculty")
        self.assertFalse(mapping.match_cas_attributes({"employeeType": "student"}))

    def test_match_missing_attribute(self):
        """Missing attribute does not match."""
        mapping = self._create_mapping(cas_attribute="employeeType", cas_value="faculty")
        self.assertFalse(mapping.match_cas_attributes({"role": "teacher"}))

    def test_invalid_regex_raises(self):
        """Invalid regex raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._create_mapping(
                cas_value="[invalid(regex",
                cas_value_is_regex=True,
            )


class TestCASGroupMappingResolve(CASTestCase):
    """Tests for resolve_groups_from_cas method."""

    def test_resolve_groups_single_match(self):
        """One matching mapping returns one group."""
        self._create_mapping(
            cas_attribute="employeeType",
            cas_value="faculty",
            odoo_group_id=self.group_enseignant.id,
            is_internal_user=True,
        )
        group_ids, is_internal = self.CASMapping.resolve_groups_from_cas({"employeeType": "faculty"})
        self.assertIn(self.group_enseignant.id, group_ids)
        self.assertTrue(is_internal)

    def test_resolve_groups_multiple_matches(self):
        """Multiple matching mappings return multiple groups."""
        self._create_mapping(
            cas_attribute="employeeType",
            cas_value="faculty",
            odoo_group_id=self.group_enseignant.id,
            is_internal_user=True,
            sequence=10,
        )
        self._create_mapping(
            cas_attribute="memberOf",
            cas_value="cn=scolarite,*",
            odoo_group_id=self.group_scolarite.id,
            is_internal_user=True,
            sequence=20,
        )
        group_ids, is_internal = self.CASMapping.resolve_groups_from_cas(
            {
                "employeeType": "faculty",
                "memberOf": "cn=scolarite,ou=Groups,dc=isic,dc=ac,dc=ma",
            }
        )
        self.assertIn(self.group_enseignant.id, group_ids)
        self.assertIn(self.group_scolarite.id, group_ids)
        self.assertTrue(is_internal)

    def test_resolve_groups_is_internal(self):
        """is_internal_user=True on any mapping sets internal flag."""
        self._create_mapping(
            cas_attribute="employeeType",
            cas_value="faculty",
            is_internal_user=True,
        )
        _, is_internal = self.CASMapping.resolve_groups_from_cas({"employeeType": "faculty"})
        self.assertTrue(is_internal)

    def test_resolve_groups_provider_filter(self):
        """Provider filter restricts which mappings are checked."""
        other_cas_url = "https://other.cas.test/cas"
        other_provider = self.Provider.create(
            {
                "name": "Other CAS",
                "is_cas_provider": True,
                "cas_server_url": other_cas_url,
                "auth_endpoint": f"{other_cas_url}/oauth2.0/authorize",
                "validation_endpoint": f"{other_cas_url}/oauth2.0/profile",
                "client_id": "other_client",
                "enabled": True,
                "body": "Other",
            }
        )
        # Mapping for specific provider only, using a unique attribute+value
        # not present in default data mappings
        self._create_mapping(
            cas_attribute="department",
            cas_value="test_only_dept",
            odoo_group_id=self.group_scolarite.id,
            provider_id=other_provider.id,
        )
        # Should NOT match when querying with our test provider
        group_ids, _ = self.CASMapping.resolve_groups_from_cas(
            {"department": "test_only_dept"}, provider_id=self.cas_provider.id
        )
        self.assertNotIn(self.group_scolarite.id, group_ids)
