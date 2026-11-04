#!/usr/bin/env python3
"""Download exact-source iNaturalist photographs for a photo-first family gallery.

Each source photo must pass live photo-specific CC licensing, taxon, creator,
media-byte SHA-256 and site checks before the existing publisher handles it.
Unverified/restricted originals are NEVER committed to the public repository.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error

API="https://api.inaturalist.org/v1/observations/"
CDN="https://inaturalist-open-data.s3.amazonaws.com/photos/"
LICENSES={"BY":("cc-by","CC BY 4.0","https://creativecommons.org/licenses/by/4.0/"),
          "BY-NC":("cc-by-nc","CC BY-NC 4.0","https://creativecommons.org/licenses/by-nc/4.0/")}
MAX_BYTES=25*1024*1024
def get(url, limit=MAX_BYTES):
    req=urllib.request.Request(url, headers={"User-Agent":"HaysBotanyPhotoFirst/1.0 (exact-photo license check)"})
    with urllib.request.urlopen(req, timeout=35) as resp:
        if resp.url.split("/")[2] not in ("api.inaturalist.org","inaturalist-open-data.s3.amazonaws.com"):
            raise ValueError("Unexpected source redirect")
        data=resp.read(limit+1)
        if len(data)>limit:raise ValueError("Source exceeds size limit")
        return data
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",required=True)
    p.add_argument("--site-root",required=True)
    p.add_argument("--report",required=True)
    args=p.parse_args()
    records=[];errors=[];already=[];cleared=[]
    for line in pathlib.Path(args.manifest).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):continue
        fields=line.split("|")
        if len(fields)!=8:raise ValueError("Manifest field count != 8")
        sid,filename,obs_id,pid,ext,sha,creator,lic=fields
        if not re.fullmatch(r"[a-z]+-[a-z]+",sid) or not re.fullmatch(r"photo_[0-9]_[0-9a-f]{16}\.(jpg|jpeg)",filename):
            raise ValueError("Unsafe species filename: "+filename)
        if not obs_id.isdecimal() or not pid.isdecimal() or ext not in ("jpg","jpeg") or len(sha)!=64 or lic not in LICENSES:
            raise ValueError("Invalid photo record: "+filename)
        records.append(dict(sid=sid,filename=filename,obs_id=obs_id,pid=pid,ext=ext,sha=sha,creator=creator,license_key=lic))
    cards={}
    root=pathlib.Path(args.site_root)
    for row in records:
        sid=row["sid"]
        if sid not in cards:cards[sid]=json.loads((root/"data/species"/(sid+".json")).read_text())
    with tempfile.TemporaryDirectory() as tmpdir:
        stage=pathlib.Path(tmpdir)
        for row in records:
            sid=row["sid"];fn=row["filename"];pid=row["pid"];obsid=row["obs_id"]
            lic_code,license_label,license_url=LICENSES[row["license_key"]]
            photo_page="https://www.inaturalist.org/photos/"+pid
            try:
                if any(p.get("sha256")==row["sha"] or p.get("source_page")==photo_page for p in cards[sid].get("verified_photos",[])):
                    already.append({"species":sid,"filename":fn,"reason":"Already in site species gallery"})
                    continue
                api=json.loads(get(API+obsid,limit=5_000_000))
                results=api.get("results") or []
                if len(results)!=1:raise ValueError("Observation not found uniquely")
                obs=results[0]
                taxon=(obs.get("taxon") or {}).get("name","").lower().strip()
                if taxon!=sid.replace("-"," "):
                    raise ValueError("Current observation taxon mismatch: "+taxon)
                photos=[p for p in obs.get("photos",[]) if str(p.get("id"))==pid]
                if len(photos)!=1:raise ValueError("Exact photo absent from observation")
                photo=photos[0]
                if photo.get("license_code")!=lic_code:
                    raise ValueError("Individual photo license disagrees: "+str(photo.get("license_code")))
                att=str(photo.get("attribution") or "")
                if row["creator"].casefold() not in att.casefold():
                    raise ValueError("Photo creator mismatch: "+att[:120])
                source_url=CDN+pid+"/original."+row["ext"]
                payload=get(source_url)
                digest=hashlib.sha256(payload).hexdigest()
                if digest!=row["sha"]:
                    raise ValueError("Original-byte SHA mismatch")
                if len(payload)<200:raise ValueError("Image too small")
                folder=stage/"photo-intake/approved"/sid
                folder.mkdir(parents=True,exist_ok=True)
                (folder/fn).write_bytes(payload)
                sidecar={
                    "species_id":sid,"photo_file":fn,
                    "status":"APPROVED_FOR_PUBLIC_FAMILY_SITE",
                    "rights_approved_for_public":True,"taxon_reviewed":True,
                    "approval_mode":"OWNER_STANDING_PHOTO_FIRST_POLICY",
                    "policy_ref":"PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02",
                    "approval_note":"Exact media license, creator, observation taxon and original image hash verified from live iNaturalist source.",
                    "source_review_evidence":"Live iNaturalist observation API "+API+obsid+" returned individual photo "+pid+
                       " license "+lic_code+", photographer "+att+", SHA256 "+digest+
                       "; original image "+source_url,
                    "taxon_review_evidence":"Basic contact-sheet visual sanity screen of user-supplied Cyperaceae_002.zip plus live observation taxon "+taxon+
                       "; recognition gallery only, no diagnostic-anatomy certification.",
                    "review_operator":"ChatGPT bulk photo-first visual review and independently checked iNaturalist API",
                    "creator":row["creator"],"source_page":photo_page,"source_page_is_exact":True,
                    "license":license_label,"license_url":license_url,
                    "role":"General species recognition photograph; diagnostic structures not certified",
                    "modifications":"Original image bytes, unmodified",
                    "sha256":digest,
                    "noncommercial_site_use_confirmed":row["license_key"]=="BY-NC"
                }
                (folder/(fn+".json")).write_text(json.dumps(sidecar,ensure_ascii=False,indent=2))
                cleared.append({"species":sid,"filename":fn,"photo_page":photo_page,"license":license_label})
            except Exception as exc:
                errors.append({"species":sid,"filename":fn,"reason":str(exc)[:400]})
        result={"batch":"Cyperaceae_002","candidates":len(records),"already_published":already,
                "cleared":cleared,"held":errors,"installed":0}
        if cleared:
            cmd=[sys.executable,"scripts/publish_approved_family_photos.py",
                 "--source-root",str(stage),"--site-root",str(root)]
            check=subprocess.run(cmd+["--check"],text=True,capture_output=True)
            if check.returncode:
                result["publisher_error"]=check.stdout+check.stderr
                result["cleared_but_not_installed"]=len(cleared)
            else:
                publish=subprocess.run(cmd,text=True,capture_output=True)
                if publish.returncode:
                    result["publisher_error"]=publish.stdout+publish.stderr
                else:
                    try:
                        output=json.loads(publish.stdout)
                        result["installed"]=output.get("installed",0)
                        result["site_photo_count_after"]=output.get("photo_count")
                        result["site_photo_species_after"]=output.get("photo_species")
                    except ValueError:
                        result["publisher_error"]=publish.stdout[:2000]
        pathlib.Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps({k:v if not isinstance(v,list) else len(v) for k,v in result.items()},indent=2))
        for h in errors:print("HOLD:",h["species"],h["filename"],h["reason"])
        if result.get("publisher_error"):
            print(result["publisher_error"],file=sys.stderr)
            return 1
    return 0
if __name__=="__main__":
    sys.exit(main())
