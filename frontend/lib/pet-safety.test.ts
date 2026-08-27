import { describe, expect, it } from "vitest";

import { buildPetSafetyMessage } from "./pet-safety";


const toxicPlant = {
  pet_safety: "toxic" as const,
  toxic_cats: true,
  toxic_dogs: true,
  placement_tip: "Keep on a high shelf.",
};

describe("buildPetSafetyMessage", () => {
  it("addresses the pets selected in the profile", () => {
    expect(buildPetSafetyMessage(toxicPlant, ["Cats", "Dogs"])).toBe(
      "Toxic for your cat and dog. Keep on a high shelf.",
    );
  });

  it("does not invent bird toxicity information", () => {
    expect(buildPetSafetyMessage(toxicPlant, ["Birds"])).toBe(
      "Safety for your bird is not covered by the current cat and dog dataset. Keep on a high shelf.",
    );
  });

  it("describes safe plants for the selected pet", () => {
    expect(
      buildPetSafetyMessage(
        {
          pet_safety: "safe",
          toxic_cats: false,
          toxic_dogs: false,
          placement_tip: "Normal pet-aware placement.",
        },
        ["Cats"],
      ),
    ).toBe("Listed as pet-safe for your cat. Normal pet-aware placement.");
  });
});
