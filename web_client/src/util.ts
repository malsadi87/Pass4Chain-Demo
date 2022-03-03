export function arrayToHex(array: Uint8Array): string {
    return Array.from(array)
      .map(c => c.toString(16).padStart(2, "0"))
      .join("");
}

export function randomPrivateKey() {
    const array = window.crypto.getRandomValues(new Uint8Array(32));
    return array;
}