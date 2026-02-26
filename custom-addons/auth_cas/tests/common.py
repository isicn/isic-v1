from odoo.tests.common import TransactionCase


class CASTestCase(TransactionCase):
    """Common setup for auth_cas tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CASMapping = cls.env["auth.cas.group.mapping"]
        cls.Provider = cls.env["auth.oauth.provider"]

        # CAS provider — provide auth_endpoint/validation_endpoint explicitly
        # because onchange doesn't fire in ORM create()
        cas_url = "https://cas.test.isic.ma/cas"
        cls.cas_provider = cls.Provider.create(
            {
                "name": "Test CAS",
                "is_cas_provider": True,
                "cas_server_url": cas_url,
                "auth_endpoint": f"{cas_url}/oauth2.0/authorize",
                "validation_endpoint": f"{cas_url}/oauth2.0/profile",
                "client_id": "test_client",
                "client_secret": "test_secret",
                "enabled": True,
                "body": "CAS Login",
                "css_class": "fa fa-university",
                "cas_attribute_map": '{"login": "uid", "email": "mail", "name": "cn"}',
            }
        )

        # ISIC groups references
        cls.group_enseignant = cls.env.ref("isic_base.group_isic_enseignant")
        cls.group_scolarite = cls.env.ref("isic_base.group_isic_scolarite")
        cls.group_direction = cls.env.ref("isic_base.group_isic_direction")
        cls.group_etudiant = cls.env.ref("isic_base.group_isic_etudiant")

    @classmethod
    def _create_mapping(cls, **kwargs):
        """Helper to create a CAS group mapping."""
        vals = {
            "cas_attribute": "employeeType",
            "cas_value": "faculty",
            "odoo_group_id": cls.group_enseignant.id,
            "is_internal_user": True,
            "sequence": 10,
        }
        vals.update(kwargs)
        return cls.CASMapping.create(vals)
