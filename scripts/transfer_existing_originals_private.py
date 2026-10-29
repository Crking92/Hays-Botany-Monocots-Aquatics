#!/usr/bin/env python3
"""Copy EXISTING family-group originals only; no new photos, public gallery or Pages.

Source files are byte-exact; photos/unclassified media are privately quarantined.
All files have source SHA, destination SHA and manifest. Commit in <=90 file batches.
"""
import hashlib, json, subprocess, sys
from pathlib import Path
from collections import Counter, defaultdict

TARGET=Path(sys.argv[1]).resolve()
SOURCE=Path(sys.argv[2]).resolve()
config=json.loads((TARGET/"config/collection.json").read_text())
indexpath=TARGET/"data/collection-index.json"
index=json.loads(indexpath.read_text())
families=config["family_assignments"]
assert config["publication"]["enabled"] is False
assert config["planning_status"]=="STAGING_ONLY_NOT_AUTHORITATIVE"
assert config["navigation_contract"]["published_site_url"] is None
assert config["canonical_repository_until_approved_handoff"]=="Crking92/Hays-County-Botany"
assert index["authority"]=="STAGING_ONLY" and not index["entries"]
assert len(families)==len(set(families)) and all(f.endswith("aceae") for f in families)
assert subprocess.check_output(["git","-C",str(TARGET),"branch","--show-current"],text=True).strip()=="staging/originals-transfer"
source_sha=subprocess.check_output(["git","-C",str(SOURCE),"rev-parse","HEAD"],text=True).strip()
def sha(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
safe_text={".json",".csv",".txt",".md",".yaml",".yml"}
records=[]; counter=Counter(); species=[]; family_counts=defaultdict(Counter)
media_root=TARGET/"migration/private-original-photo-holds"
for family in sorted(families):
 familydir=SOURCE/"content/taxa"/family
 if not familydir.is_dir():raise RuntimeError("Assigned source family missing: "+family)
 files=sorted(p for p in familydir.rglob("*") if p.is_file())
 if not files:raise RuntimeError("Assigned source family empty: "+family)
 for src in files:
  if src.is_symlink():raise RuntimeError("Refuse symlink: "+str(src))
  rel=src.relative_to(SOURCE)
  raw=src.read_bytes()
  if len(raw)>25*1024*1024:raise RuntimeError("Photo/file exceeds 25 MB transfer policy: "+str(rel))
  source_blob=sha(raw)
  if src.suffix.lower() in safe_text:
   dest=TARGET/rel
   kind="BYTE_EXACT_SCIENTIFIC_TEXT_AND_CREDIT"
   counter["text"]+=1
  else:
   local=rel.relative_to("content/taxa")
   dest=media_root/local
   kind="PRIVATE_SOURCE_MEDIA_HOLD_DO_NOT_SERVE"
   counter["source_media_held"]+=1
  dest.parent.mkdir(parents=True,exist_ok=True)
  if dest.exists():
   if dest.read_bytes()!=raw:raise RuntimeError("Destination differs from canonical source: "+str(dest))
  else:dest.write_bytes(raw)
  if sha(dest.read_bytes())!=source_blob:raise RuntimeError("Recheck failed: "+str(rel))
  family_counts[family]["files"]+=1
  family_counts[family]["source_media_held" if kind.startswith("PRIVATE_SOURCE") else "text"]+=1
  records.append({"source_path":rel.as_posix(),"private_destination":dest.relative_to(TARGET).as_posix(),
    "sha1_git_blob":source_blob,"size_bytes":len(raw),"family":family,"preservation_class":kind,
    "public_display_approved":False,"photo_license_review":("UNREVIEWED" if kind.startswith("PRIVATE_SOURCE") else None)})
  if src.name=="species.json" and src.parent.parent.name==src.parents[1].name:
   # species.json path: content/taxa/Family/Genus/slug/species.json
   scientific=json.loads(raw.decode("utf-8"))
   sid=src.parent.name
   if scientific.get("id")!=sid or scientific.get("family")!=family or scientific.get("genus")!=src.parents[1].name:
    raise RuntimeError("Species identity mismatch: "+str(rel))
   species.append({"id":sid,"scientific_name":scientific["scientific_name"],
    "common_name":scientific.get("common_name",""),"family":family,"genus":scientific["genus"],
    "path":rel.as_posix(),"photo_publication_status":"EXISTING_SOURCE_MEDIA_QUARANTINED_NOT_APPROVED"})
# Every source original was copied: no "links only" count as a physical file.
assert len({r["source_path"] for r in records})==len(records)
assert len({r["private_destination"] for r in records})==len(records)
ids={r["id"] for r in species}
assert len(ids)==len(species)
expected=config["installed_species_baseline"]
assert len(species)==expected,(len(species),expected)
assert len(records)>len(species)
index.update({"entries":sorted(species,key=lambda r:r["id"]),
 "source_repository":"Crking92/Hays-County-Botany","source_commit_sha":source_sha,
 "source_families_snapshot":dict((k,dict(v)) for k,v in sorted(family_counts.items())),
 "public_website_ready":False,
 "note":"SOURCE_PRESERVATION_ONLY. Original text copied byte-exact. Every original image/media file quarantined privately; none cleared for public website or learner."})
indexpath.write_text(json.dumps(index,indent=2,ensure_ascii=False)+"\n")
media_root.mkdir(parents=True,exist_ok=True)
(media_root/"DO_NOT_PUBLISH_README.txt").write_text(
 "EXISTING ORIGINAL PHOTO/MEDIA HOLD ARCHIVE — PRIVATE REPOSITORY ONLY.\n"
 "These source files are copied byte-exact for migration completeness, but are\n"
 "NOT approved for display, redistribution, public Pages, or public Git history.\n"
 "Individual photo rights and names are not reassessed in this migration pass.\n"
 "The original public Hays Botany hub remains canonical and unchanged.\n")
manif=TARGET/"migration/original-file-transfer-manifest.json"
summ=TARGET/"migration/original-file-transfer-summary.json"
summary={"status":"ALL_EXISTING_SOURCE_FILES_PRIVATE_STAGED_NOT_PUBLISHED",
 "collection":config["collection_id"],"repo":config["repository_full_name"],
 "source_repository":"Crking92/Hays-County-Botany","source_commit":source_sha,
 "families":len(families),"species_records":len(species),
 "files_total":len(records),"text_files_byte_exact":counter["text"],
 "original_media_files_byte_exact_quarantined":counter["source_media_held"],
 "all_original_bytes_preserved":True,"files_missing":0,
 "source_media_public_approval":False,"public_pages_deployed":False,
 "public_hub_unchanged":True,"source_authority_changed":False,
 "family_census":dict((k,dict(v)) for k,v in sorted(family_counts.items()))}
manif.parent.mkdir(parents=True,exist_ok=True)
manif.write_text(json.dumps({"summary":summary,"files":records},indent=2,ensure_ascii=False)+"\n")
summ.write_text(json.dumps(summary,indent=2,ensure_ascii=False)+"\n")
print("FAMILY_ORIGINALS_PRIVATE_TRANSFER",json.dumps(summary,sort_keys=True),flush=True)
# Commit up to 90 files per batch; no GitHub Pages or visibility actions.
destinations=[r["private_destination"] for r in records]+[
 "migration/private-original-photo-holds/DO_NOT_PUBLISH_README.txt",
 "data/collection-index.json",
 "migration/original-file-transfer-manifest.json",
 "migration/original-file-transfer-summary.json"]
assert len(set(destinations))==len(destinations)
subprocess.run(["git","-C",str(TARGET),"config","user.name","github-actions[bot]"],check=True)
subprocess.run(["git","-C",str(TARGET),"config","user.email","41898282+github-actions[bot]@users.noreply.github.com"],check=True)
for i in range(0,len(destinations),90):
 group=destinations[i:i+90]
 subprocess.run(["git","-C",str(TARGET),"add","--",*group],check=True)
 staged=subprocess.check_output(["git","-C",str(TARGET),"diff","--cached","--name-only","-z"]).split(b"\x00")
 assert len([x for x in staged if x])<=100
 subprocess.run(["git","-C",str(TARGET),"diff","--cached","--check"],check=True)
 if any(staged):
  subprocess.run(["git","-C",str(TARGET),"commit","-m",
    f"Preserve source collection originals private batch {i//90+1}: no rights or Pages change"],check=True)
assert not subprocess.check_output(["git","-C",str(TARGET),"status","--porcelain"]), "Unexpected uncommitted files"
