import { TableName } from "./types";

type Subscriptions = {[key in TableName]: Function[]};

export class WsListener {

    private socket: WebSocket;
    private subscriptions: Subscriptions = { agents: [], blocks: [], recordTypes: []};

    constructor(
        url: string
    ) {
        this.socket = this.initWebSocket(`ws://${url}/ws/feed`);
    }

    private initWebSocket(url: string): WebSocket {
        const socket = new WebSocket(url);
        socket.onopen = (_) => this.onOpen();
        socket.onmessage = (ev) => this.onMessage(ev);
        socket.onerror = (ev) => this.onError(ev);
        return socket;
    }

    private onOpen() {
        console.log("WebSocket connection opened.");
    }

    private onMessage(ev: MessageEvent) {
        const msg = JSON.parse(ev.data);
        this.subscriptions[msg.updated_table as TableName].forEach(cb => cb(msg));
    }

    private onError(ev: Event) {
        console.error("WebSocket connection error:", ev.type);
    }

    public subscribe(table: TableName, cb: Function) {
        this.subscriptions[table as TableName].push(cb);
    }
}