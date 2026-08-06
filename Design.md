# Design.md — Visual Design Guidelines

## 1. Design Philosophy

The product's core metaphor is "Grammarly for code" — the UI should feel calm, precise, and non-judgmental, even when flagging serious issues. Borrow Grammarly's core UX trick: problems are shown as gentle inline underlines/highlights, not alarming red banners, so users don't feel attacked by their own AI-generated code.

Secondary influence: a code-editor aesthetic (think VS Code / Linear) — technical users should feel at home, not like they're in a generic SaaS dashboard.

## 2. Color Palette

**Base (Light Mode)**
| Role | Color | Hex |
|---|---|---|
| Background | Off-white | `#FAFAF8` |
| Surface / Cards | White | `#FFFFFF` |
| Primary text | Near-black | `#1A1A1A` |
| Secondary text | Gray | `#6B7280` |
| Border | Light gray | `#E5E7EB` |

**Base (Dark Mode — default for a dev-focused tool)**
| Role | Color | Hex |
|---|---|---|
| Background | Deep charcoal | `#0F1115` |
| Surface / Cards | Slightly lighter charcoal | `#1A1D23` |
| Primary text | Off-white | `#F3F4F6` |
| Secondary text | Muted gray | `#9CA3AF` |
| Border | Subtle gray | `#2A2E37` |

**Accent / Status Colors**
| Meaning | Color | Hex |
|---|---|---|
| Primary brand accent | Teal/green (growth, "polish") | `#2DD4A7` |
| Security issue (high severity) | Warm red | `#EF4444` |
| Structure issue (medium) | Amber | `#F59E0B` |
| Style/naming suggestion (low) | Blue | `#3B82F6` |
| Verified/fixed | Green | `#22C55E` |

## 3. Typography

- **UI font:** Inter or system sans-serif — clean, neutral, highly legible at small sizes
- **Code font:** JetBrains Mono or Fira Code — monospace, ligatures optional but nice for a dev tool
- **Headings:** Semi-bold, slightly larger tracking for section titles (Readiness Score, Suggestions, etc.)
- **Body/UI text:** Regular weight, 14–16px base size
- **Diff/code blocks:** 13–14px monospace, with syntax highlighting matching the language

## 4. Key UI Surfaces

**Upload Screen**
- Minimal, centered — drag-and-drop zone, GitHub URL input, "paste code" toggle
- Should feel like a single clear action, not a cluttered dashboard

**Readiness Score Dashboard**
- Large single score (0–100) front and center
- Category breakdown as horizontal bars or a radar chart (Structure / Security / Error Handling / Style / Docs)
- Color-coded by severity using the accent palette above

**Diff / Suggestion View**
- Split or inline diff, code on monospace font
- Each suggestion shown as a subtle colored underline in the code, matching severity color
- Hover/click reveals an explanation card with Accept / Reject buttons
- Accepted fixes shown with a green checkmark once sandbox-verified

**Sandbox Status Indicator**
- Small, persistent status chip: "Verifying in sandbox…" / "Verified ✓" / "Verification failed — reverted"
- Should build trust — always visible when a fix is being tested, never a silent background process

## 5. Tone & Microcopy

- Avoid alarming language: "3 issues found" not "3 ERRORS DETECTED"
- Explanatory, not condescending: "This function has no error handling — if it fails, the app will crash silently" rather than "Bad code!"
- Celebrate progress: readiness score increasing after fixes should feel rewarding, similar to Grammarly's "your writing is clearer now" framing
