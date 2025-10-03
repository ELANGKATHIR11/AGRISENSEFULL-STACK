# AgriSense Brand & Logo Usage Guide

## 1. Brand Essence
AgriSense represents the fusion of:  
- Sustainable Green Farming 🌱  
- Applied AI & Machine Learning 🤖  
- Connected IoT Infrastructure 📡  
- Precision Water & Nutrient Intelligence 💧  
- Climate-aware Optimization ☁️  

## 2. Logo System
| Variant | File | Purpose |
|---------|------|---------|
| Primary Full Lockup | `agrisense_logo.svg` | Marketing pages, hero sections, documents |
| Icon Mark | `agrisense_logo_icon.svg` | App launcher, mobile nav, compact UI |
| Dark Variant | `agrisense_logo_dark.svg` | Dark backgrounds / night mode |
| Monochrome | `agrisense_logo_monochrome.svg` | Single-color print, emboss, watermark |
| Favicon | `favicon.svg` | Browser tabs, PWA manifest |

## 3. Symbol Anatomy
The symbol blends five conceptual layers:
1. Outer dashed circular ring → sustainability & cyclical precision agriculture
2. Leaf form → crop vitality / agronomy foundation
3. Water droplet carve-out → precision irrigation focus
4. Neural graph nodes & links → AI/ML inference network
5. Radiating arcs → IoT telemetry & wireless sensor mesh

## 4. Color Palette
| Token | Hex | Usage |
|-------|-----|-------|
| Primary Deep Green | `#14532d` | Core wordmark (Agri), headings |
| Primary Mid Green | `#198754` | Leaf gradients, accents |
| Emerald Accent | `#2e9d62` | Highlights, buttons hover |
| AI Cyan | `#06b6d4` | Neural nodes, analytics emphasis |
| AI Sky | `#0ea5e9` | Gradients, data glyphs |
| IoT Orange | `#f97316` | Connectivity arcs, active signals |
| IoT Amber | `#fb923c` | Secondary IoT emphasis |
| Water Light | `#38bdf8` | Hydration metrics, charts |
| Water Deep | `#0369a1` | Depth shading |
| Background Mist | `#f0fdf4` | Light thematic surfaces |
| Dark Base | `#0a0f0d` | Dark variant background |

Accessibility: Aim for 4.5:1 contrast for body text. Use deep green or near-black on light backgrounds; use off-white `#f0fdf4` or `#e6ffee` on deep green backgrounds.

## 5. Clear Space & Minimum Sizes
- Clear space: Maintain padding equal to the height of the neural node circle (≈ leaf inner circle diameter).  
- Minimum display sizes:
  - Full lockup: 260px width (below this tagline should be dropped)
  - Icon mark: 24px (SVG scales cleanly; avoid rasterizing for UI)
  - Favicon: Provided vector—browser will rasterize for you

## 6. Improper Usage (Avoid)
🚫 Do not stretch or distort proportions  
🚫 Do not recolor with arbitrary hues  
🚫 Do not apply drop shadows beyond provided glow variants  
🚫 Do not separate neural graph nodes from leaf outside icon context  
🚫 Do not put light variant on light photographic backgrounds without contrast panel  
🚫 Do not rotate the symbol arbitrarily  

## 7. Dark Mode Guidance
Use `agrisense_logo_dark.svg` on backgrounds darker than `#10221a`.  
Fallback: If gradients are disabled, replace with `agrisense_logo_monochrome.svg` in a single accessible color.

## 8. Integration Snippets
### React Import Example
```tsx
import LogoFull from "@/assets/branding/agrisense_logo.svg";
import LogoIcon from "@/assets/branding/agrisense_logo_icon.svg";

export function BrandHeader() {
  return (
    <header className="flex items-center gap-3">
      <img src={LogoIcon} alt="AgriSense" className="h-10 w-10" />
      <img src={LogoFull} alt="AgriSense Smart Farming Intelligence" className="h-10 hidden md:block" />
    </header>
  );
}
```

### HTML Embed
```html
<img src="/assets/branding/agrisense_logo.svg" alt="AgriSense – Smart Farming Intelligence" width="320" />
```

### Favicon (HTML Head)
```html
<link rel="icon" type="image/svg+xml" href="/assets/branding/favicon.svg" />
```

## 9. Thematic Usage Mapping
| Discipline | Visual Cue |
|------------|------------|
| Soil Health | Deep greens & leaf form |
| Irrigation | Water gradient + droplet overlay |
| AI Insights | Cyan/teal neural connections |
| IoT Devices | Orange radiating arcs |
| Sustainability | Circular dashed loop |
| Climate | Muted teal overlays |

## 10. Motion & Animation (Optional)
Suggested subtle animations for hero contexts:
- IoT arcs: stroke-dashoffset pulse (4–6s ease)
- Neural nodes: soft scale + glow (6–8s stagger)
- Leaf: very subtle vertical parallax (2–3px range)

## 11. File Inventory
```
src/assets/branding/
  agrisense_logo.svg
  agrisense_logo_icon.svg
  agrisense_logo_monochrome.svg
  agrisense_logo_dark.svg
  favicon.svg
  BRANDING_GUIDE.md
```

## 12. Licensing & Attribution
All branding assets © 2025 AgriSense.  
Internal + partner use only. Redistribution requires explicit approval.

---
For enhancements (animated SVG variants, font pairing refinements, adaptive dark-mode theming) request: `extend branding system`.
