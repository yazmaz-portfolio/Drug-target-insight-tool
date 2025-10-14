#!/usr/bin/env python3
# drugtarget.py  -- simple UniProt fetch & summary
import argparse, json, requests, sys
from pathlib import Path

UNI_BASE = "https://rest.uniprot.org/uniprotkb"

def fetch_by_id(uid):
    url = f"{UNI_BASE}/{uid}.json"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()

def search_by_gene(gene, organism="Homo sapiens", size=1):
    query = f"gene_exact:{gene} AND organism_name:{organism}"
    url = f"https://rest.uniprot.org/uniprotkb/search?query={requests.utils.quote(query)}&format=json&size={size}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    if not results:
        return None
    acc = results[0]["primaryAccession"]
    return fetch_by_id(acc)

def parse_entry(entry):
    out = {}
    out["primaryAccession"] = entry.get("primaryAccession")
    out["proteinName"] = entry.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value")
    out["geneNames"] = [g.get("geneName", {}).get("value") for g in entry.get("genes", []) if "geneName" in g]
    out["organism"] = entry.get("organism", {}).get("scientificName")
    out["length"] = entry.get("sequence", {}).get("length")
    out["sequence_mw"] = entry.get("sequence", {}).get("mass")
    out["keywords"] = [k.get("value") for k in entry.get("keywords", [])]
    subs = []
    for cc in entry.get("comments", []):
        if cc.get("commentType") == "SUBCELLULAR_LOCATION":
            for loc in cc.get("subcellularLocations", []):
                vals = []
                if "location" in loc and loc["location"]:
                    vals.append(loc["location"].get("value"))
                if "topology" in loc and loc["topology"]:
                    vals.append(loc["topology"].get("value"))
                subs.append(" ; ".join([v for v in vals if v]))
    out["subcellular_locations"] = subs
    domains = []
    for feat in entry.get("features", []):
        if feat.get("category") in ("DOMAIN", "REGION", "TOPOLOGICAL_DOMAIN"):
            name = feat.get("description") or feat.get("type")
            loc = feat.get("location", {})
            begin = loc.get("start", {}).get("value")
            end = loc.get("end", {}).get("value")
            domains.append({"name": name, "start": begin, "end": end})
    out["domains"] = domains
    cross_refs = entry.get("uniProtKBCrossReferences", [])
    pdbs = [cr for cr in cross_refs if cr.get("database") == "PDB"]
    out["pdb_count"] = len(pdbs)
    out["pdb_entries"] = [p.get("id") for p in pdbs]
    functions = []
    for cc in entry.get("comments", []):
        if cc.get("commentType") == "FUNCTION":
            texts = []
            for t in cc.get("texts", []):
                texts.append(t.get("value"))
            functions.append(" ".join(texts))
    out["functions"] = functions
    return out

def pretty_print(res):
    print("\n=== UniProt Summary ===")
    print(f"Accession: {res.get('primaryAccession')}")
    print(f"Protein:   {res.get('proteinName')}")
    print(f"Gene(s):   {', '.join([g for g in res.get('geneNames') if g])}")
    print(f"Organism:  {res.get('organism')}")
    print(f"Length:    {res.get('length')} aa, Mass: {res.get('sequence_mw')} Da")
    print(f"PDB entries: {res.get('pdb_count')}, IDs: {', '.join(res.get('pdb_entries')[:5])}")
    print(f"Subcellular locations: {', '.join(res.get('subcellular_locations')[:3]) or 'N/A'}")
    print("Domains (first 5):")
    for d in res.get("domains", [])[:5]:
        print(f" - {d.get('name')} ({d.get('start')}-{d.get('end')})")
    if res.get("functions"):
        print("Function (short):")
        print(" ", res.get("functions")[0][:400])
    print("=======================\n")

def save_json(res, outpath):
    Path(outpath).write_text(json.dumps(res, indent=2))
    print(f"Saved JSON to {outpath}")

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--id", help="UniProt accession (e.g., P04637)")
    p.add_argument("--gene", help="Gene symbol (e.g., TP53)")
    p.add_argument("--organism", default="Homo sapiens", help="Organism name (default: Homo sapiens)")
    p.add_argument("--out", default="uniprot_result.json", help="Output JSON filename")
    args = p.parse_args()

    try:
        if args.id:
            entry = fetch_by_id(args.id)
        elif args.gene:
            entry = search_by_gene(args.gene, organism=args.organism)
            if not entry:
                print("No results found for gene + organism.")
                sys.exit(1)
        else:
            print("Specify --id or --gene")
            sys.exit(1)

        parsed = parse_entry(entry)
        pretty_print(parsed)
        save_json(parsed, args.out)
    except requests.HTTPError as e:
        print("HTTP error:", e)
    except Exception as ex:
        print("Error:", ex)

if __name__ == "__main__":
    main()

