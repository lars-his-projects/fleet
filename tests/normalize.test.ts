import { describe, expect, it } from "vitest";
import { normalizeStreetName } from "../src/normalize";

describe("normalizeStreetName", () => {
  it("makes lower case, removes accents and trims", () => {
    expect(normalizeStreetName("  Rue de l'Élysée ")).toBe("rue de l'elysee");
  });

  it("joins repeated spaces", () => {
    expect(normalizeStreetName("Van  Baerlestraat")).toBe("van baerlestraat");
  });
});
