from enum import IntEnum
from typing import List, Optional

from pydantic import BaseModel

# Models are based on protobufs in project_root/protos/


class Reporter(BaseModel):
    public_key: str
    authorized: bool
    index: int


class AssociatedAgent(BaseModel):
    agent_id: str
    timestamp: int


class Agent(BaseModel):
    public_key: str
    name: str
    timestamp: int


class PropertySchema(BaseModel):
    name: str
    data_type: str
    required: bool = False
    fixed: bool = False
    delayed: bool = False
    number_exponent: Optional[int]
    enum_options: Optional[List[str]]
    struct_properties: Optional[List['PropertySchema']]
    unit: Optional[str]


PropertySchema.update_forward_refs()


class Record(BaseModel):
    record_id: str
    record_type: str
    owners: List[AssociatedAgent]
    custodians: List[AssociatedAgent]
    final: bool = False


Record.update_forward_refs()


class RecordType(BaseModel):
    name: str
    properties: List[PropertySchema]


RecordType.update_forward_refs()


class Property(BaseModel):
    name: str
    record_id: str
    data_type: str
    reporters: List[Reporter]
    current_page: int = 1
    wrapped: bool = False
    fixed: Optional[bool]
    number_exponent: Optional[int]
    enum_options: Optional[List[str]]
    struct_properties: Optional[List[PropertySchema]]
    unit: Optional[str]


Property.update_forward_refs()


class Location(BaseModel):
    latitude: int
    longitude: int


class PropertyValue(BaseModel):
    name: str
    data_type: str
    # bytes_value: Optional[bytes]
    boolean_value: Optional[bool]
    number_value: Optional[int]
    string_value: Optional[str]
    enum_value: Optional[str]
    struct_values: Optional[List['PropertyValue']]
    location_value: Optional[Location]


PropertyValue.update_forward_refs()


class ReportedValue(BaseModel):
    reporter_index: int
    timestamp: int
    # bytes_value: Optional[bytes]
    boolean_value: Optional[bool]
    number_value: Optional[int]
    string_value: Optional[str]
    enum_value: Optional[int]
    struct_values: Optional[List[PropertyValue]]
    location_value: Optional[Location]


ReportedValue.update_forward_refs()


class PropertyPage(BaseModel):
    name: str
    record_id: str
    reported_values: Optional[List[ReportedValue]]


PropertyPage.update_forward_refs()


class NotFound(BaseModel):
    detail: str


VALUES_LOOKUP = {
    "NUMBER": "number_value",
    "STRING": "string_value",
    "BOOLEAN": "boolean_value",
    "ENUM": "enum_value",
    "STRUCT": "struct_values",
    "LOCATION": "location_value"
}
