> **Current photo-first instructions (November 2, 2026):** See [the shared family policy](../workflow/PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02.md). Publish useful credited general views of already indexed species as soon as exact-image rights and a basic species sanity check are substantiated. No anatomy arrows or finished lessons are required. Every source image needs its matching metadata sidecar; copies in a ZIP or staging branch do not count until the family Pages gallery serves them. Keep restricted or unresolved photo bytes out of **every** branch of a public repository.

**Two accepted approval paths:** (1) an actual named photo reviewer with real documented evidence; or (2) the owner's documented standing photo-first policy with `approval_mode: OWNER_STANDING_PHOTO_FIRST_POLICY`, `policy_ref: PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02`, and truthful `review_operator`, `source_review_evidence`, `taxon_review_evidence` and `approval_note` values. Both still require `rights_approved_for_public: true`, `taxon_reviewed: true`, verified creator, exact-photo HTTPS source, license/version/URL, image bytes and credible source proof. **Never fabricate reviewer evidence, IDs or approvals.**

**Licenses:** verifiable CC0, CC BY and CC BY-SA photos are normally allowed. CC BY-NC 4.0 / CC BY-NC-SA 4.0 are conditionally permitted **only** with an actually noncommercial educational family site, an individually checked license, and `noncommercial_site_use_confirmed: true` for that photo. Preserve explicit NC reuse limits, attribution and adaptation/ShareAlike requirements. Hold ND, ARR and uncertain rights. If the publisher refuses otherwise eligible media, fix its implementation or record the hold; don't bypass guards. New species still need a reviewed index/card installation before automatic general-gallery intake.

# Approved image upload — Monocots & Aquatics

**This is a PUBLIC repository.** Do not upload photographs here unless each original is cleared for public source access and reuse. Keep unclear-rights photos outside the public repository.

Upload both `photo-intake/approved/aquarius-cordifolius/new-approved-photo.jpg` and `photo-intake/approved/aquarius-cordifolius/new-approved-photo.jpg.json` to branch `staging/original-source-transfer`. Name both files for the SAME photograph. Each real file requires a manual license and ID review.

Example sidecar structure (PLACEHOLDERS ONLY — not an actual approval):

```json
{
  "species_id": "aquarius-cordifolius",
  "photo_file": "new-approved-photo.jpg",
  "status": "APPROVED_FOR_PUBLIC_FAMILY_SITE",
  "rights_approved_for_public": true,
  "taxon_reviewed": true,
  "approved_by": "Name of actual reviewer",
  "approval_note": "Describe verified exact photo source, license and taxonomic evidence",
  "creator": "Name of the real photographer",
  "source_page": "https://www.example.org/exact-individual-photo-page",
  "source_page_is_exact": true,
  "license": "CC BY 4.0",
  "license_url": "https://creativecommons.org/licenses/by/4.0/",
  "role": "Only morphological structures clearly visible in the uploaded image",
  "modifications": "Exact original or detailed alterations"
}
```

Allowed licenses: exact-version CC0, CC BY, and CC BY-SA, plus conditional verified CC BY-NC / CC BY-NC-SA 4.0 with noncommercial-site and exact-photo confirmations. No ND, vague rights, false credits or unverified arrows. Source URL must be exact-photo HTTPS. Media limit 25 MB. If any approval field is missing or a photo lacks its matching sidecar, the automatic publish fails safely. New species need a separate reviewed installation first.
