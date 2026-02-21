import base64
import logging
import os

_logger = logging.getLogger(__name__)


def _post_init_hook(env):
    """Set ISIC logo as default company logo on module installation."""
    logo_path = os.path.join(
        os.path.dirname(__file__),
        "static",
        "src",
        "img",
        "isic_logo.png",
    )
    if os.path.isfile(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read())
        main_company = env.ref("base.main_company", raise_if_not_found=False)
        if main_company:
            main_company.write(
                {
                    "name": "ISIC",
                    "logo": logo_data,
                }
            )
            _logger.info("ISIC logo set on main company")
    else:
        _logger.warning("ISIC logo not found at %s", logo_path)
