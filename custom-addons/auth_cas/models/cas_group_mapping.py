from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CASGroupMapping(models.Model):
    """Mapping des attributs CAS vers les groupes Odoo"""

    _name = "auth.cas.group.mapping"
    _description = "CAS Group Mapping"
    _order = "sequence, id"

    name = fields.Char(string="Name", compute="_compute_name", store=True)

    sequence = fields.Integer(string="Sequence", default=10)

    active = fields.Boolean(string="Active", default=True)

    cas_attribute = fields.Selection(
        selection=[
            ("eduPersonAffiliation", "eduPersonAffiliation"),
            ("employeeType", "employeeType"),
            ("memberOf", "memberOf (LDAP Group DN)"),
            ("eduPersonEntitlement", "eduPersonEntitlement"),
            ("role", "role"),
            ("affiliation", "affiliation"),
            ("department", "department"),
        ],
        string="CAS Attribute",
        required=True,
        help="L'attribut CAS à matcher",
    )

    cas_value = fields.Char(
        string="CAS Value",
        required=True,
        help="La valeur attendue de l'attribut CAS (peut utiliser des wildcards avec *)",
    )

    cas_value_is_regex = fields.Boolean(
        string="Value is Regex", default=False, help="Interpréter la valeur comme une expression régulière"
    )

    odoo_group_id = fields.Many2one(
        "res.groups",
        string="Odoo Group",
        required=True,
        ondelete="cascade",
        help="Le groupe Odoo à attribuer si le mapping correspond",
    )

    is_internal_user = fields.Boolean(
        string="Internal User",
        default=False,
        help="Si coché, l'utilisateur sera créé comme utilisateur interne, sinon comme utilisateur portail",
    )

    provider_id = fields.Many2one(
        "auth.oauth.provider",
        string="CAS Provider",
        domain=[("is_cas_provider", "=", True)],
        help="Si défini, ce mapping ne s'applique qu'à ce provider CAS",
    )

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    notes = fields.Text(string="Notes", help="Notes internes sur ce mapping")

    @api.depends("cas_attribute", "cas_value", "odoo_group_id")
    def _compute_name(self):
        for mapping in self:
            if mapping.cas_attribute and mapping.cas_value and mapping.odoo_group_id:
                mapping.name = f"{mapping.cas_attribute}={mapping.cas_value} → {mapping.odoo_group_id.name}"
            else:
                mapping.name = _("New Mapping")

    @api.constrains("cas_value", "cas_value_is_regex")
    def _check_regex_valid(self):
        """Vérifie que les regex sont valides"""
        import re

        for mapping in self:
            if mapping.cas_value_is_regex:
                try:
                    re.compile(mapping.cas_value)
                except re.error as e:
                    raise ValidationError(
                        _("Invalid regex pattern '%(pattern)s': %(error)s")
                        % {"pattern": mapping.cas_value, "error": str(e)}
                    )

    def match_cas_attributes(self, cas_attributes):
        """
        Vérifie si les attributs CAS correspondent à ce mapping.

        :param cas_attributes: dict des attributs retournés par CAS
        :return: True si le mapping correspond, False sinon
        """
        import re

        self.ensure_one()

        # Récupérer la valeur de l'attribut CAS
        attr_value = cas_attributes.get(self.cas_attribute)
        if not attr_value:
            return False

        # Normaliser en liste si c'est une valeur unique
        attr_values = [attr_value] if isinstance(attr_value, str) else list(attr_value)

        # Vérifier chaque valeur
        for value in attr_values:
            if self.cas_value_is_regex:
                if re.match(self.cas_value, value):
                    return True
            else:
                # Support des wildcards simples
                pattern = self.cas_value.replace("*", ".*")
                if re.fullmatch(pattern, value, re.IGNORECASE):
                    return True

        return False

    @api.model
    def resolve_groups_from_cas(self, cas_attributes, provider_id=None):
        """
        Résout les groupes Odoo à partir des attributs CAS.

        :param cas_attributes: dict des attributs CAS
        :param provider_id: ID du provider CAS (optionnel)
        :return: tuple (group_ids, is_internal_user)
        """
        domain = [("active", "=", True)]
        if provider_id:
            domain.append("|")
            domain.append(("provider_id", "=", False))
            domain.append(("provider_id", "=", provider_id))

        mappings = self.search(domain, order="sequence")

        group_ids = set()
        is_internal = False

        for mapping in mappings:
            if mapping.match_cas_attributes(cas_attributes):
                group_ids.add(mapping.odoo_group_id.id)
                if mapping.is_internal_user:
                    is_internal = True

        return list(group_ids), is_internal
