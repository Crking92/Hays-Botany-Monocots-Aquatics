#!/usr/bin/env python3
"""Publish only original Typhaceae media passing exact iNaturalist photo-specific checks."""
from __future__ import annotations
import hashlib, io, json, os, re, urllib.request, time
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
source=json.loads((ROOT/"photo-intake/remote-photo-manifests/typhaceae-2026-11-02.json").read_text())
if source["family"]!="Typhaceae" or len(source["photos"])!=8:
    raise SystemExit("Unexpected Typhaceae source manifest")
OUT=Path(os.environ["RUNNER_TEMP"])/"typhaceae-verified"
REPORT=Path(os.environ["RUNNER_TEMP"])/"typhaceae-original-source-review.json"
species={"typha-domingensis":"typha domingensis","typha-latifolia":"typha latifolia"}
def get(url,maxbytes=26_000_000):
    req=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyPhotoFirstEducationalSourceReview/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=35) as response:
                b=response.read(maxbytes+1)
            if len(b)>maxbytes:raise ValueError("Remote file exceeds intake size limit")
            return b
        except Exception:
            if attempt==2:raise
            time.sleep(attempt+1)
review=[];seen=set()
for p in source["photos"]:
    sid=p["species_id"];photoid=int(p["photo_id"]);obsid=int(p["observation_id"])
    status={"species_id":sid,"photo_id":photoid,"observation_id":obsid}
    try:
        if sid not in species or photoid in seen:raise ValueError("Unrecognized species or duplicate photo")
        seen.add(photoid)
        if not re.fullmatch("[0-9a-f]{64}",p["sha256"]):raise ValueError("Invalid SHA256")
        if not p["image_url"].startswith(f"https://inaturalist-open-data.s3.amazonaws.com/photos/{photoid}/original."):
            raise ValueError("Photo ID and image source URL disagree")
        obs_data=json.loads(get(f"https://api.inaturalist.org/v1/observations/{obsid}",5_000_000))
        obs=next((x for x in obs_data.get("results",[]) if int(x.get("id",0))==obsid),None)
        if obs is None:raise ValueError("Observation not found in live source")
        taxon=(obs.get("taxon") or {}).get("name","").strip().lower()
        if taxon!=species[sid]:raise ValueError("Observation identification does not match photo folder: "+taxon)
        original=next((x for x in obs.get("photos",[]) if int(x.get("id",0))==photoid),None)
        if original is None:raise ValueError("Individual photo not included in cited observation")
        photo_license=str(original.get("license_code") or "").lower().replace("_","-")
        if photo_license!="cc-by-nc":raise ValueError("Photo-specific license not verified as CC BY-NC: "+photo_license)
        creator=str(original.get("attribution") or "").strip()
        if not creator or creator.lower() in {"some rights reserved","all rights reserved"}:
            creator=str(p.get("photographer") or "").strip()
        if not creator:raise ValueError("Photo photographer credit absent")
        payload=get(p["image_url"])
        if hashlib.sha256(payload).hexdigest()!=p["sha256"]:
            raise ValueError("Live exact image bytes fail original ZIP SHA256 check")
        with Image.open(io.BytesIO(payload)) as im:
            if im.format!="JPEG" or im.width*im.height>80_000_000:raise ValueError("Wrong image format or pixel count")
            im.verify()
        ext=p["image_url"].split(".")[-1].lower()
        name=f"inat-{photoid}.{ext}"
        dest=OUT/"photo-intake/approved"/sid
        dest.mkdir(parents=True,exist_ok=True)
        (dest/name).write_bytes(payload)
        sidecar={
          "species_id":sid,"photo_file":name,
          "status":"APPROVED_FOR_PUBLIC_FAMILY_SITE","rights_approved_for_public":True,"taxon_reviewed":True,
          "approval_mode":"OWNER_STANDING_PHOTO_FIRST_POLICY","policy_ref":"PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02",
          "review_operator":"Hays Botany exact iNaturalist photo source and original ZIP integrity check",
          "source_review_evidence":f"Live iNaturalist observation {obsid} explicitly contains photo {photoid} under CC BY-NC with its real creator, and the original photo bytes match the user's ZIP SHA256 {p['sha256']}.",
          "taxon_review_evidence":f"Source observation taxon {taxon} matches assigned species; uploaded contact sheet reviewed for general cattail habit. Detailed anatomical determination and county nativity separately deferred.",
          "approval_note":"Standing owner authorization for general cattail photos, with independent exact-media rights and original-image integrity checks.",
          "creator":creator,
          "source_page":f"https://www.inaturalist.org/photos/{photoid}",
          "source_page_is_exact":True,
          "license":"CC BY-NC 4.0",
          "license_url":"https://creativecommons.org/licenses/by-nc/4.0/",
          "noncommercial_site_use_confirmed":True,
          "role":p["caption"]+" (general recognition, not anatomical diagnostic certification)",
          "modifications":"Unmodified original source photo; no edits",
          "sha256":p["sha256"]
        }
        (dest/(name+".json")).write_text(json.dumps(sidecar,indent=2)+"\n")
        status["status"]="VERIFIED_FOR_GALLERY_PUBLICATION"
    except Exception as exc:
        status.update(status="HOLD_SOURCE_OR_SPECIES",reason=str(exc)[:500])
    print(json.dumps(status),flush=True)
    review.append(status)
REPORT.write_text(json.dumps({"batch":source["batch"],"photo_checks":review,"held_herbarium":source["held_herbarium"]},indent=2)+"\n")
print(json.dumps({"verified":sum(x["status"]=="VERIFIED_FOR_GALLERY_PUBLICATION" for x in review),"held":sum(x["status"]!="VERIFIED_FOR_GALLERY_PUBLICATION" for x in review)}))
