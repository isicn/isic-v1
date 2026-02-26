from odoo.addons.auth_cas.controllers.main import CASAuthController
from odoo.tests.common import TransactionCase


class TestCASControllerParsing(TransactionCase):
    """Tests for CAS response parsing (JSON and XML)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = CASAuthController()

    def test_parse_cas_json_success(self):
        """JSON authenticationSuccess is parsed correctly."""
        data = {
            "serviceResponse": {
                "authenticationSuccess": {
                    "user": "prof.test",
                    "attributes": {
                        "mail": "prof@isic.ac.ma",
                        "cn": "Prof Test",
                        "employeeType": "faculty",
                        "memberOf": ["cn=enseignants,ou=Groups,dc=isic,dc=ac,dc=ma"],
                    },
                }
            }
        }
        result = self.controller._parse_cas_json_response(data)
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "prof.test")
        self.assertEqual(result["uid"], "prof.test")
        self.assertEqual(result["mail"], "prof@isic.ac.ma")
        self.assertEqual(result["employeeType"], "faculty")

    def test_parse_cas_json_failure(self):
        """JSON authenticationFailure returns None."""
        data = {
            "serviceResponse": {
                "authenticationFailure": {
                    "code": "INVALID_TICKET",
                    "description": "Ticket not recognized",
                }
            }
        }
        result = self.controller._parse_cas_json_response(data)
        self.assertIsNone(result)

    def test_parse_cas_xml_success(self):
        """XML with CAS namespace is parsed correctly."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
  <cas:authenticationSuccess>
    <cas:user>prof.test</cas:user>
    <cas:attributes>
      <cas:mail>prof@isic.ac.ma</cas:mail>
      <cas:cn>Prof Test</cas:cn>
      <cas:employeeType>faculty</cas:employeeType>
    </cas:attributes>
  </cas:authenticationSuccess>
</cas:serviceResponse>"""
        result = self.controller._parse_cas_xml_response(xml_text)
        self.assertIsNotNone(result)
        self.assertEqual(result["user"], "prof.test")
        self.assertEqual(result["uid"], "prof.test")
        self.assertEqual(result["mail"], "prof@isic.ac.ma")
        self.assertEqual(result["employeeType"], "faculty")

    def test_parse_cas_xml_failure(self):
        """XML authentication failure returns None."""
        xml_text = """<?xml version="1.0" encoding="UTF-8"?>
<cas:serviceResponse xmlns:cas="http://www.yale.edu/tp/cas">
  <cas:authenticationFailure code="INVALID_TICKET">
    Ticket not recognized
  </cas:authenticationFailure>
</cas:serviceResponse>"""
        result = self.controller._parse_cas_xml_response(xml_text)
        self.assertIsNone(result)

    def test_parse_cas_xml_malformed(self):
        """Malformed XML returns None."""
        result = self.controller._parse_cas_xml_response("<not valid xml")
        self.assertIsNone(result)
