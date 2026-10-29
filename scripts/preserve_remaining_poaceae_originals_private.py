#!/usr/bin/env python3
"""Private, byte-exact archive of public Poaceae migration holds.

This is file transfer ONLY, NOT a photo use/republication approval.
Poaceae public source remains separate from this private monocot asset holding
archive; the original Hays Botany source is never modified. No new images.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
from collections import Counter
SRC=Path(sys.argv[1]).resolve()
TARGET=Path(sys.argv[2]).resolve()
PUBLIC=Path(sys.argv[3]).resolve()
LEDGER=TARGET/"migration"
manifest=json.loads((PUBLIC/"migration/poaceae-source-manifest-20261028.json").read_text())
records=json.loads((PUBLIC/"migration/source-file-ledger.json").read_text())
reviews=json.loads((PUBLIC/"migration/image-record-review-ledger.json").read_text())
config=json.loads((TARGET/"config/collection.json").read_text())
assert config["publication"]["enabled"] is False
assert "Poaceae" not in config["family_assignments"],"This is a segregation archive, NOT species ownership"
assert json.loads((TARGET/"data/collection-index.json").read_text())["authority"]=="STAGING_ONLY"
assert subprocess.check_output(["git","-C",str(TARGET),"branch","--show-current"],text=True).strip()=="staging/original-source-transfer"
assert manifest["snapshot_commit"]==subprocess.check_output(["git","-C",str(SRC),"rev-parse","HEAD"],text=True).strip()
assert manifest["file_count"]==len(manifest["files"])==len(records)==1402
by_file={x["path"]:x for x in manifest["files"]}
review_by={x["resolved_path"]:x for x in reviews if x.get("resolved_path")}
assert len(by_file)==1402
held=[x for x in records if x["disposition"]=="IMAGE_HELD_IN_ORIGINAL_SOURCE_ONLY"]
assert 0<len(held)<=58,("Unexpected held count",len(held))
expected_remaining=len(held)
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
base=LEDGER/"poaceae-rights-held-originals"
entries=[]
for item in held:
 path=item["path"]
 assert path in by_file and path.startswith("content/taxa/Poaceae/") and "/images/" in path or path.startswith("content/taxa/Poaceae/") and Path(path).suffix.lower() in (".jpg",".jpeg",".png",".webp")
 original=(SRC/path).read_bytes()
 assert len(original)==by_file[path]["bytes"]
 assert blob(original)==by_file[path]["git_blob_sha"]==item["git_blob_sha"]
 assert len(original)<=25*1024*1024
 dest=base/path
 dest.parent.mkdir(parents=True,exist_ok=True)
 if dest.exists():assert dest.read_bytes()==original,("Existing private source differs",path)
 else:dest.write_bytes(original)
 assert blob(dest.read_bytes())==item["git_blob_sha"]
 credit=review_by.get(path)
 entries.append({"source_path":path,"private_archived_path":dest.relative_to(TARGET).as_posix(),
   "git_blob_sha":item["git_blob_sha"],"bytes":len(original),
   "source_rights_decision":item.get("hold_reasons",[]),
   "source_credit_record":credit,
   "nonpublic_quarantine_only":True,"public_reuse_verified":False})
assert len(entries)==expected_remaining
expected_files={x["private_archived_path"] for x in entries}
actual={p.relative_to(TARGET).as_posix() for p in base.rglob("*")
  if p.is_file() and p.suffix.lower() in (".jpg",".jpeg",".png",".webp")}
assert expected_files==actual,("Unexpected archival images",expected_files^actual)
report={"status":"POACEAE_ALL_CURRENT_HELD_ORIGINALS_EXACTLY_ARCHIVED_PRIVATE_NOT_PUBLIC",
 "source_repository":"Crking92/Hays-County-Botany",
 "public_poaceae_repository":"Crking92/Hays-Botany-Poaceae",
 "private_archive_repository":"Crking92/Hays-Botany-Monocots-Aquatics",
 "original_source_snapshot":manifest["snapshot_commit"],
 "held_source_photo_files_archived_privately":len(entries),
 "original_github_blob_hashes_matching":len(entries),
 "photo_bytes_preserved":sum(x["bytes"] for x in entries),
 "original_poaceae_source_files_total":1402,
 "source_record_dispositions_untouched":True,
 "public_poaceae_repository_modified":False,
 "original_hub_modified":False,
 "site_display_approved":False,
 "public_pages_deployed":False,
 "author_license_changes":False,
 "private_storage_location":"migration/poaceae-rights-held-originals/",
 "note":"A private asset preservation archive, not a change to family classification, owner permissions, source licenses, or live Poaceae routes."}
(LEDGER/"poaceae-held-photo-private-preservation-manifest.json").write_text(json.dumps({"summary":report,"images":entries},indent=2,ensure_ascii=False)+"\n")
(LEDGER/"poaceae-held-photo-private-preservation-summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
(base/"DO_NOT_PUBLISH.txt").write_text(
 "EXACT POACEAE ORIGINAL PHOTO QUARANTINE. PRIVATE ONLY. NOT PUBLIC-DISPLAY PERMISSION.\n"
 "This holding archive preserves the final source files that were not included in\n"
 "the public Poaceae repository, under their original credits and rights restrictions.\n"
 "No botanical family ownership is transferred to Monocots-Aquatics; the folder is\n"
 "strictly private migration storage. See sibling Poaceae hold manifest for SHAs.\n")
assert all(x["nonpublic_quarantine_only"] for x in entries)
print("POACEAE_PRIVATE_REMAINING_ORIGINALS_PRESERVED",json.dumps(report,sort_keys=True),flush=True)
