from dataclasses import dataclass
from typing import Optional, Any

import inflection

from .refs import SchemaOrRef, ResolverFunc
from ..module_path import ModulePath
from ..type_ref import TypeRef, get_type_ref
from ...openapi import model as openapi


@dataclass(frozen=True)
class AttributeAnnotationModel:
    type: TypeRef
    field_props: dict[str, Any]

    direction: Optional[str] = None
    style: Optional[str] = None
    explode: Optional[bool] = None
    allowReserved: Optional[bool] = False


def get_attr_annotation(
        typ: SchemaOrRef,
        name: str,
        parent_name: str,
        required: bool,
        module: ModulePath,
        resolve: ResolverFunc,
        in_: Optional[str] = None,
) -> AttributeAnnotationModel:
    """
    if typ is a schema, then it's a nested schema. Name should be parent_class_name+prop_name, and module is the same.
    Otherwise, it's a reference, schema, module and name should be resolved from it and used to generate type_ref
    """
    if isinstance(typ, openapi.Reference):
        schema, module, name = resolve(typ, openapi.Schema)
    else:
        schema: openapi.Schema = typ
        name = inflection.camelize(parent_name) + inflection.camelize(name)
    return _get_attr_annotation(schema, name, required, module, resolve, in_)


FIELD_PROPS = {
    'multipleOf': 'multiple_of',
    'maximum': 'le',
    'exclusiveMaximum': 'lt',
    'minimum': 'gt',
    'exclusiveMinimum': 'ge',
    'maxLength': 'max_length',
    'minLength': 'min_length',
    'maxItems': 'max_items',
    'minItems': 'min_items',
    'uniqueItems': 'unique_items',
    'maxProperties': 'max_properties',
    'minProperties': 'min_properties',
    'default': 'default',
}


def _get_attr_annotation(
        schema: openapi.Schema,
        name: str,
        required: bool,
        module: ModulePath,
        resolve: ResolverFunc,
        in_: Optional[str] = None,
) -> AttributeAnnotationModel:
    field_props = {FIELD_PROPS[k]: getattr(schema, k) for k in schema.__fields_set__ if k in FIELD_PROPS}
    for k, v in field_props.items():
        if isinstance(v, str):
            field_props[k] = f"'{v}'"

    if in_ is not None:
        field_props['in_'] = 'lapis_client_base.ParamPlacement.' + in_

    if 'pattern' in schema.__fields_set__:
        field_props['regex'] = f"r'${schema.pattern}'"

    if not required:
        field_props['default'] = 'lapis_client_base.absent.ABSENT'

    return AttributeAnnotationModel(
        type=get_type_ref(schema, module, name, required, resolve),
        direction=get_direction(schema.readOnly, schema.writeOnly),
        field_props=field_props
    )


def get_direction(read_only: Optional[bool], write_only: Optional[bool]) -> Optional[str]:
    if read_only:
        if write_only:
            raise ValueError()
        else:
            return 'lapis_client_base.ParamDirection.read'
    else:
        if write_only:
            return 'lapis_client_base.ParamDirection.write'
        else:
            return None
