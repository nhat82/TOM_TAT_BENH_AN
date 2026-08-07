# Home Page Dashboard Redesign

## Goal

Turn the home page into a pure dashboard: no hero/title section. Page opens directly with a full-width row of KPI cards, then the existing patient list. Patient lookup-by-code already lives in the sticky `Header` search box (Enter navigates to `/patient/:id`), so removing the hero's own lookup form loses no functionality. Metrics are scoped to what serves this app's actual purpose — patient record lookup and AI summarization — not hospital operational analytics (no admission trend charts, no department distribution).

Built with shadcn/ui components (Card, Badge) instead of hand-rolled inline-styled divs.

## shadcn/ui setup

Not yet present in this project (no `components.json`, no `cn()` helper, no `class-variance-authority`). Full CLI init, project-wide, reusable for future pages:

- `npx shadcn@latest init` — creates `components.json`, `src/lib/utils.ts` (`cn` helper), adds `clsx`, `tailwind-merge`, `class-variance-authority`, `tailwindcss-animate`.
- Updates `tailwind.config.js` with shadcn's CSS-variable-based color tokens and `frontend/src/index.css` with the `:root` variable block (light theme only — this app has no dark mode toggle today, so no dark variant block needed).
- Add components actually used: `npx shadcn@latest add card badge`.
- Existing custom Tailwind tokens (`primary`, `on-surface`, etc. — see `tailwind.config.js`) stay as-is; shadcn's own tokens (`--primary`, `--card`, etc.) are additive, not a replacement. The KPI cards use shadcn's `Card`/`Badge`; the rest of the page (patient list, Header, Footer) is untouched and keeps its existing custom classes.

## Data source

`GET /api/patients` returns rows shaped like `RawPatient` (frontend/src/pages/HomePage.tsx):
`ma_bn_an, birthdayyear, departmentid, medicalrecorddate_in, medicalrecorddate_out, chandoan_out_main, chandoan_in`.

No backend changes required. All 5 KPIs are derivable from this existing payload.

## KPI cards (5, full width row)

| # | Label | Computation | Color intent |
|---|-------|-------------|---------------|
| 1 | Tổng hồ sơ | `patients.length` | neutral blue |
| 2 | Đang điều trị | count where `medicalrecorddate_out` is empty | blue |
| 3 | Đã ra viện | count where `medicalrecorddate_out` is set | green |
| 4 | Hồ sơ mới (7 ngày) | count where `medicalrecorddate_in` falls within the last 7 days from now | indigo/purple |
| 5 | Thiếu chẩn đoán ra viện | count where discharged (`medicalrecorddate_out` set) AND `chandoan_out_main` is empty | amber/red (warning) |

KPI 5 is a data-quality signal: a discharged record with no final diagnosis degrades AI summary quality, which is directly relevant to this app's core feature.

### Data model changes needed

`mapRawPatient` currently collapses `chandoan_out_main || chandoan_in` into a single `diagnosis` string, discarding whether the out-diagnosis was actually present, and discards the raw admission date after formatting it into a relative string. `Patient` interface needs two additional fields:

- `rawVisitDate: string` (original `medicalrecorddate_in`, ISO string, kept for the 7-day window calc)
- `missingOutDiagnosis: boolean` (`discharged && !r.chandoan_out_main`)

These are computed once in `mapRawPatient` alongside the existing fields, no new API calls.

## Layout changes (frontend/src/pages/HomePage.tsx)

1. **Hero section removed entirely** — no title, no subtitle, no lookup form, no 2x2 stats card. `main` starts directly with the KPI row (with normal page top padding).
2. **New `KpiRow` section**: full-width row at the top of `main`, above "Danh sách bệnh nhân". Grid: `grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4`. This breakpoint progression is chosen specifically to avoid the horizontal-overflow bug observed earlier in the 660-800px range — cards reflow to fewer columns instead of clipping.
3. Each KPI card is a shadcn `Card`: number + label, KPI 5 additionally uses a shadcn `Badge` (amber/warning variant) when its count is > 0 to visually flag it apart from the other four.
4. Patient list section (filters, cards, pagination) is unchanged.

## Loading / error states

While `loading` is true, KPI cards show `—` placeholders (same convention as the old stats card). No skeleton needed for the KPI row specifically — it's a small, fast-computing derived value once the fetch resolves.

## Out of scope

- No admission trend charts, no department distribution charts (explicitly rejected — hospital operational analytics, not this app's job).
- No average length-of-stay KPI (explicitly rejected — reference-only info, doesn't serve the lookup/Q&A/summary workflow).
- No backend/API changes.
- No changes to patient detail page, AI summary/chat panel, or Header (its search box already covers the removed hero's lookup function).
- shadcn init only adds components actually used here (Card, Badge) — not a wholesale migration of Header/Footer/patient list to shadcn.
