import { describe, expect, it } from "vitest";

import * as vacationService from "./vacation";

describe("vacation API service", () => {
  it("builds a Gmail compose link for sharing the briefing manually", () => {
    expect("getGmailComposeUrl" in vacationService).toBe(true);
    const getGmailComposeUrl = (
      vacationService as unknown as { getGmailComposeUrl: () => string }
    ).getGmailComposeUrl;

    expect(getGmailComposeUrl()).toBe("https://mail.google.com/mail/u/0/?view=cm&fs=1&tf=1");
  });

  it("accepts a departure date in the future when it is before the return date", () => {
    expect(vacationService.validateVacationWindow("2030-01-10T10:00", "2030-01-12T10:00")).toBeNull();
  });
});
