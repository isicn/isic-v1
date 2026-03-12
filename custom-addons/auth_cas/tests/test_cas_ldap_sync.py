"""Tests for CAS → LDAP attribute sync on res.partner."""

from .common import CASTestCase


class TestCASLdapSync(CASTestCase):
    """Test _cas_sync_partner_fields with various LDAP attribute payloads."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._create_mapping(
            cas_attribute="employeeType",
            cas_value="faculty",
            odoo_group_id=cls.group_enseignant.id,
            is_internal_user=True,
            sequence=10,
        )

    def _signin_and_get_user(self, validation):
        """Helper: CAS signin and return the created/updated user."""
        login = self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        return self.env["res.users"].sudo().search([("login", "=", login)])

    # ------------------------------------------------------------------
    # Name sync: cn, givenName, sn
    # ------------------------------------------------------------------
    def test_sync_name_from_givenname_sn(self):
        """givenName + sn → partner.name (priority over cn)."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.name1",
                "user": "sync.name1",
                "mail": "name1@isic.ac.ma",
                "cn": "Old Name",
                "givenName": "Abdellatif",
                "sn": "Bensfia",
                "employeeType": "faculty",
            }
        )
        self.assertEqual(user.partner_id.name, "Abdellatif Bensfia")

    def test_sync_name_from_cn_fallback(self):
        """cn → partner.name when givenName/sn not both present."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.name2",
                "user": "sync.name2",
                "mail": "name2@isic.ac.ma",
                "cn": "Mohammed El Amrani",
                "employeeType": "faculty",
            }
        )
        self.assertEqual(user.partner_id.name, "Mohammed El Amrani")

    def test_sync_name_update_on_relogin(self):
        """Name is updated on subsequent CAS logins."""
        validation = {
            "uid": "sync.name3",
            "user": "sync.name3",
            "mail": "name3@isic.ac.ma",
            "cn": "Initial Name",
            "givenName": "Initial",
            "sn": "Name",
            "employeeType": "faculty",
        }
        user = self._signin_and_get_user(validation)
        self.assertEqual(user.partner_id.name, "Initial Name")

        # Simulate LDAP update + re-login
        validation["givenName"] = "Updated"
        validation["sn"] = "Surname"
        validation["cn"] = "Updated Surname"
        self.env["res.users"].sudo()._cas_signin(self.cas_provider, validation, {})
        user.invalidate_recordset()
        self.assertEqual(user.partner_id.name, "Updated Surname")

    # ------------------------------------------------------------------
    # Basic sync: email, function, enseignant flag
    # ------------------------------------------------------------------
    def test_sync_email(self):
        """LDAP mail → partner.email."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.email",
                "user": "sync.email",
                "mail": "sync.email@isic.ac.ma",
                "cn": "Sync",
                "employeeType": "faculty",
            }
        )
        self.assertEqual(user.partner_id.email, "sync.email@isic.ac.ma")

    def test_sync_function(self):
        """LDAP title → partner.function."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.func",
                "user": "sync.func",
                "mail": "f@isic.ac.ma",
                "cn": "F",
                "employeeType": "faculty",
                "title": "Professeur",
            }
        )
        self.assertEqual(user.partner_id.function, "Professeur")

    def test_sync_is_enseignant_true(self):
        """employeeType=faculty → is_enseignant=True."""
        user = self._signin_and_get_user(
            {"uid": "sync.ens", "user": "sync.ens", "mail": "e@isic.ac.ma", "cn": "E", "employeeType": "faculty"}
        )
        self.assertTrue(user.partner_id.is_enseignant)

    def test_sync_is_enseignant_false(self):
        """employeeType=staff → is_enseignant=False."""
        user = self._signin_and_get_user(
            {"uid": "sync.staff", "user": "sync.staff", "mail": "s@isic.ac.ma", "cn": "S", "employeeType": "staff"}
        )
        self.assertFalse(user.partner_id.is_enseignant)

    # ------------------------------------------------------------------
    # Identity fields: CIN, date_naissance, lieu_naissance, genre
    # ------------------------------------------------------------------
    def test_sync_cin(self):
        """isicCIN → partner.cin."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.cin",
                "user": "sync.cin",
                "mail": "c@isic.ac.ma",
                "cn": "C",
                "employeeType": "faculty",
                "isicCIN": "BE123456",
            }
        )
        self.assertEqual(user.partner_id.cin, "BE123456")

    def test_sync_date_naissance(self):
        """isicDateNaissance (ISO format) → partner.date_naissance."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.dob",
                "user": "sync.dob",
                "mail": "d@isic.ac.ma",
                "cn": "D",
                "employeeType": "faculty",
                "isicDateNaissance": "1985-06-15",
            }
        )
        self.assertEqual(str(user.partner_id.date_naissance), "1985-06-15")

    def test_sync_date_naissance_invalid_format(self):
        """Invalid date format is silently skipped (logged as warning)."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.baddob",
                "user": "sync.baddob",
                "mail": "bd@isic.ac.ma",
                "cn": "BD",
                "employeeType": "faculty",
                "isicDateNaissance": "15/06/1985",
            }
        )
        self.assertFalse(user.partner_id.date_naissance, "Invalid date should not be stored")

    def test_sync_lieu_naissance(self):
        """isicLieuNaissance → partner.lieu_naissance."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.lieu",
                "user": "sync.lieu",
                "mail": "l@isic.ac.ma",
                "cn": "L",
                "employeeType": "faculty",
                "isicLieuNaissance": "Rabat",
            }
        )
        self.assertEqual(user.partner_id.lieu_naissance, "Rabat")

    def test_sync_genre_male(self):
        """isicGenre=M → partner.genre='M'."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.gm",
                "user": "sync.gm",
                "mail": "gm@isic.ac.ma",
                "cn": "GM",
                "employeeType": "faculty",
                "isicGenre": "M",
            }
        )
        self.assertEqual(user.partner_id.genre, "M")

    def test_sync_genre_female_lowercase(self):
        """isicGenre=f → partner.genre='F' (normalized to uppercase)."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.gf",
                "user": "sync.gf",
                "mail": "gf@isic.ac.ma",
                "cn": "GF",
                "employeeType": "faculty",
                "isicGenre": "f",
            }
        )
        self.assertEqual(user.partner_id.genre, "F")

    def test_sync_genre_invalid_skipped(self):
        """Invalid genre value is not stored."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.gbad",
                "user": "sync.gbad",
                "mail": "gb@isic.ac.ma",
                "cn": "GB",
                "employeeType": "faculty",
                "isicGenre": "X",
            }
        )
        self.assertFalse(user.partner_id.genre)

    # ------------------------------------------------------------------
    # Nationalite (ISO code → res.country)
    # ------------------------------------------------------------------
    def test_sync_nationalite(self):
        """isicNationalite=MA → country Morocco."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.nat",
                "user": "sync.nat",
                "mail": "n@isic.ac.ma",
                "cn": "N",
                "employeeType": "faculty",
                "isicNationalite": "MA",
            }
        )
        morocco = self.env["res.country"].search([("code", "=", "MA")], limit=1)
        self.assertEqual(user.partner_id.nationalite_id, morocco)

    def test_sync_nationalite_lowercase(self):
        """isicNationalite=ma → normalized to MA."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.natl",
                "user": "sync.natl",
                "mail": "nl@isic.ac.ma",
                "cn": "NL",
                "employeeType": "faculty",
                "isicNationalite": "ma",
            }
        )
        morocco = self.env["res.country"].search([("code", "=", "MA")], limit=1)
        self.assertEqual(user.partner_id.nationalite_id, morocco)

    def test_sync_nationalite_invalid_code(self):
        """Unknown country code does not crash."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.natx",
                "user": "sync.natx",
                "mail": "nx@isic.ac.ma",
                "cn": "NX",
                "employeeType": "faculty",
                "isicNationalite": "ZZ",
            }
        )
        self.assertFalse(user.partner_id.nationalite_id)

    # ------------------------------------------------------------------
    # Situation familiale — normalization
    # ------------------------------------------------------------------
    def test_sync_situation_celibataire(self):
        """celibataire → celibataire."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.sf1",
                "user": "sync.sf1",
                "mail": "sf1@isic.ac.ma",
                "cn": "SF1",
                "employeeType": "faculty",
                "isicSituationFamiliale": "celibataire",
            }
        )
        self.assertEqual(user.partner_id.situation_familiale, "celibataire")

    def test_sync_situation_mariee_to_marie(self):
        """mariee → marie (female to male form)."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.sf2",
                "user": "sync.sf2",
                "mail": "sf2@isic.ac.ma",
                "cn": "SF2",
                "employeeType": "faculty",
                "isicSituationFamiliale": "mariee",
            }
        )
        self.assertEqual(user.partner_id.situation_familiale, "marie")

    def test_sync_situation_marie_accented(self):
        """marié → marie (accented to normalized)."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.sf3",
                "user": "sync.sf3",
                "mail": "sf3@isic.ac.ma",
                "cn": "SF3",
                "employeeType": "faculty",
                "isicSituationFamiliale": "marié",
            }
        )
        self.assertEqual(user.partner_id.situation_familiale, "marie")

    def test_sync_situation_veuve_to_veuf(self):
        """veuve → veuf."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.sf4",
                "user": "sync.sf4",
                "mail": "sf4@isic.ac.ma",
                "cn": "SF4",
                "employeeType": "faculty",
                "isicSituationFamiliale": "veuve",
            }
        )
        self.assertEqual(user.partner_id.situation_familiale, "veuf")

    def test_sync_situation_divorcee_to_divorce(self):
        """divorcee → divorce."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.sf5",
                "user": "sync.sf5",
                "mail": "sf5@isic.ac.ma",
                "cn": "SF5",
                "employeeType": "faculty",
                "isicSituationFamiliale": "divorcee",
            }
        )
        self.assertEqual(user.partner_id.situation_familiale, "divorce")

    def test_sync_situation_unknown_skipped(self):
        """Unknown situation value is not stored."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.sf6",
                "user": "sync.sf6",
                "mail": "sf6@isic.ac.ma",
                "cn": "SF6",
                "employeeType": "faculty",
                "isicSituationFamiliale": "pacs",
            }
        )
        self.assertFalse(user.partner_id.situation_familiale)

    # ------------------------------------------------------------------
    # Contact fields
    # ------------------------------------------------------------------
    def test_sync_phone(self):
        """telephoneNumber → partner.phone."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.ph",
                "user": "sync.ph",
                "mail": "ph@isic.ac.ma",
                "cn": "PH",
                "employeeType": "faculty",
                "telephoneNumber": "+212537773340",
            }
        )
        self.assertEqual(user.partner_id.phone, "+212537773340")

    def test_sync_mobile(self):
        """mobile → partner.telephone_personnel."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.mob",
                "user": "sync.mob",
                "mail": "mob@isic.ac.ma",
                "cn": "MOB",
                "employeeType": "faculty",
                "mobile": "+212600000000",
            }
        )
        self.assertEqual(user.partner_id.telephone_personnel, "+212600000000")

    def test_sync_address(self):
        """homePostalAddress → partner.adresse_personnelle."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.addr",
                "user": "sync.addr",
                "mail": "addr@isic.ac.ma",
                "cn": "ADDR",
                "employeeType": "faculty",
                "homePostalAddress": "123 Av Allal El Fassi, Rabat",
            }
        )
        self.assertEqual(user.partner_id.adresse_personnelle, "123 Av Allal El Fassi, Rabat")

    # ------------------------------------------------------------------
    # Emergency contact
    # ------------------------------------------------------------------
    def test_sync_emergency_contact_name(self):
        """isicContactUrgenceNom → partner.contact_urgence_nom."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.urg",
                "user": "sync.urg",
                "mail": "urg@isic.ac.ma",
                "cn": "URG",
                "employeeType": "faculty",
                "isicContactUrgenceNom": "Ahmed Test",
            }
        )
        self.assertEqual(user.partner_id.contact_urgence_nom, "Ahmed Test")

    def test_sync_emergency_contact_phone(self):
        """isicContactUrgenceTel → partner.contact_urgence_tel."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.urgt",
                "user": "sync.urgt",
                "mail": "urgt@isic.ac.ma",
                "cn": "URGT",
                "employeeType": "faculty",
                "isicContactUrgenceTel": "+212600111222",
            }
        )
        self.assertEqual(user.partner_id.contact_urgence_tel, "+212600111222")

    # ------------------------------------------------------------------
    # ldap_synced flag
    # ------------------------------------------------------------------
    def test_sync_sets_ldap_synced_flag(self):
        """After sync, partner.ldap_synced is True."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.flag",
                "user": "sync.flag",
                "mail": "flag@isic.ac.ma",
                "cn": "FLAG",
                "employeeType": "faculty",
            }
        )
        self.assertTrue(user.partner_id.ldap_synced)

    # ------------------------------------------------------------------
    # List values from LDAP
    # ------------------------------------------------------------------
    def test_sync_list_value_extracts_first(self):
        """LDAP attribute returned as list → first element used."""
        user = self._signin_and_get_user(
            {
                "uid": "sync.list",
                "user": "sync.list",
                "mail": ["sync.list@isic.ac.ma", "secondary@isic.ac.ma"],
                "cn": "List",
                "employeeType": "faculty",
                "isicCIN": ["AB123", "AB456"],
            }
        )
        self.assertEqual(user.partner_id.cin, "AB123")

    # ------------------------------------------------------------------
    # Full payload (all 15 fields)
    # ------------------------------------------------------------------
    def test_sync_full_payload(self):
        """All LDAP attributes synced in a single signin (name + 15 fields)."""
        morocco = self.env["res.country"].search([("code", "=", "MA")], limit=1)
        user = self._signin_and_get_user(
            {
                "uid": "sync.full",
                "user": "sync.full",
                "cn": "Karim Benjelloun",
                "givenName": "Karim",
                "sn": "Benjelloun",
                "mail": "full@isic.ac.ma",
                "employeeType": "faculty",
                "title": "Directeur adjoint",
                "isicCIN": "CD789012",
                "isicDateNaissance": "1970-03-21",
                "isicLieuNaissance": "Casablanca",
                "isicGenre": "M",
                "isicNationalite": "MA",
                "isicSituationFamiliale": "marie",
                "telephoneNumber": "+212537773340",
                "mobile": "+212661234567",
                "homePostalAddress": "45 Rue Hassan II, Rabat",
                "isicContactUrgenceNom": "Fatima Sync",
                "isicContactUrgenceTel": "+212655000111",
            }
        )
        p = user.partner_id
        self.assertTrue(p.ldap_synced)
        self.assertEqual(p.name, "Karim Benjelloun")
        self.assertEqual(p.email, "full@isic.ac.ma")
        self.assertEqual(p.function, "Directeur adjoint")
        self.assertTrue(p.is_enseignant)
        self.assertEqual(p.cin, "CD789012")
        self.assertEqual(str(p.date_naissance), "1970-03-21")
        self.assertEqual(p.lieu_naissance, "Casablanca")
        self.assertEqual(p.genre, "M")
        self.assertEqual(p.nationalite_id, morocco)
        self.assertEqual(p.situation_familiale, "marie")
        self.assertEqual(p.phone, "+212537773340")
        self.assertEqual(p.telephone_personnel, "+212661234567")
        self.assertEqual(p.adresse_personnelle, "45 Rue Hassan II, Rabat")
        self.assertEqual(p.contact_urgence_nom, "Fatima Sync")
        self.assertEqual(p.contact_urgence_tel, "+212655000111")
