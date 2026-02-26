# Compatibility shim for odoo_test_helper.FakeModelLoader on Odoo 19.
# Odoo 19 changed:
#   Registry.load() signature: load(cr, package) → load(module) where module.name
#   setup_models(cr) → _setup_models__(cr, model_names)
#   _fields is now a mappingproxy (read-only), backed by _fields__ dict
#   __base_classes → _base_classes__

import logging
from unittest import mock

from odoo.release import version_info
from odoo.tools import OrderedSet
from odoo.tools.func import reset_cached_properties

from odoo_test_helper import FakeModelLoader as _OriginalFakeModelLoader
from odoo_test_helper.fake_model_loader import FakePackage, module_to_models

_ODOO_19 = version_info[0] >= 19
_logger = logging.getLogger(__name__)


class FakeModelLoader(_OriginalFakeModelLoader):
    """FakeModelLoader patched for Odoo 19 Registry API."""

    def backup_registry(self):
        if not _ODOO_19:
            return super().backup_registry()

        self._check_wrong_import()
        self._original_registry = {}
        self._original_module_to_models = {}
        for model_name, model in self.env.registry.models.items():
            self._original_registry[model_name] = {
                "base": model.__bases__,
                "base_classes": model._base_classes__,
                "_fields__": dict(model._fields__),
                "_inherit_children": OrderedSet(model._inherit_children._map.keys()),
                "_inherits_children": set(model._inherits_children),
            }
        for key in module_to_models:
            self._original_module_to_models[key] = list(module_to_models[key])

    def update_registry(self, odoo_models):
        if not _ODOO_19:
            return super().update_registry(odoo_models)

        if hasattr(self.env, "flush_all"):
            self.env.flush_all()

        self._clean_module_to_model()
        for model in odoo_models:
            if model not in module_to_models[self._module_name]:
                module_to_models[self._module_name].append(model)

        with mock.patch.object(self.env.cr, "commit"):
            # Odoo 19: Registry.load(module) — single arg, module.name used
            model_names = self.env.registry.load(FakePackage(self._module_name))
            # Odoo 19: full setup to rebuild all models
            self.env.registry._setup_models__(self.env.cr)
            self.env.registry.init_models(
                self.env.cr, model_names, {"module": self._module_name}
            )

    def restore_registry(self):
        if not _ODOO_19:
            return super().restore_registry()

        # Restore original model classes
        for key in self._original_registry:
            ori = self._original_registry[key]
            model = self.env.registry[key]
            model.__bases__ = ori["base"]
            model._base_classes__ = ori["base_classes"]
            model._inherit_children = ori["_inherit_children"]
            model._inherits_children = ori["_inherits_children"]
            # Restore _fields__ (the actual dict behind _fields mappingproxy)
            model._fields__.clear()
            model._fields__.update(ori["_fields__"])
            # Sync class attributes with restored fields
            for field_name, field_obj in model._fields__.items():
                setattr(model, field_name, field_obj)

        # Delete fake models (those not in the original registry)
        sorted_models = sorted(
            self.env.registry.models.items(),
            key=lambda x: x[1]._inherit_children,
        )
        for name, __ in sorted_models:
            if name not in self._original_registry:
                del self.env.registry.models[name]

        self._clean_module_to_model()

        # Odoo 19: clear cached properties and caches, mark models for re-setup
        reset_cached_properties(self.env.registry)
        for model_cls in self.env.registry.models.values():
            model_cls._setup_done__ = False
        self.env.registry.field_depends.clear()
        self.env.registry.field_depends_context.clear()
        self.env.registry._field_trigger_trees.clear()
        self.env.registry._is_modifying_relations.clear()
        for cache in self.env.registry._Registry__caches.values():
            cache.clear()
