from dataclasses import dataclass

from typing import Optional, Union

from .attribute import AttributeModel, get_attribute, get_enum_attribute
from .type_ref import TypeRef
from ..refs import ResolverFunc
from ...openapi import model as openapi


@dataclass(frozen=True)
class SchemaClass:
    class_name: str
    base_type: TypeRef
    attributes: list[AttributeModel]
    docstr: Optional[str]


def get_schema_class(
        schema: Union[openapi.Schema, openapi.Reference],
        path: list[str],
        resolver: ResolverFunc,
) -> SchemaClass:
    if isinstance(schema, openapi.Reference):
        schema, path = resolver(schema)

    if schema.enum:
        attributes = [get_enum_attribute(value) for value in schema.enum]
        base_type = TypeRef.from_str('enum.Enum')
    else:
        attributes = [get_attribute(attr, schema.required and attr_name in schema.required, [*path, attr_name], resolver) for attr_name, attr in
                      schema.properties.items()] if schema.properties else []
        base_type = TypeRef.from_str('pydantic.BaseModel')

    return SchemaClass(
        class_name=path[-1],
        base_type=base_type,
        attributes=attributes,
        docstr=schema.description or None,
    )
