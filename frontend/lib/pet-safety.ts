import type { Plant } from "@/types/plant";
import type { PetType } from "@/types/user";


type PetSafetyPlant = Pick<
  Plant,
  "pet_safety" | "toxic_cats" | "toxic_dogs" | "placement_tip"
>;

function petList(pets: string[]): string {
  if (pets.length === 1) return pets[0];
  return `${pets.slice(0, -1).join(", ")} and ${pets.at(-1)}`;
}

export function buildPetSafetyMessage(
  plant: PetSafetyPlant,
  userPets: PetType[],
): string | undefined {
  if (!plant.pet_safety) return undefined;

  const hasCats = userPets.includes("Cats");
  const hasDogs = userPets.includes("Dogs");
  const hasBirds = userPets.includes("Birds");
  const knownPets = [hasCats ? "cat" : null, hasDogs ? "dog" : null].filter(
    (pet): pet is string => Boolean(pet),
  );
  const affectedPets = [
    hasCats && plant.toxic_cats ? "cat" : null,
    hasDogs && plant.toxic_dogs ? "dog" : null,
  ].filter((pet): pet is string => Boolean(pet));
  const messages: string[] = [];

  if (affectedPets.length) {
    const risk = plant.pet_safety === "mild" ? "Mild risk" : "Toxic";
    messages.push(`${risk} for your ${petList(affectedPets)}.`);
  } else if (plant.pet_safety === "safe" && knownPets.length) {
    messages.push(`Listed as pet-safe for your ${petList(knownPets)}.`);
  } else if (!hasBirds) {
    const classification = plant.pet_safety === "mild" ? "Mild risk" : "Toxic";
    messages.push(`${classification} for cats or dogs.`);
  }

  if (hasBirds) {
    messages.push("Safety for your bird is not covered by the current cat and dog dataset.");
  }

  if (plant.placement_tip) messages.push(plant.placement_tip);
  return messages.join(" ");
}
