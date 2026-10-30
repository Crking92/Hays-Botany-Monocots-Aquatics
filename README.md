# Hays Botany — Monocots & Aquatics

**Existing-source migration: COMPLETE. Public family learner: ACTIVE (existing rights-filtered subset). Botanical/photo enrichment: DEFERRED.**

[Open the Monocots & Aquatics Visual Learner](https://crking92.github.io/Hays-Botany-Monocots-Aquatics/site/) · [Original read-only hub](https://crking92.github.io/Hays-County-Botany/) · [Active family routing registry](https://github.com/Crking92/Hays-County-Botany/blob/main/workflow/ACTIVE_NEW_PLANT_WRITE_ROUTING_20261028.json)

This collection contains **113 original species lessons in 26 assigned families**. The original historic source was transferred to branch [`staging/original-source-transfer`](https://github.com/Crking92/Hays-Botany-Monocots-Aquatics/tree/staging/original-source-transfer); new botanical edits for these assigned families route to that branch, **not** the old hub. Staging is not automatically merged with the public site.

## Source-preservation verification — October 30, 2026

- **587/587** original source files are present at the manifest destinations with identical Git blob hashes: **382 scientific/credit text files + 205 original photo files**.
- **0 missing source files, 0 byte mismatches** in the staging transfer audit.
- Existing public `main/site` contains **113 species lesson JSON files and 35 hosted photos across 23 species**. Approved gallery photos are exactly attributed individually and reference their archived original Git blob.
- The source-photo release report records **176 image references held** from the public gallery because their individual photo provenance, license, permission, or original location is insufficiently verified. These records do not mean the source transfer failed.
- The repo is **PUBLIC**, including staged Git history and historic photo holds. A rights-filtered Pages build does **not** make held photo bytes in public Git history private. Do not add more restricted/unverified media or treat archival preservation as publication clearance.
- GitHub Pages successfully deployed the current photo-backed main build on October 29, 2026 (run [40910176003](https://github.com/Crking92/Hays-Botany-Monocots-Aquatics/actions/runs/40910176003)).
- Obsolete text-only workflow failures are protective: that script intentionally rejects overwriting a photo-backed learner. Do **not** bypass/re-run the obsolete text-only publishing workflow.

[Original source transfer manifest](https://github.com/Crking92/Hays-Botany-Monocots-Aquatics/blob/staging/original-source-transfer/migration/original-source-transfer-manifest.json) · [Existing public gallery summary](site/photo-source-migration-report.json) · [Migration closeout checkpoint](migration/MONOCOTS_AQUATICS_TRANSFER_QA_20261030.md)

## Website checks and next scope

`python3 scripts/verify_existing_site.py` verifies every existing public species lesson, photo link, per-image source credit and byte-exact source-blob hash. The separate [GitHub Action](.github/workflows/verify-existing-site-gallery.yml) also checks published Pages bytes when it runs.

Keep the original hub read-only, do not restart legacy automations, and do not gather new imagery/species/anatomy for this migration phase. New rights decisions, botanical improvements and additional photo publishing belong to later enrichment work. Repository visibility, raw-source history, publication rights, and hub cutover are separate decisions.
