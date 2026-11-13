/** Normalize a street name for a comparison: lower case, no accents, no extra spaces. */
export function normalizeStreetName(name: string): string {
  return name.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().replace(/\s+/g, " ").trim();
}
