#!/usr/bin/env python3
"""Validate total existing Poaceae source migration: public cleared + private held.

No photo sourcing, no rights reinterpretation, no Pages and no modifications
to canonical Hays-County-Botany or Poaceae main.
"""
import hashlib,json,subprocess,sys
from collections import Counter
from pathlib import Path
PRIVATE=Path(sys.argv[1]).resolve()
PUBLIC=Path(sys.argv[2]).resolve()
SOURCE=Path(sys.argv[3]).resolve()
priv=json.loads((PRIVATE/"migration/poaceae-held-photo-private-preservation-manifest.json").read_text())
files=json.loads((PUBLIC/"migration/poaceae-source-manifest-20261028.json").read_text())
ledger=json.loads((PUBLIC/"migration/source-file-ledger.json").read_text())
status=json.loads((PUBLIC/"migration/poaceae-transfer-status.json").read_text())
assert len(ledger)==len(files["files"])==1402
assert files["snapshot_commit"]==status["source_commit"]==priv["summary"]["original_source_snapshot"]
assert len(priv["images"])==58
assert priv["summary"]["held_source_photo_files_archived_privately"]==58
by_file={x["path"]:x for x in files["files"]}
by_ledger={x["path"]:x for x in ledger}
assert by_file.keys()==by_ledger.keys()
def sha(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
# git ls-tree verifies committed file identity by blob SHA without rewriting or
# downloading any source photo. The SHA matches the original pinned source blob.
tree=subprocess.check_output(["git","-C",str(PUBLIC),"ls-tree","-r","HEAD","content/taxa/Poaceae"],text=True)
public_git={}
for line in tree.splitlines():
 head,path=line.split("\t",1)
 mode,kind,blob=head.split()
 if kind=="blob":public_git[path]=blob
copied=[x for x in ledger if x["disposition"]!="IMAGE_HELD_IN_ORIGINAL_SOURCE_ONLY"]
held=[x for x in ledger if x["disposition"]=="IMAGE_HELD_IN_ORIGINAL_SOURCE_ONLY"]
assert len(copied)+len(held)==1402
assert len(copied)>=1346 and len(held)<=56
assert dict(Counter(x["disposition"] for x in ledger))==status["destination_file_counts"]
for x in copied:
 path=x["path"]
 assert public_git.get(path)==x["git_blob_sha"]==by_file[path]["git_blob_sha"],f"Public Poaceae source missing/changed: {path}"
for x in held:
 assert x["path"] not in public_git,"Rights-held photo accidentally committed to public Poaceae: "+x["path"]
private_by_path={x["source_path"]:x for x in priv["images"]}
assert len(private_by_path)==58
# Two originals since recovered in public Poaceae must remain safely preserved in
# private history; that creates a deliberate duplicate, not another hold.
for x in priv["images"]:
 p=PRIVATE/x["private_archived_path"]
 assert p.is_file()
 raw=p.read_bytes()
 assert len(raw)==x["bytes"]
 assert sha(raw)==x["git_blob_sha"]==by_file[x["source_path"]]["git_blob_sha"]
for x in held:
 assert x["path"] in private_by_path,"Held Poaceae original neither public nor private: "+x["path"]
overlap=sorted(set(public_git)&set(private_by_path))
assert len(overlap)==len(private_by_path)-len(held),len(overlap)
# Compare newest source tree against 2026-10-28 pinned original tree: no new
# grass files hidden in the active canonical hub.
latest_source_tree=subprocess.check_output(
 ["git","-C",str(SOURCE),"rev-parse","HEAD:content/taxa/Poaceae"],text=True).strip()
pinned_tree="e50d8ed26158d652d9c03fa67f4f47055af79420"
assert latest_source_tree==pinned_tree,"Canonical grass source drifted: recensus!"
cnt=Counter(x["disposition"] for x in ledger)
out={
 "status":"ALL_POACEAE_ORIGINAL_SOURCE_FILES_PRESERVED_PUBLIC_OR_PRIVATE",
 "public_collection":"Crking92/Hays-Botany-Poaceae",
 "private_rights_hold_archive":"Crking92/Hays-Botany-Monocots-Aquatics/staging/original-source-transfer/migration/poaceae-rights-held-originals",
 "original_hub":"Crking92/Hays-County-Botany",
 "canonical_source_tree_matches_migration_snapshot":True,
 "canonical_source_poaceae_tree_sha":pinned_tree,
 "original_source_files":1402,
 "existing_original_data_records_in_public_repo":cnt["SOURCE_DATA_COPIED"],
 "existing_original_photos_in_public_repo":len(copied)-cnt["SOURCE_DATA_COPIED"],
 "total_original_source_files_in_public_repo":len(copied),
 "source_photo_originals_preserved_private_archive":len(private_by_path),
 "source_photo_originals_private_only_public_rights_held":len(held),
 "duplicated_originals_in_public_and_private_preservation":len(overlap),
 "original_source_files_missing_from_all_staging":0,
 "public_content_original_source_git_blobs_verified":len(copied),
 "private_original_photo_bytes_verified":len(priv["images"]),
 "original_source_file_list_unchanged":True,
 "new_photo_download_or_collection":False,
 "live_pages_published":False,
 "rights_gates_preserved":True,
 "photo_public_display_permission_claimed_for_held":False,
 "remaining_outstanding_task":"Human photo-by-photo rights/publication review for private-only originals; static site, glossary, quiz, and cross-family routing are separate tasks"
}
dest=PRIVATE/"migration/poaceae-all-originals-public-private-reconciliation.json"
dest.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
print("POACEAE_FULL_PUBLIC_PRIVATE_ORIGINAL_MIGRATION_PASS",json.dumps(out,sort_keys=True),flush=True)
