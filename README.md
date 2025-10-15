# Drug Target Insight Tool 🧬

A simple Python CLI tool to fetch and summarize protein information from the UniProt database.

### Features
- Fetch protein data by UniProt ID or gene name
- Display details: name, gene, length, molecular weight, domains, subcellular location, function
- Save results as JSON for further analysis

### Usage
```bash
python drugtarget.py --id P04637
# or
python drugtarget.py --gene TP53 --organism "Homo sapiens"
