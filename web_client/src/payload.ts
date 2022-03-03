import { Message } from "protobufjs";
import { SCPayload, ActionEnum, CreateAgentAction, Transaction, TransactionHeader } from "./protos/proto";
import { ISigner } from "./types";
import { createHash } from "crypto";
import { API } from "./api";


// TODO: Sync with "addressing/supply_chain_adressers/addressing.py" somehow
const FAMILY_NAME = "paasforchain_adresser";
const FAMILY_VERSION = "0.01";

type Action = "CREATE_AGENT";
type EncodedMessage = Uint8Array;

const action_lookup: { [key in Action]: protobuf.Type } = {
    "CREATE_AGENT": CreateAgentAction
}

export class TransactionHandler {

    constructor(private api: API) { }

    createPayload(action: Action, actionData: any): EncodedMessage {
        const actionMessage = action_lookup[action];
        return SCPayload.encode({
            action: ActionEnum[action],
            timestamp: Math.floor(Date.now() / 1000),
            [actionMessage.name]: actionMessage.create(...actionData)  // Should add validation of actionData before this
        }).finish();
    }

    createTransaction(payload: EncodedMessage, signer: ISigner) {
        const address = "TODO";
        const transactionHeader = this.createTransactionHeader(payload, address, signer.pubKey);
        return Transaction.create({

        })
    }

    createTransactionHeader(payload: EncodedMessage, address: string, pubKey: string): EncodedMessage {
        return TransactionHeader.encode({
            family_name: FAMILY_NAME,
            family_version: FAMILY_VERSION,
            inputs: [address],
            outputs: [address],
            signer_public_key: pubKey,
            batcher_public_key: this.api.getPubKey(),
            dependencies: [],
            payload_sha512: createHash('sha512').update(payload).digest('hex'),
            nonce: (Math.random() * 10 ** 18).toString(36)
        }).finish();
    }

}