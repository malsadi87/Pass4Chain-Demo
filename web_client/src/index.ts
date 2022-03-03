import { Agent } from "./agent";
import { arrayToHex, randomPrivateKey } from "./util";
import { WsListener } from "./WsListener";


const listener = new WsListener("localhost:9090");

const blocksTable = document.getElementById("blocks-table").querySelector("tbody");
const agentsTable = document.getElementById("agents-table").querySelector("tbody");
const recordTypesTable = document.getElementById("record-types-table").querySelector("tbody");

listener.subscribe("agents", (msg: any) => {
    const elem = agentsTable.insertRow(0);
    elem.innerHTML = `<td>${msg.new_val.name}</td><td>${msg.new_val.public_key}</td>`;
});

listener.subscribe("blocks", (msg: any) => {
    const elem = blocksTable.insertRow(0);
    elem.innerHTML = `<td>${msg.new_val.block_num}</td><td>${msg.new_val.block_id}</td>`;
});

listener.subscribe("recordTypes", (msg: any) => {
    const elem = recordTypesTable.insertRow(0);
    console.log(msg.new_val.properties);
    elem.innerHTML = `<td>${msg.new_val.name}</td><td>${msg.new_val.properties.dataType}</td><td>${msg.new_val.properties.unit}</td>`;
});



// Add agent modal  # todo: use some frontend framwork for this stuff (react or mithril probably)

type ModalState = {
    name: string,
    privateKey: Uint8Array,
    privateKeyString: string
}

const state: Partial<ModalState> = {};

const addAgentBtn = document.getElementById("addAgentBtn");
const agentNameInput = document.getElementById("agentNameInput") as HTMLInputElement;
const privKeyInput = document.getElementById("privatekey-input") as HTMLInputElement;
const randomizePrivKeyBtn = document.getElementById("random-privatekey-btn");
const agentSubmitBtn = document.getElementById("addAgentSubmitBtn");

addAgentBtn.addEventListener("click", () => {
    state.name = "";
    state.privateKeyString = "";

    agentNameInput.value = state.name;
    privKeyInput.value = state.privateKeyString;
});

randomizePrivKeyBtn.addEventListener("click", () => {
    const randomKey = randomPrivateKey();
    privKeyInput.value = arrayToHex(randomKey);
    state.privateKey = randomKey;
});

agentSubmitBtn.addEventListener("click", () => {
    const agent = new Agent(state.name, state.privateKey);
});