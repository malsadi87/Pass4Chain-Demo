import datetime
import logging
import time

from sawtooth_sdk.processor.exceptions import InvalidTransaction, InternalError
from sawtooth_sdk.processor.handler import TransactionHandler

from protobuf.supply_chain_protos.payload_pb2 import *
from protobuf.supply_chain_protos.agent_pb2 import *
from protobuf.supply_chain_protos.property_pb2 import *
from protobuf.supply_chain_protos.proposal_pb2 import *
from protobuf.supply_chain_protos.record_pb2 import *

from addressing.supply_chain_addressers import addresser

SYNC_TOLERANCE = 60 * 5
MAX_LAT = 90 * 1e6
MIN_LAT = -90 * 1e6
MAX_LNG = 180 * 1e6
MIN_LNG = -180 * 1e6

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)

PROPERTY_PAGE_MAX_LENGTH = 256
TOTAL_PROPERTY_PAGE_MAX = 16 ** 4 - 1


class SupplyChainTransactionHandler(TransactionHandler):

    @property
    def family_name(self):
        return addresser.FAMILY_NAME

    @property
    def family_versions(self):
        return [addresser.FAMILY_VERSION]

    @property
    def namespaces(self):
        return [addresser.NAMESPACE]

    def apply(self, transaction, context):
        """
        A SupplyChain payload consists of a timestamp, an action tag, and
        attributes corresponding to various actions (create|_agent,
        create_record, etc). The appropriate attribute will be
        selected depending on the action tag, and that information
        plus the timestamp and the public key with which the
        transaction was signed will be passed on to the appropriate
        handler function (_create_agent, _create_record, etc).
        _unpack_transaction gets the signing key, the timestamp, and
        the action tag out of the transaction, then returns the
        signing key, the timestamp, and the appropriate SupplyChain payload
        attribute and handler function.

        Besides this, the transaction's timestamp is verified, since
        that validation is common to all transactions.
        """
        LOGGER.info("apply() method ")
        LOGGER.info(transaction)
        signer, timestamp, payload, handler = _unpack_transaction(transaction)
        handler(payload, signer, timestamp, context)


def _unpack_transaction(transaction):
    """Return the transaction signing key, the SupplyChainPayload timestamp, the
    appropriate SupplyChainPayload action attribute, and the appropriate
    handler function (with the latter two determined by the constant
    TYPE_TO_ACTION_HANDLER table.
    """
    signer = transaction.header.signer_public_key

    LOGGER.info("_unpack_transaction() ")

    payload = SupplyChainPayload()
    payload.ParseFromString(transaction.payload)

    action = payload.action
    timestamp = payload.timestamp

    try:
        attribute, handler = TYPE_TO_ACTION_HANDLER[action]
    except KeyError:
        raise InvalidTransaction('Specified action is invalid')

    payload = getattr(payload, attribute)

    return signer, timestamp, payload, handler


# hANDLERS
def _create_agent(payload, signer, timestamp, state):
    name = payload.name

    if not name:
        raise InvalidTransaction(
            'Agent name cannot be empty string')

    address = addresser.get_agent_address(signer)
    container = _get_container(state, address)

    for agent in container.entries:
        if agent.public_key == signer:
            raise InvalidTransaction('Agent with the public key {} already exists'.format(agent.public_key))

    agent = Agent(
        public_key=signer,
        name=name,
        timestamp=timestamp,
    )

    container.entries.extend([agent])
    container.entries.sort(key=lambda ag: ag.public_key)

    _set_container(state, address, container)


# def _create_agent(state, public_key, payload):
#     name = payload.name
#     if not name:
#         raise InvalidTransaction(
#             'Agent name cannot be empty string')
#
#     if state.get_agent(public_key):
#         raise InvalidTransaction('Agent with the public key {} already '
#                                  'exists'.format(public_key))
#     state.set_agent(
#         public_key=public_key,
#         name=payload.data.name,
#         timestamp=payload.timestamp)


def _create_record(payload, signer, timestamp, state):
    """
    * Check that the signer is registered.
    * Check that the record doesn't already exist.
    * Check that the record type exists.
    * Check that the required properties have been provided.
    * Create the record (and record container if needed).
    * Create the associated properties.
    * Post the provided property values.
    """

    # Check that the signer is registered.
    _verify_agent(state, signer)

    # Check that the record doesn't already exist
    record_id = payload.record_id

    if not record_id:
        raise InvalidTransaction(
            'Record id cannot be empty string')

    record_address = addresser.get_record_address(record_id)
    record_container = _get_container(state, record_address)

    if any(rec.record_id == record_id for rec in record_container.entries):
        raise InvalidTransaction(
            'Record {} already exists'.format(record_id))

    # Check that the record type exists.
    type_name = payload.record_type
    record_type, _, _ = _get_record_type(state, type_name)

    type_schemata = {
        prop.name: prop
        for prop in record_type.properties
    }

    required_properties = {
        name: prop
        for name, prop in type_schemata.items()
        if prop.required
    }

    provided_properties = {
        prop.name: prop
        for prop in payload.properties
    }

    # Make sure the required properties are all provided
    for name in required_properties:
        if name not in provided_properties:
            raise InvalidTransaction(
                'Required property {} not provided'.format(
                    name))

    # Make sure the provided properties have the right type
    for provided_name in provided_properties:
        required_type = type_schemata[provided_name].data_type
        provided_type = provided_properties[provided_name].data_type
        if required_type != provided_type:
            raise InvalidTransaction(
                'Value provided for {} is the wrong type'.format(
                    provided_name))

    # Create the record
    record = Record(
        record_id=record_id,
        record_type=type_name,
        final=False,
    )

    record.owners.extend([
        Record.AssociatedAgent(
            agent_id=signer,
            timestamp=timestamp,
        )
    ])

    record.custodians.extend([
        Record.AssociatedAgent(
            agent_id=signer,
            timestamp=timestamp,
        )
    ])

    record_container.entries.extend([record])
    record_container.entries.sort(key=lambda rec: rec.record_id)

    _set_container(state, record_address, record_container)

    # Create the associated properties
    for property_name, prop in type_schemata.items():
        _make_new_property(
            state=state,
            record_id=record_id,
            property_name=property_name,
            prop=prop,
            signer=signer
        )

        _make_new_property_page(
            state=state,
            timestamp=timestamp,
            record_id=record_id,
            property_name=property_name,
            value=(
                None if property_name not in provided_properties
                else provided_properties[property_name]
            ),
            page_number=1,
        )


# def _create_record(state, public_key, payload):
#    if state.get_agent(public_key) is None:
#        raise InvalidTransaction('Agent with the public key {} does '
#                                 'not exist'.format(public_key))
#
#    if payload.data.record_id == '':
#        raise InvalidTransaction('No record ID provided')#
#
#    if state.get_record(payload.data.record_id):
#        raise InvalidTransaction('Identifier {} belongs to an existing '
#                                 'record'.format(payload.data.record_id))
#
#    _validate_latlng(payload.data.latitude, payload.data.longitude)
#
#    state.set_record(
#        public_key=public_key,
#        latitude=payload.data.latitude,
#        longitude=payload.data.longitude,
#        record_id=payload.data.record_id,
#        timestamp=payload.timestamp)


def _get_record(state, record_id):
    """ Return record, record_container, record_address """
    record_address = addresser.get_record_address(record_id)
    record_container = _get_container(state, record_address)

    try:
        record = next(
            record
            for record in record_container.entries
            if record.record_id == record_id
        )
    except StopIteration:
        raise InvalidTransaction(
            'Record does not exist')

    return record, record_container, record_address


def _finalize_record(payload, signer, timestamp, state):
    """
    * Check that the signer is both the owner and custodian
    * Check that the record is not already final
    """
    record_id = payload.record_id
    record, container, address = _get_record(state, record_id)

    if not _is_owner(record, signer) or not _is_custodian(record, signer):
        raise InvalidTransaction(
            'Must be owner and custodian to finalize record')

    if record.final:
        raise InvalidTransaction(
            'Record is already final')

    record.final = True
    _set_container(state, address, container)


def _create_record_type(payload, signer, timestamp, state):
    _verify_agent(state, signer)

    name, properties = payload.name, payload.properties

    if not name:
        InvalidTransaction(
            'Record type name cannot be empty string')

    if not properties:
        raise InvalidTransaction(
            'Record type must have at least one property')

    for prop in properties:
        if not prop.name:
            raise InvalidTransaction(
                'Property name cannot be empty string')

    address = addresser.get_record_type_address(name)

    container = _get_container(state, address)

    for rec_type in container.entries:
        if name == rec_type.name:
            raise InvalidTransaction(
                'Record type `{}` already exists'.format(name))

    record_type = RecordType(
        name=name,
        properties=properties,
    )

    container.entries.extend([record_type])
    container.entries.sort(key=lambda rec_type: rec_type.name)

    _set_container(state, address, container)


def _transfer_record(state, public_key, payload):
    if state.get_agent(payload.data.receiving_agent) is None:
        raise InvalidTransaction(
            'Agent with the public key {} does '
            'not exist'.format(payload.data.receiving_agent))

    record = state.get_record(payload.data.record_id)
    if record is None:
        raise InvalidTransaction('Record with the record id {} does not '
                                 'exist'.format(payload.data.record_id))

    if not _validate_record_owner(signer_public_key=public_key,
                                  record=record):
        raise InvalidTransaction(
            'Transaction signer is not the owner of the record')

    state.transfer_record(
        receiving_agent=payload.data.receiving_agent,
        record_id=payload.data.record_id,
        timestamp=payload.timestamp)


def _update_properties(payload, signer, timestamp, state):
    """
    * Check that the record is not final
    * Check that the signer is an authorized reporter
    * Check that the types are correct
    """
    # Check that the record is not final
    record_id = payload.record_id
    record, _, _ = _get_record(state, record_id)

    if record.final:
        raise InvalidTransaction(
            'Record is final')

    updates = payload.properties

    for update in updates:
        name, data_type = update.name, update.data_type
        property_address = addresser.get_property_address(record_id, name)
        property_container = _get_container(state, property_address)

        try:
            prop = next(
                prop
                for prop in property_container.entries
                if prop.name == name
            )
        except StopIteration:
            raise InvalidTransaction(
                'Record does not have property')

        try:
            reporter_index = next(
                reporter.index
                for reporter in prop.reporters
                if reporter.public_key == signer and reporter.authorized
            )
        except StopIteration:
            raise InvalidTransaction(
                'Reporter is not authorized')

        if data_type != prop.data_type:
            raise InvalidTransaction(
                'Update has wrong type')

        page_number = prop.current_page
        page_address = addresser.get_property_address(
            record_id, name, page_number)
        page_container = _get_container(state, page_address)

        try:
            page = next(
                page
                for page in page_container.entries
                if page.name == name
            )
        except StopIteration:
            raise InternalError(
                'Property page does not exist')

        reported_value = _make_new_reported_value(
            reporter_index=reporter_index,
            timestamp=timestamp,
            prop=update,
        )

        page.reported_values.extend([reported_value])
        page.reported_values.sort(
            key=lambda val: (val.timestamp, val.reporter_index))

        _set_container(state, page_address, page_container)

        # increment page if needed

        if len(page.reported_values) >= PROPERTY_PAGE_MAX_LENGTH:
            new_page_number = (
                page_number + 1
                if page_number + 1 <= TOTAL_PROPERTY_PAGE_MAX
                else 1
            )

            new_page_address = addresser.get_property_address(
                record_id, name, new_page_number)

            new_page_container = _get_container(state, new_page_address)

            try:
                new_page = next(
                    page
                    for page in new_page_container.entries
                    if page.name == name
                )

                del new_page.reported_values[:]

            except StopIteration:
                new_page = PropertyPage(
                    name=name,
                    record_id=record_id,
                )

                new_page_container.entries.extend([new_page])

            _set_container(state, new_page_address, new_page_container)

            # increment the property's page number (or wrap back to 1)

            prop.current_page = new_page_number

            if new_page_number == 1 and not prop.wrapped:
                prop.wrapped = True

            _set_container(state, property_address, property_container)


# TODO: MOVE ME TO STATE AND REWORK ME
def _get_property(state, record_id, property_name):
    """ Return property, property_container, property_address """
    property_address = addresser.get_property_address(
        record_id, property_name)

    property_container = _get_container(state, property_address)

    try:
        prop = next(
            prop
            for prop in property_container.entries
            if prop.name == property_name
        )
    except StopIteration:
        raise InvalidTransaction(
            'Property does not exist')

    return prop, property_container, property_address


def _create_proposal(payload, signer, timestamp, state):
    record_id, receiving_agent, role, properties = payload.record_id, payload.receiving_agent, payload.role, payload.properties

    # Verify both agents
    _verify_agent(state, signer)
    _verify_agent(state, receiving_agent)

    proposal_address = addresser.make_proposal_address(
        record_id, receiving_agent)
    proposal_container = _get_container(state, proposal_address)

    open_proposals = [
        proposal
        for proposal in proposal_container.entries
        if proposal.status == Proposal.OPEN
    ]

    for proposal in open_proposals:
        if (proposal.receiving_agent == receiving_agent
                and proposal.role == role
                and proposal.record_id == record_id):
            raise InvalidTransaction(
                'Proposal already exists')

    record, _, _ = _get_record(state, record_id)

    if record.final:
        raise InvalidTransaction(
            'Record is final')

    if role == Proposal.OWNER or role == Proposal.REPORTER:
        if not _is_owner(record, signer):
            raise InvalidTransaction(
                'Must be owner')

    if role == Proposal.CUSTODIAN:
        if not _is_custodian(record, signer):
            raise InvalidTransaction(
                'Must be custodian')

    proposal = Proposal(
        record_id=record_id,
        timestamp=timestamp,
        issuing_agent=signer,
        receiving_agent=receiving_agent,
        role=role,
        properties=properties,
        status=Proposal.OPEN,
    )

    proposal_container.entries.extend([proposal])
    proposal_container.entries.sort(
        key=lambda prop: (
            prop.record_id,
            prop.receiving_agent,
            prop.timestamp,
        )
    )

    _set_container(state, proposal_address, proposal_container)


def _accept_proposal(state, signer, proposal, timestamp):
    record_id, issuing_agent, receiving_agent, role, properties = \
        proposal.record_id, proposal.issuing_agent, \
        proposal.receiving_agent, proposal.role, proposal.properties

    record, record_container, record_address = _get_record(state, record_id)

    if role == Proposal.OWNER:
        if not _is_owner(record, issuing_agent):
            LOGGER.info('Issuing agent is not owner')
            return Proposal.CANCELED

        record.owners.extend([
            Record.AssociatedAgent(
                agent_id=receiving_agent,
                timestamp=timestamp)
        ])

        record.owners.sort(key=lambda agent: agent.timestamp)

        _set_container(state, record_address, record_container)

        # Authorize the new owner as a reporter on all of the record's
        # properties and deauthorize the old owner, leaving everything
        # else as-is
        record_type, _, _ = _get_record_type(state, record.record_type)

        for prop_name in (prop.name for prop in record_type.properties):
            prop, prop_container, prop_address = _get_property(
                state, record_id, prop_name)

            old_owner = next(
                reporter
                for reporter in prop.reporters
                if reporter.public_key == issuing_agent
            )

            old_owner.authorized = False

            try:
                new_owner = next(
                    reporter
                    for reporter in prop.reporters
                    if reporter.public_key == receiving_agent
                )

                if not new_owner.authorized:
                    new_owner.authorized = True
                    _set_container(state, prop_address, prop_container)

            except StopIteration:
                new_owner = Property.Reporter(
                    public_key=receiving_agent,
                    authorized=True,
                    index=len(prop.reporters),
                )

                prop.reporters.extend([new_owner])

                _set_container(state, prop_address, prop_container)

        return Proposal.ACCEPTED


def _make_new_property(state, record_id, property_name, prop, signer):
    property_address = addresser.get_property_address(
        record_id, property_name, 0)

    property_container = _get_container(state, property_address)

    new_prop = Property(
        name=property_name,
        record_id=record_id,
        data_type=prop.data_type,
        reporters=[Property.Reporter(
            public_key=signer,
            authorized=True,
            index=0,
        )],
        current_page=1,
        wrapped=False,
        fixed=prop.fixed,
        unit=prop.unit
    )

    if prop.data_type == PropertySchema.DataType.STRUCT:
        # Getting protobuf MergeFrom error when not recreating the PropertSchemas (this fix is a bit hacky)
        # Also, nested structs are not fully supported yet.
        props = [
            PropertySchema(
                name=p.name,
                data_type=p.data_type,
                required=p.required,
                fixed=p.fixed,
                delayed=p.delayed,
                number_exponent=p.number_exponent,
                enum_options=p.enum_options,
                struct_properties=p.struct_properties,
                unit=p.unit
            ) for p in prop.struct_properties]
        new_prop.struct_properties.extend(props)

    property_container.entries.extend([new_prop])
    property_container.entries.sort(key=lambda p: p.name)

    _set_container(state, property_address, property_container)


def _make_new_property_page(
        state, timestamp, record_id,
        property_name, value, page_number):
    page_address = addresser.get_property_address(
        record_id, property_name, page_number)

    page_container = _get_container(state, page_address)

    page = PropertyPage(
        name=property_name,
        record_id=record_id,
    )

    if value:
        page.reported_values.extend([
            _make_new_reported_value(
                reporter_index=0,
                timestamp=timestamp,
                prop=value,
            )
        ])

    page_container.entries.extend([page])
    page_container.entries.sort(key=lambda page: page.name)

    _set_container(state, page_address, page_container)


def _make_new_reported_value(reporter_index, timestamp, prop):
    reported_value = PropertyPage.ReportedValue(
        reporter_index=reporter_index,
        timestamp=timestamp,
    )

    _set_attribute(prop, reported_value)

    return reported_value


def _set_attribute(src, dst):
    attribute = DATA_TYPE_TO_ATTRIBUTE[src.data_type]
    if attribute == 'location_value':
        dst.location_value.latitude = src.location_value.latitude
        dst.location_value.longitude = src.location_value.longitude
    elif attribute == 'struct_values':
        _set_struct_attribute(dst, src.struct_values)
    else:
        setattr(dst, attribute, getattr(src, attribute))


def _set_struct_attribute(dst, struct_values):
    vals = []
    for s in struct_values:
        pv = PropertyValue(name=s.name, data_type=s.data_type)
        _set_attribute(s, pv)
        vals.append(pv)
    dst.struct_values.extend(vals)


def _answer_proposal(payload, signer, timestamp, state):
    record_id, receiving_agent, role, response = payload.record_id, payload.receiving_agent, payload.role, payload.response

    proposal_address = addresser.make_proposal_address(
        record_id, receiving_agent)
    proposal_container = _get_container(state, proposal_address)

    try:
        proposal = next(
            proposal
            for proposal in proposal_container.entries
            if (proposal.status == Proposal.OPEN
                and proposal.receiving_agent == receiving_agent
                and proposal.role == role)
        )
    except StopIteration:
        raise InvalidTransaction(
            'No such open proposal')

    if response == AnswerProposalAction.CANCEL:
        if proposal.issuing_agent != signer:
            raise InvalidTransaction(
                'Only the issuing agent can cancel')

        proposal.status = Proposal.CANCELED

    elif response == AnswerProposalAction.REJECT:
        if proposal.receiving_agent != signer:
            raise InvalidTransaction(
                'Only the receiving agent can reject')

        proposal.status = Proposal.REJECTED

    elif response == AnswerProposalAction.ACCEPT:
        if proposal.receiving_agent != signer:
            raise InvalidTransaction(
                'Only the receiving agent can accept')

        proposal.status = _accept_proposal(state, signer, proposal, timestamp)

    _set_container(state, proposal_address, proposal_container)


def _revoke_reporter(payload, signer, timestamp, state):
    """
    * Check that the signer is the owner
    * Check that the reporter is actually a reporter
    * Does it matter if the record is finalized?
    """
    record_id, reporter_id, properties = \
        payload.record_id, payload.reporter_id, payload.properties

    record, _, _ = _get_record(state, record_id)

    if not _is_owner(record, signer):
        raise InvalidTransaction(
            'Must be owner to revoke reporters')

    if record.final:
        raise InvalidTransaction(
            'Record is final')

    for property_name in properties:
        prop, property_container, property_address = \
            _get_property(state, record_id, property_name)

        try:
            reporter = next(
                reporter
                for reporter in prop.reporters
                if reporter.public_key == reporter_id
            )

            if not reporter.authorized:
                raise InvalidTransaction(
                    'Reporter has already been revoked')

        except StopIteration:
            raise InvalidTransaction(
                'Reporter cannot be revoked')

        reporter.authorized = False

        _set_container(state, property_address, property_container)


def _update_record(state, public_key, payload):
    record = state.get_record(payload.data.record_id)
    if record is None:
        raise InvalidTransaction('Record with the record id {} does not '
                                 'exist'.format(payload.data.record_id))

    if not _validate_record_owner(signer_public_key=public_key,
                                  record=record):
        raise InvalidTransaction(
            'Transaction signer is not the owner of the record')

    _validate_latlng(payload.data.latitude, payload.data.longitude)

    state.update_record(
        latitude=payload.data.latitude,
        longitude=payload.data.longitude,
        record_id=payload.data.record_id,
        timestamp=payload.timestamp)


def _validate_record_owner(signer_public_key, record):
    """Validates that the public key of the signer is the latest (i.e.
    current) owner of the record
    """
    latest_owner = max(record.owners, key=lambda obj: obj.timestamp).agent_id
    return latest_owner == signer_public_key


def _validate_latlng(latitude, longitude):
    if not MIN_LAT <= latitude <= MAX_LAT:
        raise InvalidTransaction('Latitude must be between -90 and 90. '
                                 'Got {}'.format(latitude / 1e6))
    if not MIN_LNG <= longitude <= MAX_LNG:
        raise InvalidTransaction('Longitude must be between -180 and 180. '
                                 'Got {}'.format(longitude / 1e6))


def _validate_timestamp(timestamp):
    """Validates that the client submitted timestamp for a transaction is not
    greater than current time, within a tolerance defined by SYNC_TOLERANCE

    NOTE: Timestamp validation can be challenging since the machines that are
    submitting and validating transactions may have different system times
    """
    dts = datetime.datetime.utcnow()
    current_time = round(time.mktime(dts.timetuple()) + dts.microsecond / 1e6)
    if (timestamp - current_time) > SYNC_TOLERANCE:
        raise InvalidTransaction(
            'Timestamp must be less than local time.'
            ' Expected {0} in ({1}-{2}, {1}+{2})'.format(
                timestamp, current_time, SYNC_TOLERANCE))


"""message PropertySchema {
  enum DataType {
    TYPE_UNSET = 0;
    BYTES = 1;
    BOOLEAN = 2;
    NUMBER = 3;
    STRING = 4;
    ENUM = 5;
    STRUCT = 6;
    LOCATION = 7;
  }
"""
DATA_TYPE_TO_ATTRIBUTE = {
    PropertySchema.BYTES: 'bytes_value',
    PropertySchema.STRING: 'string_value',
    # PropertySchema.NUMBER: 'float_value',
    PropertySchema.NUMBER: 'number_value',
    PropertySchema.LOCATION: 'location_value',
    PropertySchema.ENUM: 'enum_value',
    PropertySchema.STRUCT: 'struct_values'
}

TYPE_TO_ACTION_HANDLER = {
    SupplyChainPayload.CREATE_AGENT: ('create_agent', _create_agent),
    SupplyChainPayload.CREATE_RECORD: ('create_record', _create_record),
    SupplyChainPayload.FINALIZE_RECORD: ('finalize_record', _finalize_record),
    SupplyChainPayload.CREATE_RECORD_TYPE: ('create_record_type', _create_record_type),
    SupplyChainPayload.UPDATE_PROPERTIES: ('update_properties', _update_properties),
    SupplyChainPayload.CREATE_PROPOSAL: ('create_proposal', _create_proposal),
    SupplyChainPayload.ANSWER_PROPOSAL: ('answer_proposal', _answer_proposal),
    SupplyChainPayload.REVOKE_REPORTER: ('revoke_reporter', _revoke_reporter),
}


# Helper methods
def _set_container(state, address, container):
    addresses = state.set_state({
        address: container.SerializeToString()
    })

    if not addresses:
        raise InternalError(
            'State error -- failed to set state entries')


def _get_container(state, address):
    # Get the appropriate container type based on the address
    namespace = address[6:8]

    containers = {
        addresser.AGENT_PREFIX: AgentContainer,
        addresser.PROPERTY_PREFIX: (PropertyContainer
                                    if address[-4:] == '0000'
                                    else PropertyPageContainer),
        addresser.PROPOSAL_PREFIX: ProposalContainer,
        addresser.RECORD_PREFIX: RecordContainer,
        addresser.RECORD_TYPE_PREFIX: RecordTypeContainer,
    }

    container = containers[namespace]()

    # Get data from state
    entries = state.get_state([address])

    if entries:
        data = entries[0].data
        container.ParseFromString(data)

    return container


def _verify_agent(state, public_key):
    """ Verify that public_key has been registered as an agent """
    address = addresser.get_agent_address(public_key)
    container = _get_container(state, address)

    if all(agent.public_key != public_key for agent in container.entries):
        raise InvalidTransaction(
            'Agent must be registered to perform this action')


def _get_record_type(state, type_name):
    type_address = addresser.get_record_type_address(type_name)
    type_container = _get_container(state, type_address)

    try:
        record_type = next(
            rec_type
            for rec_type in type_container.entries
            if rec_type.name == type_name
        )
    except StopIteration:
        raise InvalidTransaction(
            'No record type {} exists'.format(type_name))

    return record_type, type_container, type_address


def _is_owner(record, agent_id):
    return record.owners[-1].agent_id == agent_id


def _is_custodian(record, agent_id):
    return record.custodians[-1].agent_id == agent_id
