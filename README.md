## Convert any Obsidian folder in a html /templates ready folder for docs or websites. 

Put all your vault files in the "/pages" folder and then run `python obsidian_to_docs.py`.

Converts an obsidian vault in an html files folder the `frontend_files` folder (contains three folders: `static`, `templates` and `extra_files`).

it is better to not use the extra_files folder's files in your app since they are of miscellaneous types, not used in normal app-web development.  

Always remove index.html from here before using these templates, if you already have
a custom index.html for your app-website! Otherwise it will be overwritten.

### Features:
- renders Latex (quite well)


### Limitations
- Only works with all files in a folder. Doesn't work with more complex structures (nested folders/subfolders).


### Based on obsidian links parsing and conversion

Internal links matching:
Obsidian supports the following internal link formats:
- Wikilink: [[Three laws of motion]]
- Markdown: [Three laws of motion](Three%20laws%20of%20motion.md)

External links matching:
- Custom links to online resources: ![resource alias](http://path/to/source/file)
- https://help.obsidian.md/Linking+notes+and+files/Internal+links
- Local external docs: ![[Python RegEx 101.pdf]]
- every link with "|some text" if existing" (the custom link alias)
