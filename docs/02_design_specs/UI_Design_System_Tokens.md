# UI Design System & Token Specifications
## Liquid Glassmorphic Design for Modern Governance Dashboards

### 1. Visual Aesthetics & Philosophy

The user interface follows an Apple iOS 26 inspired **Liquid Glassmorphism** aesthetic, optimized for high-density administrative data consumption:
- High contrast, dark and light tailored HSL tokens.
- Translucent backdrop blur filters (`backdrop-filter: blur(20px)`).
- Crisp micro-borders (`1px solid rgba(255, 255, 255, 0.12)`).
- Subdued typography combining modern sans-serif headings with Times New Roman italic accents for state prestige.

### 2. Design Tokens (`tokens.css`)

```css
:root {
  --font-sans: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, sans-serif;
  --font-serif: "Times New Roman", Times, serif;

  /* Color Palette */
  --color-canvas: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-translucent: rgba(255, 255, 255, 0.78);
  --color-ink: #0f172a;
  --color-ink-muted: #64748b;
  --color-primary: #0284c7;
  --color-primary-hover: #0369a1;

  /* Status Colors */
  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;

  /* Elevation & Glass */
  --glass-blur: blur(16px);
  --glass-border: 1px solid rgba(0, 0, 0, 0.06);
  --shadow-card: 0 4px 20px -2px rgba(0, 0, 0, 0.05);
  --radius-pill: 9999px;
  --radius-card: 16px;
}
```

### 3. Responsive Breakpoints

- **Desktop:** `1440px` (Max layout container, multi-column analytical panels).
- **Tablet:** `768px` to `1024px` (Adaptive stacked layout, horizontal scroll pills).
- **Mobile:** `375px` to `480px` (Single column cards, high-contrast KPI badges).
