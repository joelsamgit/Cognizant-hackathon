import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("AccountAvatar", () => {
  it("renders the enlarged floating trigger away from the screen edges", () => {
    const source = readFileSync(new URL("./account-avatar.tsx", import.meta.url), "utf8");

    expect(source).toContain("bottom-10 right-10");
    expect(source).toContain("size-[5.25rem]");
    expect(source).toContain("size={66}");
  });
});
