from collections import OrderedDict

from rest_framework.fields import SkipField
from rest_framework.relations import PKOnlyObject


class AllowNoneAtToRepresentationMixin:
    """
    Patch DRF to allow to_representation to be called for fields with None values.
    To be used with ModelSerializers
    """
    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            if isinstance(attribute, PKOnlyObject):
                if attribute.pk is None:
                    ret[field.field_name] = None
            else:
                # >> Override DRF here
                # Deliberately run `to_representation` for `None` values so that
                # custom formatting can be applied.
                ret[field.field_name] = field.to_representation(attribute)

        return ret
