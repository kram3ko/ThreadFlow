import { describe, expect, it } from "vitest";

import { LatestRequest } from "../src/search/latestRequest";

describe("LatestRequest", () => {
  it("aborts the previous request and accepts only the latest response", () => {
    const requests = new LatestRequest();
    const first = requests.begin();
    const second = requests.begin();

    expect(first.aborted).toBe(true);
    expect(requests.isCurrent(first)).toBe(false);
    expect(requests.isCurrent(second)).toBe(true);
  });

  it("invalidates the active request when cancelled", () => {
    const requests = new LatestRequest();
    const signal = requests.begin();

    requests.cancel();

    expect(signal.aborted).toBe(true);
    expect(requests.isCurrent(signal)).toBe(false);
  });
});
