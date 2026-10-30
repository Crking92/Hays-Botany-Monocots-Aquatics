# Monocots & Aquatics — source migration and website QA checkpoint (October 30, 2026)

## Existing source: PASS

Checked branch `staging/original-source-transfer` against `migration/original-source-transfer-manifest.json`, using Git tree `5fe8eb4f91dbc00b716b33a6d461a64e6bdf2b50`.

| Metric | Audited result |
|---|---:|
| Assigned families | 26 |
| Source species | 113 |
| Original source files | **587/587 matching their recorded Git blob SHA** |
| Original scientific / credit files | 382 |
| Original image bytes preserved | 205 |
| Missing original files | 0 |
| Hash mismatches | 0 |

The archived photo images and attribution files remain preserved, not newly harvested. The historic source manifest is pinned to hub commit `515387cbc23b8bf8931141ead9c44c92a7793699`.

## Public main learner: audited contents

Before this checkpoint, public main tree `e20e93d0abcc774472a1abb615f21c2c5e1a09bf` contained **113 species JSON files**, **35 actual hosted media files**, and one gallery index that recorded **35 images / 23 species**, consistent with the existing photo-release report. **176 source image references remain held from public display.** No new photo bytes or new plant data were added by this audit.

The [last inspected GitHub Pages deployment](https://github.com/Crking92/Hays-Botany-Monocots-Aquatics/actions/runs/40910176003) succeeded. That verifies publication execution, not independent HTTP validation of every public photo. The new `scripts/verify_existing_site.py` and `verify-existing-site-gallery.yml` perform full local and live photo/hash and 113-card checks. Treat live end-to-end status as verified only when that job actually passes.

### Safety and follow-up

- Historic `README.md` used outdated PRIVATE and NOT-PUBLISHED wording; updated to distinguish source staging, the public photo-backed learner and editorial ownership.
- Source holds are **not private** while the repository and its Git history are public. This is a separate image-rights exposure concern; do not automatically delete or rewrite history or introduce new unverified bytes.
- Existing image credits must describe **unmodified source originals**, not inaccurately claim that an exact-copy photo was resized.
- Historical red text-only publication jobs are intentional protection against overwriting existing photo pages; do not override them.
- Old hub remains unchanged, the family source-writing registry continues to govern new edits, and automations remain paused.
- Family source migration can be marked complete without resolving photo-rights holds or collecting new images.
- Next family-group collection for this transfer-only QA sweep: **Asterid Allies**.

**Closeout scope:** existing file preservation, public site structure/photo link integrity, credit consistency, and separate live Pages verification. Does not assert field-ready diagnostic anatomy, county-nativity review, or future enrichment completeness.
