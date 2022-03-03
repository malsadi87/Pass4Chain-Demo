from protobuf.property_pb2 import PropertySchema, PropertyValue, Location
from supply_chain_client.models.record import RecordItem
from supply_chain_client.models.record_type import RecordTypeItem


_temperature = PropertySchema(
        name="_temperature",
        data_type=PropertySchema.DataType.NUMBER,
        unit="Celsius")

_location = PropertySchema(
    name="_location",
    data_type=PropertySchema.DataType.LOCATION)

temperature_schema = PropertySchema(
    name="Temperature",
    data_type=PropertySchema.DataType.STRUCT,
    struct_properties=[_temperature, _location])

trip_schema = PropertySchema(
    name="Trip",
    data_type=PropertySchema.DataType.NUMBER,
    fixed=True,
    required=True)

specie_schema = PropertySchema(
    name="Specie",
    data_type=PropertySchema.DataType.STRING,
    fixed=True,
    required=True)

fish_pallet_type = RecordTypeItem(
    name="FishPallet",
    properties=[trip_schema, specie_schema, temperature_schema])


def create_trip(trip_id: int):
    return PropertyValue(
        name="Trip",
        data_type=PropertySchema.DataType.NUMBER,
        number_value=trip_id)


def create_specie(specie_name: str):
    return PropertyValue(
        name="Specie",
        data_type=PropertySchema.DataType.STRING,
        string_value=specie_name)


def create_temperature(temperature, location):
    temp = PropertyValue(
        name="temperature",
        data_type=PropertySchema.DataType.NUMBER,
        number_value=temperature)

    location = PropertyValue(
        name="location",
        data_type=PropertySchema.DataType.LOCATION,
        location_value=Location(latitude=location[0], longitude=location[1]))

    return PropertyValue(
        name="Temperature",
        data_type=PropertySchema.DataType.STRUCT,
        struct_values=[temp, location])


def create_fish_pallet(record_id: str, trip_id: int, specie_name: str):
    trip = create_trip(trip_id)
    specie = create_specie(specie_name)
    return RecordItem(
        record_id=record_id,
        record_type=fish_pallet_type,
        properties=[trip, specie])
