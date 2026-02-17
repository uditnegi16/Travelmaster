type Props = {
  label: string;
  onClick?: () => void;
  href?: string;
};

export default function DarkButton({ label, onClick, href }: Props) {
  const classes =
    "inline-flex items-center gap-3 rounded-sm bg-white/15 px-5 py-3 text-sm text-white backdrop-blur hover:bg-white/20 transition";

  if (href) {
    return (
      <a className={classes} href={href}>
        {label} <span aria-hidden>→</span>
      </a>
    );
  }

  return (
    <button className={classes} onClick={onClick} type="button">
      {label} <span aria-hidden>→</span>
    </button>
  );
}
