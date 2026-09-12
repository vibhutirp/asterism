import { useId, useState } from 'react';
import type { ButtonHTMLAttributes, ReactNode, Ref } from 'react';

type Props = Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> & {
  label: string; children: ReactNode; explanation?: string; tipSide?: 'right' | 'below'; ref?: Ref<HTMLButtonElement>;
};

export function IconControl({ label, children, explanation, tipSide = 'right', disabled, ref, onClick, ...props }: Props) {
  const id = useId();
  const [hovered, setHovered] = useState(false), [focused, setFocused] = useState(false);
  return <span className={`icon-control-wrap tooltip-${tipSide}`} onPointerEnter={() => setHovered(true)} onPointerLeave={() => setHovered(false)}>
    <button {...props} ref={ref} type="button" className="map-icon-button" aria-label={label} aria-disabled={disabled || undefined}
      aria-describedby={hovered || focused ? id : undefined} onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
      onClick={event => { if (!disabled) onClick?.(event); }}>
      {children}
    </button>
    {(hovered || focused) && <span id={id} role="tooltip" className="control-tooltip" data-scene-obstacle>{explanation || label}</span>}
  </span>;
}
