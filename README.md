# obsidian-to-docs-converter
A Python basic tool to convert an Obsidian vault to HTML documentation


### Instructions
1) Clone it directly in your vault.
2) For now you have to put all `.md` files (Obsidian notes) and images in the `/pages` directory.
2) `pip install -r requirements.txt` # Installs necessary Python packages (creating a virtual environment first is highly suggested)
3)  Run `python generate_site.py`

An `/output` will be generated with all the HTML converted files (notes are converted from `.md` to `.html`).
Obsidian links are pretty well converted, but sometimes you can get an error. It distinguishes file obsidian links (`![[file]]`) from non file ones.


### Limits:
Only copies notes. All notes must be in the same folder (doesn'work on folder structures)


### Next features (work in progress):
- Also copying images
- Recognizing and copying vault's entire folder structure
