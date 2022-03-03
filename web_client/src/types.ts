export type TableName = "agents" | "blocks" | "recordTypes";

export interface ISigner {
    sign(): any
    pubKey: string
}