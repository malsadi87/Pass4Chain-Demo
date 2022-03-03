import { getPublicKey } from "@noble/secp256k1";
import { ActionEnum, SCPayload } from "./protos/proto";

export class Agent {

    private publicKey: Uint8Array;

    constructor(
        private name: string,
        private privateKey: Uint8Array
    ) {
        this.publicKey =  getPublicKey(privateKey);
    }

}