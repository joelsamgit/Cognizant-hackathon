import { forwardRef } from "react";


type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: "sm" | "md";
}

const variants: Record<ButtonVariant, string> = {
  primary:
    "border-transparent bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] dark:text-[#101a14]",
  secondary:
    "border-[var(--line-strong)] bg-[var(--surface-raised)] text-[var(--text)] hover:border-[var(--accent)] hover:text-[var(--accent)]",
  ghost:
    "border-transparent bg-transparent text-[var(--text-muted)] hover:bg-[var(--page-muted)] hover:text-[var(--text)]",
  danger:
    "border-transparent bg-[var(--danger)] text-white hover:brightness-90 dark:text-[#1a0e0d]",
};

const sizes = {
  sm: "min-h-9 px-3 text-sm",
  md: "min-h-11 px-4 text-sm",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { className = "", variant = "primary", size = "md", type = "button", ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={`inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full border font-semibold transition-[background-color,border-color,color,transform,opacity] duration-200 active:translate-y-px disabled:opacity-55 ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    />
  );
});

