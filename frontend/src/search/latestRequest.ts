export class LatestRequest {
  #controller: AbortController | null = null;

  begin(): AbortSignal {
    this.#controller?.abort();
    this.#controller = new AbortController();
    return this.#controller.signal;
  }

  isCurrent(signal: AbortSignal): boolean {
    return this.#controller?.signal === signal && !signal.aborted;
  }

  cancel(): void {
    this.#controller?.abort();
    this.#controller = null;
  }
}
