import { PawPrint } from "@phosphor-icons/react";

import { petOptions, type PetType } from "@/types/user";


interface PetSelectorProps {
  value: PetType[];
  onChange: (value: PetType[]) => void;
  error?: string;
}

export function PetSelector({ value, onChange, error }: PetSelectorProps) {
  function toggle(option: PetType) {
    if (option === "No pets") {
      onChange(value.includes(option) ? [] : [option]);
      return;
    }

    const withoutNone = value.filter((item) => item !== "No pets");
    onChange(
      withoutNone.includes(option)
        ? withoutNone.filter((item) => item !== option)
        : [...withoutNone, option],
    );
  }

  return (
    <fieldset className="grid gap-2" aria-describedby={error ? "pets-error" : undefined}>
      <legend className="flex items-center gap-2 text-sm font-semibold text-[var(--text)]">
        <PawPrint size={17} weight="duotone" aria-hidden="true" />
        Pets in your home
      </legend>
      <p className="text-xs leading-5 text-[var(--text-soft)]">
        This keeps future care guidance mindful of curious paws, feathers, and fins.
      </p>
      <div className="mt-1 flex flex-wrap gap-2">
        {petOptions.map((option) => {
          const checked = value.includes(option);
          return (
            <label
              key={option}
              className={`cursor-pointer rounded-full border px-3 py-2 text-sm font-semibold transition-colors ${
                checked
                  ? "border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent)]"
                  : "border-[var(--line)] bg-[var(--surface-raised)] text-[var(--text-muted)] hover:border-[var(--line-strong)]"
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={checked}
                onChange={() => toggle(option)}
              />
              {option}
            </label>
          );
        })}
      </div>
      {error && (
        <span id="pets-error" className="text-xs font-medium text-[var(--risk)]">
          {error}
        </span>
      )}
    </fieldset>
  );
}
