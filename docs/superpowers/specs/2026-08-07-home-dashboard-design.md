# Home Page Dashboard Redesign

## Goal

Turn the current hero-heavy home page into a dashboard-style page: a compact hero (title + lookup form) followed by a full-width row of KPI cards, then the existing patient list unchanged. Metrics are scoped to what serves this app's actual purpose — patient record lookup and AI summarization — not hospital operational analytics (no admission trend charts, no department distribution).

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

1. **Hero section**: remove the existing 2x2 "TỔNG QUAN HỒ SƠ" stats card (lines ~172-207) entirely. Hero keeps only the title, subtitle, and lookup form. Hero grid changes from two columns (`grid-cols-[1.05fr_0.95fr]`) to a single column, reduced bottom margin.
2. **New `KpiRow` section**: full-width row directly below hero, above "Danh sách bệnh nhân". Grid: `grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4`. This breakpoint progression is chosen specifically to avoid the horizontal-overflow bug observed earlier in the 660-800px range — cards reflow to fewer columns instead of clipping.
3. Each KPI card: white background, rounded corners consistent with existing card style (`border border-[#ECEFF6] rounded-[8px]`), big number + label, matching the visual language of the existing stat cells (font sizes ~28-30px bold for the number, ~13px medium gray for the label).
4. Patient list section (filters, cards, pagination) is unchanged.

## Loading / error states

While `loading` is true, KPI cards show `—` placeholders (same convention as current stats card). No skeleton needed for the KPI row specifically — it's a small, fast-computing derived value once the fetch resolves.

## Out of scope

- No admission trend charts, no department distribution charts (explicitly rejected — hospital operational analytics, not this app's job).
- No average length-of-stay KPI (explicitly rejected — reference-only info, doesn't serve the lookup/Q&A/summary workflow).
- No backend/API changes.
- No changes to patient detail page or AI summary/chat panel.
