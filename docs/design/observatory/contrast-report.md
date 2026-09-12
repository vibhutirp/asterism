# Observatory contrast calculations

Calculated from the declared opaque sRGB tokens using relative luminance and (lighter + 0.05) / (darker + 0.05). These are palette-pair calculations, not rendered-page accessibility validation. The results exclude glow, anti-aliasing and variable backgrounds. Map labels must use the specified opaque backing; do not assume these ratios apply directly to a nebula image.

49 specified pairings pass their assigned thresholds. Normal text uses 4.5:1; focus and necessary control boundaries use 3:1. Quiet dividers are decorative and must never be the sole way to recognize a control. Disabled controls are not counted as active controls.

| Foreground | Background | Ratio | Threshold | Result |
|---|---|---:|---:|---|
| primary | panel | 15.806 | 4.5 | Pass |
| primary | raised | 13.980 | 4.5 | Pass |
| primary | hover | 12.146 | 4.5 | Pass |
| primary | labelBacking | 14.422 | 4.5 | Pass |
| secondary | panel | 9.870 | 4.5 | Pass |
| secondary | raised | 8.730 | 4.5 | Pass |
| secondary | hover | 7.585 | 4.5 | Pass |
| secondary | labelBacking | 9.006 | 4.5 | Pass |
| muted | panel | 7.110 | 4.5 | Pass |
| muted | raised | 6.288 | 4.5 | Pass |
| muted | hover | 5.463 | 4.5 | Pass |
| muted | labelBacking | 6.487 | 4.5 | Pass |
| icon | panel | 14.451 | 4.5 | Pass |
| icon | raised | 12.782 | 4.5 | Pass |
| icon | hover | 11.105 | 4.5 | Pass |
| icon | labelBacking | 13.186 | 4.5 | Pass |
| link | panel | 9.860 | 4.5 | Pass |
| link | raised | 8.721 | 4.5 | Pass |
| link | hover | 7.577 | 4.5 | Pass |
| link | labelBacking | 8.997 | 4.5 | Pass |
| focus | panel | 12.581 | 3.0 | Pass |
| focus | raised | 11.128 | 3.0 | Pass |
| focus | hover | 9.668 | 3.0 | Pass |
| focus | labelBacking | 11.480 | 3.0 | Pass |
| product | panel | 8.685 | 4.5 | Pass |
| product | raised | 7.682 | 4.5 | Pass |
| product | hover | 6.674 | 4.5 | Pass |
| product | labelBacking | 7.924 | 4.5 | Pass |
| personal | panel | 11.145 | 4.5 | Pass |
| personal | raised | 9.858 | 4.5 | Pass |
| personal | hover | 8.564 | 4.5 | Pass |
| personal | labelBacking | 10.169 | 4.5 | Pass |
| saved | panel | 11.145 | 4.5 | Pass |
| saved | raised | 9.858 | 4.5 | Pass |
| saved | hover | 8.564 | 4.5 | Pass |
| saved | labelBacking | 10.169 | 4.5 | Pass |
| processing | panel | 9.806 | 4.5 | Pass |
| processing | raised | 8.674 | 4.5 | Pass |
| processing | hover | 7.536 | 4.5 | Pass |
| processing | labelBacking | 8.948 | 4.5 | Pass |
| error | panel | 10.524 | 4.5 | Pass |
| error | raised | 9.309 | 4.5 | Pass |
| error | hover | 8.087 | 4.5 | Pass |
| error | labelBacking | 9.603 | 4.5 | Pass |
| controlBorder | panel | 4.171 | 3.0 | Pass |
| controlBorder | raised | 3.689 | 3.0 | Pass |
| controlBorder | hover | 3.205 | 3.0 | Pass |
| onAccent | accent | 8.802 | 4.5 | Pass |
| badgeText | badgeSurface | 9.707 | 4.5 | Pass |

References: [W3C text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [W3C non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). Ratios are evaluated before rounding; displayed decimals are for readability.
