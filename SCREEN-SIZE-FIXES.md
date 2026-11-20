# Screen-size fixes (v2) and what they mean for the Divi build

Source: Chris's *Screen-size audit* (19 November 2026, tested against commit c13e3ee) and his note that "when I shrink screen sizes some things stay left aligned".

All CSS sits at the end of the `<style>` block in `v2/index.html`, numbered to match the audit. No wording changed. The root (approved v1) page was checked at 1024, 820, 600 and 390px and has no capped, left-stuck blocks, so it is unchanged.

## The left-aligned problem (fix 17)

Every form is capped at 640px wide once it drops below the text. Until now it then sat on the left, leaving 130 to 380px of empty space on its right on tablets and small laptop windows. It is now centred.

| Where | Stacks at | Divi setting |
|---|---|---|
| Home hero form | 1099px and narrower | Form column/module: Max Width 640px, Module Alignment **Center** on Tablet |
| Guide pages, form beside the article (`.aside`) | 1020px and narrower | Same, on the sidebar column |
| Turning 65 inline form | 1020px and narrower | Same |
| Contact, FAQ, Seminars form (`.cols2`) | 980px and narrower | Same |

In Divi, set the alignment on the **Tablet** (and Phone) tab of the module's Sizing settings, not only Desktop, or the module keeps the desktop left alignment.

## Audit fixes 1 to 16

Applied as written in the audit, plus its two script changes (phone menu height, short years in the seven-month tool). For fix 9 the plain-text phone numbers in the page body (1-800-MEDICARE and the office number) are wrapped in `<span class="nb">`; FAQ question lines and script-built text were left alone. "Part A/B/C/D" in the page body now use a non-breaking space so they never split across lines ("Plan G" only appears in script-built text, which was left alone).

## Breakpoints to set up in Divi 5 first

The preview changes layout at many widths; these are the ones that matter:

- **1160px**: desktop menu above, burger menu below
- **1099px**: home hero form drops under the headline (centred)
- **1020px**: guides drop to one column, form centred under the article
- **980px**: Contact/FAQ/Seminars form drops under the text (centred)
- **767px**: mobile call bar appears
- **520px**: phone header (phone number hidden, smaller logo)

## Checked

- Every route, 288 to 1700px every 7px: no sideways scrolling.
- Visible text on 17 routes identical before and after.
- Screens at 820px (Contact, Plan review), 375px (seven-month tool) and 390px (Medigap chart).
- Only Chrome's engine was available; the audit asks for a spot check on a real iPhone and iPad in Safari.
