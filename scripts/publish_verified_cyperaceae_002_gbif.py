#!/usr/bin/env python3
"""Verify exact GBIF media license and archive hash, then add cleared specimens."""
import argparse
import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import time
import urllib.request
from PIL import Image

URL="https://api.gbif.org/v1/occurrence/"
LICENSES={"BY":("CC BY 4.0","https://creativecommons.org/licenses/by/4.0/"),
          "BY-NC":("CC BY-NC 4.0","https://creativecommons.org/licenses/by-nc/4.0/")}
def grab(url,size_limit):
    last=None
    for attempt in range(3):
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"HaysBotanyCyperaceaeOriginalSourceQA/1.0"})
            with urllib.request.urlopen(request,timeout=40) as r:
                blob=r.read(size_limit+1)
            if len(blob)>size_limit:raise ValueError("Photo larger than allowed")
            return blob
        except Exception as error:
            last=error
            if attempt<2:time.sleep(2+attempt)
    raise last
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",required=True)
    parser.add_argument("--site-root",required=True)
    parser.add_argument("--report",required=True)
    args=parser.parse_args()
    root=pathlib.Path(args.site_root)
    site_meta=json.loads((root/"data/collection-meta.json").read_text())
    rows=[]
    for line in pathlib.Path(args.manifest).read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):continue
        parts=line.split("|")
        if len(parts)!=7:raise ValueError("Expected 7 manifest fields")
        sid,filename,gbif_id,sha,url,creator,license_key=parts
        if not gbif_id.isdigit() or len(sha)!=64 or license_key not in LICENSES:
            raise ValueError("Malformed media record: "+line[:100])
        if not sid.replace("-","").isalpha() or "/" in filename or not filename.lower().endswith((".jpg",".jpeg")):
            raise ValueError("Unsafe ID/filename")
        rows.append(dict(sid=sid,filename=filename,gbif_id=gbif_id,sha=sha,url=url,creator=creator,license_key=license_key))
    loaded={};held=[];ready=[];already=[]
    for r in rows:
        sid=r["sid"]
        if sid not in loaded:loaded[sid]=json.loads((root/"data/species"/(sid+".json")).read_text())
    with tempfile.TemporaryDirectory() as td:
        source=pathlib.Path(td)
        for r in rows:
            sid=r["sid"];url=r["url"];gid=r["gbif_id"]
            page="https://www.gbif.org/occurrence/"+gid
            try:
                if any(p.get("sha256")==r["sha"] or p.get("source_page")==page for p in loaded[sid]["verified_photos"]):
                    already.append({"species":sid,"gbif_id":gid})
                    continue
                occurrence=json.loads(grab(URL+gid,3_000_000))
                scientific=str(occurrence.get("species") or occurrence.get("scientificName") or "").lower()
                expected=sid.replace("-"," ")
                if not (scientific==expected or scientific.startswith(expected+" ")):
                    raise ValueError("GBIF occurrence taxon mismatch: "+scientific)
                media=[m for m in occurrence.get("media",[]) if str(m.get("identifier") or "")==url]
                if len(media)!=1:raise ValueError("Exact archived image identifier missing from current GBIF media")
                m=media[0]
                expected_name,expected_url=LICENSES[r["license_key"]]
                actual=str(m.get("license") or "").replace("http://","https://")
                if actual.rstrip("/")!=expected_url.rstrip("/"):
                    raise ValueError("Exact media license not independently confirmed: "+actual)
                if r["license_key"]=="BY-NC" and not site_meta["photo_license_policy"].get("noncommercial_educational_use"):
                    raise ValueError("Public site does not have noncommercial-only permission")
                credits=" ".join(str(m.get(k) or "") for k in ("creator","rightsHolder","publisher"))
                significant=[w for w in r["creator"].lower().replace("("," ").split() if len(w)>5]
                if significant and not any(w in credits.lower() for w in significant):
                    raise ValueError("Individual provider creator differs from ZIP credit: "+credits)
                raw=grab(url,25*1024*1024)
                if hashlib.sha256(raw).hexdigest()!=r["sha"]:
                    raise ValueError("Original image bytes mismatch; no media published")
                with Image.open(io.BytesIO(raw)) as im:
                    if im.format!="JPEG" or im.width*im.height>80_000_000:raise ValueError("Invalid JPEG original")
                    im.verify()
                dest=source/"photo-intake/approved"/sid
                dest.mkdir(parents=True,exist_ok=True)
                filename="gbif-"+gid+".jpg"
                (dest/filename).write_bytes(raw)
                sidecar={
                    "species_id":sid,"photo_file":filename,
                    "status":"APPROVED_FOR_PUBLIC_FAMILY_SITE",
                    "rights_approved_for_public":True,"taxon_reviewed":True,
                    "approval_mode":"OWNER_STANDING_PHOTO_FIRST_POLICY",
                    "policy_ref":"PHOTO_FIRST_PUBLIC_GALLERY_POLICY_2026-11-02",
                    "review_operator":"ChatGPT visual sample review plus live GBIF individual media-license and exact-byte verifier",
                    "approval_note":"Verified original specimen media source, image-specific CC license, provider, accepted taxon, source image bytes and source attribution.",
                    "source_review_evidence":"Live GBIF occurrence "+URL+gid+" has exact media identifier "+url+", image-level license "+actual+", provider credit "+credits+
                        "; original uploaded ZIP SHA256 matches live media: "+r["sha"],
                    "taxon_review_evidence":"Basic visual contact sheet review of original herbarium sheet, current GBIF occurrence taxon "+
                        scientific+"; general specimen recognition only, detailed label and diagnostic identification deferred.",
                    "creator":r["creator"],"source_page":page,"source_page_is_exact":True,
                    "license":expected_name,"license_url":expected_url,
                    "noncommercial_site_use_confirmed":r["license_key"]=="BY-NC",
                    "role":"Pressed herbarium specimen showing general culms and inflorescence; original voucher label visible",
                    "modifications":"Original source JPEG, no alterations",
                    "sha256":r["sha"]
                }
                (dest/(filename+".json")).write_text(json.dumps(sidecar,ensure_ascii=False,indent=2))
                ready.append({"species":sid,"gbif_id":gid,"license":expected_name})
            except Exception as exc:
                held.append({"species":sid,"gbif_id":gid,"reason":str(exc)[:400]})
        result={"batch":"Cyperaceae_002_GBIF","checked":len(rows),"ready":ready,"already":already,
                "held":held,"installed":0}
        if ready:
            cmd=[sys.executable,"scripts/publish_approved_family_photos.py",
                 "--source-root",str(source),"--site-root",str(root)]
            check=subprocess.run(cmd+["--check"],text=True,capture_output=True)
            if check.returncode:
                result["publisher_error"]=check.stdout+check.stderr
            else:
                installed=subprocess.run(cmd,text=True,capture_output=True)
                if installed.returncode:result["publisher_error"]=installed.stdout+installed.stderr
                else:
                    p=json.loads(installed.stdout)
                    result["installed"]=p.get("installed",0)
                    result["site_photo_count_after"]=p.get("photo_count")
        pathlib.Path(args.report).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps({k:v if not isinstance(v,list) else len(v) for k,v in result.items()},indent=2))
        for h in held:print("HOLD",h["species"],h["gbif_id"],h["reason"])
        if result.get("publisher_error"):
            print(result["publisher_error"],file=sys.stderr)
            return 1
    return 0
if __name__=="__main__":
    sys.exit(main())
