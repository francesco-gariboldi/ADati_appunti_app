import os
import sys
import re
import shutil
from markdown_it import MarkdownIt
from jinja2 import Environment, FileSystemLoader

# Set the base directory based on the executable's path (PyInstaller's _MEIPASS when frozen)
if getattr(sys, 'frozen', False):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Main paths
pages_dir = os.path.join(base_dir, 'pages')
templates_dir = os.path.join(base_dir, 'templates')
css_filename = 'style.css'

# Define output directory on the Desktop
output_dir = os.path.join(os.path.expanduser("~"), 'Desktop', 'ADati_appunti')
os.makedirs(output_dir, exist_ok=True)
print(f"Output directory created at: {output_dir}")

# Load the template with Jinja2
env = Environment(loader=FileSystemLoader(templates_dir))
template = env.get_template('base.html')

# Ensure that the output folder exists
try:
    os.makedirs(output_dir, exist_ok=True)
except Exception as e:
    print(f"Error creating directory: {e}")

# Configure markdown-it-py for Markdown parsing
md = MarkdownIt()

# Function to extract Obsidian internal links and images
def get_md_matches(content):
    # Regex pattern for Obsidian links and embeds
    md_reg = r'(!)?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'
    matches = re.finditer(md_reg, content)
    
    output_array = [
        {
            'link': match.group(2).strip(),       # The link target (first part before |)
            'alt': match.group(3).strip() if match.group(3) else match.group(2).strip(),  # Alt text or link if no alt
            'isEmbed': bool(match.group(1)),      # True if it's an embed (has "!")
            'original': match.group(0)            # Original matched text
        }
        for match in matches
    ]
    
    return output_array

# Function to convert Obsidian internal links to HTML links
def convert_obsidian_links(text):
    matches = get_md_matches(text)
    
    for match in matches:
        if match['isEmbed']:
            # If it's an embedded image
            replacement = f'<img src="{match["link"]}" alt="{match["alt"]}">'
        else:
            # If it's a regular internal link
            replacement = f'<a href="{match["link"]}.html">{match["alt"] or match["link"]}</a>'
        
        # Replace original Obsidian syntax with the generated HTML
        text = text.replace(match['original'], replacement)
    
    return text

# Function to convert Obsidian callouts to HTML
def convert_callouts(text):
    # Define a regex to match callouts in various forms like `>[!]`, `> [!]`, or `>`.
    callout_pattern = r'^\s*>\s*(\[\s*(!|\?|i|x)\s*\])?\s*(.*)$'
    callout_classes = {
        '!': 'note',      # general note
        '?': 'question',  # question
        'i': 'info',      # info
        'x': 'warning'    # warning
    }

    def callout_replacer(match):
        # Determine if it's a specific callout type or a generic blockquote
        callout_type = match.group(2)
        content = match.group(3)
        
        # Assign a CSS class or default to 'note' for unspecified callout types
        callout_class = callout_classes.get(callout_type, 'note') if callout_type else 'blockquote'
        return f'<div class="callout {callout_class}"><p>{content}</p></div>'

    # Apply the callout pattern line by line
    lines = text.split('\n')
    for i, line in enumerate(lines):
        lines[i] = re.sub(callout_pattern, callout_replacer, line)
    return '\n'.join(lines)

# List of generated pages for the menu
pages = []

# Generate an HTML file for each Markdown file
for filename in os.listdir(pages_dir):
    if filename.endswith('.md'):
        # Read the Markdown file
        with open(os.path.join(pages_dir, filename), 'r', encoding='utf-8') as f:
            text = f.read()

        # Convert Obsidian callouts
        text = convert_callouts(text)

        # Convert Obsidian internal links
        text = convert_obsidian_links(text)

        # Convert Markdown content to HTML
        html_content = md.render(text)

        # Page name for the menu. Uppercase only for the first letter
        page_title = filename.replace('.md', '')[0].upper() + filename.replace('.md', '')[1:]

        # Render the content into the template
        output_content = template.render(
            title=page_title,
            content=html_content,
            pages=[f"{file.replace('.md', '.html')}" for file in os.listdir(pages_dir) if file.endswith('.md')]
        )

        # Save the page as an HTML file
        output_filename = os.path.join(output_dir, filename.replace('.md', '.html'))
        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(output_content)
        except Exception as e:
            print(f"Error writing file {output_filename}: {e}")
        
        # Add to the menu
        pages.append((page_title, filename.replace('.md', '.html')))

# Generate the homepage (index.html) with links to all pages
index_content = template.render(
    title="Home",
    content="<h1>Indice dei contenuti</h1><ul>" +
            "".join(f'<li><a href="{page[1]}">{page[0]}</a></li>' for page in pages) +
            "</ul>",
    pages=[page[1] for page in pages]
)

# Save the homepage as index.html
with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(index_content)

# Copy the CSS file to the output folder
css_source = os.path.join(templates_dir, css_filename)
css_dest = os.path.join(output_dir, css_filename)
if os.path.exists(css_source):
    print(f"Copying CSS from {css_source} to {css_dest}")
    shutil.copy(css_source, css_dest)
else:
    print("CSS source not found!")

# Copy any non-Markdown file from the "pages" folder to the "output" folder
for filename in os.listdir(pages_dir):
    src_path = os.path.join(pages_dir, filename)
    dest_path = os.path.join(output_dir, filename)
    
    # Only copy files that are not Markdown files
    if not filename.endswith('.md'):
        try:
            shutil.copy(src_path, dest_path)
            print(f"Successfully copied {src_path} to {dest_path}")
        except Exception as e:
            print(f"Error copying {src_path} to {dest_path}: {e}")


# Print message when done generating the site and where it's saved
print(f"Generated site saved to: {output_dir}")