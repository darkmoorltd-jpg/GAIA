# GAIA Brand Guidelines v1.0

> Global Agricultural Intelligence Assistant
> Last updated: August 25, 2026

---

## 1. Brand Overview

**Name:** GAIA (Global Agricultural Intelligence Assistant)

**Mission:** Empower farmers with AI-driven agricultural intelligence — diagnose crops instantly, detect pests early, and make data-driven farming decisions.

**Vision:** Every farmer has an expert agronomist in their pocket.

**Values:** Accessible, Reliable, Farmer-first, Data-driven

---

## 2. Brand Voice & Tone

### Voice Characteristics
| Trait | Do | Don't |
|-------|-----|-------|
| **Helpful** | "Here's what we found on your leaf photo" | "Your image has been processed by our AI model" |
| **Clear** | Use simple language farmers understand | Use technical jargon without explanation |
| **Confident** | "This looks like Common Rust at 87% confidence" | "It might possibly be some kind of disease" |
| **Warm** | Speak like a trusted agricultural advisor | Sound robotic or corporate |

### Messaging Framework
- **Tagline:** "Your pocket agronomist"
- **Elevator pitch:** GAIA helps farmers diagnose crop diseases, detect pests, and analyze soil using just a smartphone photo — no agronomist visit needed.
- **Key messages:**
  1. Instant answers: Get results in seconds, not days
  2. Works anywhere: No internet needed for saved scans
  3. Trusted science: Trained on 100,000+ labeled images

---

## 3. Color System

### Primary Palette
| Token | Hex | Usage | Contrast |
|-------|-----|-------|----------|
| `primary-600` | `#16a34a` | Primary buttons, active nav, links | 4.5:1 on white ✅ |
| `primary-700` | `#15803d` | Hover state, headings | 5.2:1 on white ✅ |
| `primary-800` | `#166534` | Dark text on light bg | 7.1:1 on white ✅ |

### Background
| Token | Hex | Usage |
|-------|-----|-------|
| `primary-50` | `#f0fdf4` | Page background, subtle fills |
| `white` | `#ffffff` | Cards, panels, sidebar |

### Semantic Colors
| Purpose | Token | Hex |
|---------|-------|-----|
| Error | `red-500` | `#ef4444` |
| Warning | `amber-500` | `#f59e0b` |
| Success | `green-500` | `#22c55e` |
| Info | `blue-500` | `#3b82f6` |

### Rules
1. Never use green-on-red or red-on-green (colorblind accessibility)
2. Always pair color changes with icons or text labels
3. Body text minimum contrast ratio: 4.5:1
4. Large heading contrast ratio: 3:1 minimum

---

## 4. Typography

### Font Stack
| Level | Font | Weight | Size | Line Height |
|-------|------|--------|------|-------------|
| H1 | Plus Jakarta Sans | 800 (ExtraBold) | 36px / 2.25rem | 1.25 |
| H2 | Plus Jakarta Sans | 700 (Bold) | 24px / 1.5rem | 1.33 |
| H3 | Plus Jakarta Sans | 700 (Bold) | 20px / 1.25rem | 1.4 |
| Body | Inter | 400 (Regular) | 16px / 1rem | 1.5 |
| Small | Inter | 400 (Regular) | 14px / 0.875rem | 1.43 |
| Caption | Inter | 500 (Medium) | 12px / 0.75rem | 1.33 |

### Rules
1. Never use font size below 12px for body text
2. Maximum line length: 80 characters (~640px) for readability
3. Bold only for emphasis, not entire paragraphs
4. All headings use sentence case (not ALL CAPS except acronyms)

---

## 5. Spacing System

Base unit: **4px** (Tailwind spacing scale)

| Element | Padding | Gap |
|---------|---------|-----|
| Page container | 16px mobile, 32px desktop | — |
| Card padding | 20px (p-5) | 16px between cards |
| Button padding | 12px vertical, 24px horizontal | — |
| Form field gap | 12px vertical | — |
| Section gap | 32px between sections | — |

### Touch Targets
- Minimum button height: **48px** (WCAG + Material Design)
- Minimum touch target width: **44px**
- Minimum gap between interactive elements: **8px**

---

## 6. Iconography

### Style
- Use emoji as temporary placeholders (will be replaced with custom SVG icon set)
- Final icons: Lucide React (open source, matches minimal style)
- Size: 24×24px in nav, 48×48px in feature cards
- Stroke weight: 2px consistent

### Rules
- Never use emoji as the ONLY indicator of function
- Always pair icons with text labels in navigation
- Active state icons use `primary-700`, inactive use `gray-500`

---

## 7. Imagery

### Style
- Source: Unsplash (free license, high quality agriculture photos)
- Treatment: Rounded corners (rounded-xl = 12px), subtle shadow
- Overlay: Dark gradient from bottom (black/70 → transparent) for text readability

### Approved Images (by page)
| Page | Unsplash ID | Description |
|------|-------------|-------------|
| Dashboard | `photo-1556801712` | Green farm aerial view |
| Crops | `photo-1600112356` | Maize field close-up |
| Pests | `photo-1590691566` | Insects on leaf macro |
| Soil | `photo-1466692476` | Rich soil/earth texture |
| Livestock | `photo-1570042225` | Cattle herd grazing |
| Video Scan | `photo-1615485290` | Drone over farm field |
| Calendar | `photo-1500382017` | Sunrise over farmland |

---

## 8. Component Standards

### Buttons
| Variant | Background | Text | Border | Hover |
|---------|-----------|------|--------|-------|
| Primary | `primary-600` | White | None | `primary-700` |
| Secondary | `primary-50` | `primary-700` | None | `primary-100` |
| Ghost | Transparent | `primary-700` | None | `primary-50` |
| Disabled | `gray-200` | `gray-400` | None | No hover |

### Cards
- Border radius: 12px (`rounded-xl`)
- Shadow: `shadow-md` (resting), `shadow-lg` (hover)
- Border: `border-neutral-100`
- Padding: 20px internal

### Forms
- Input border: 2px solid `neutral-300`, rounded-lg
- Focus state: 2px outline `primary-600` with 2px offset
- Error state: Red border + message below input
- Label position: Above input, left-aligned, 14px medium

---

## 9. Animation Standards

| Interaction | Duration | Easing |
|------------|----------|--------|
| Hover states | 150ms | ease-out |
| Page transitions | 200ms | ease-in-out |
| Sidebar slide | 250ms | spring (damping: 25, stiffness: 250) |
| Loading spinners | Continuous linear | — |
| Toast dismiss | 300ms | ease-in |

### Rules
1. Respect `prefers-reduced-motion` system setting
2. Never animate width/height (causes layout thrash)
3. Use transform + opacity only (GPU-accelerated)
4. Every animation must convey meaning (state change, spatial relationship)

---

## 10. Accessibility Checklist

- [ ] All text meets 4.5:1 contrast ratio
- [ ] Interactive elements ≥ 44×44px touch targets
- [ ] Focus visible on all interactive elements (2px primary ring)
- [ ] Alt text on all meaningful images
- [ ] Aria-labels on icon-only buttons
- [ ] Keyboard navigation works for all flows
- [ ] Forms have visible labels (not placeholder-only)
- [ ] Color is never the sole indicator of meaning
- [ ] Reduced motion respected
- [ ] Heading hierarchy is sequential (no skipped levels)
