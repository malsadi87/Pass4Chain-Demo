import protobuf from "protobufjs";
import * as appProtoJson from "./generated_protos.json" ;
import * as sdkProtoJson from "./sdk_protos.json" ;

// Compile Application Protobufs
const app_root = protobuf.Root.fromJSON(appProtoJson);
export const SCPayload = app_root.lookupType('SupplyChainPayload');

export const CreateAgentAction = app_root.lookupType('CreateAgentAction');

export const PropertyValue = app_root.lookupType('PropertyValue');
export const PropertySchema = app_root.lookup('PropertySchema');
export const Location = app_root.lookup('Location');
export const Proposal = app_root.lookup('Proposal');
export const ActionEnum = app_root.lookupEnum('SupplyChainPayload.Action').values;

// Compile SDK Protobufs
const sdk_root = protobuf.Root.fromJSON(sdkProtoJson);
export const Transaction = sdk_root.lookupType('Transaction');
export const TransactionHeader = sdk_root.lookupType('TransactionHeader');