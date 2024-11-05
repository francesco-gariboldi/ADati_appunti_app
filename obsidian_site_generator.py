import os
import sys
import re
import shutil
from markdown_it import MarkdownIt
from jinja2 import Environment, FileSystemLoader

# Function to get base directory
def get_base_dir():
    return sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# Directories and Paths
base_dir = get_base_dir()
pages_dir = os.path.join(base_dir, 'pages')
os.makedirs(pages_dir, exist_ok=True)
css_filename = 'style.css'

# Output root for the Flask-ready frontend
output_dir_frontend = os.path.join(base_dir, 'app_frontend')
output_templates_dir = os.path.join(output_dir_frontend, 'templates')
output_static_dir = os.path.join(output_dir_frontend, 'static')
output_images_dir = os.path.join(output_static_dir, 'images')
os.makedirs(output_templates_dir, exist_ok=True)
os.makedirs(output_static_dir, exist_ok=True)
os.makedirs(output_images_dir, exist_ok=True)

# Set up the Jinja2 environment and Markdown renderer
templates_dir = os.path.join(base_dir, 'templates')
env = Environment(loader=FileSystemLoader(templates_dir))
template = env.get_template('base.html')
md = MarkdownIt()

# Function to convert Obsidian-style links
def convert_obsidian_links(text):
    md_reg = r'(!)?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'

    def replace_link(match):
        is_embed = bool(match.group(1))
        link_target = match.group(2).strip()
        alt_text = match.group(3).strip() if match.group(3) else link_target
        if is_embed:
            return f'<img src="static/images/{link_target}" alt="{alt_text}">'
        else:
            return f'<a href="{link_target}.html">{alt_text}</a>'

    return re.sub(md_reg, replace_link, text)

# Function to convert Obsidian callouts
def convert_callouts(text):
    callout_pattern = r'^\s*>\s*(\[\s*(!|\?|i|x)\s*\])?\s*(.*)$'
    callout_classes = {'!': 'note', '?': 'question', 'i': 'info', 'x': 'warning'}

    def callout_replacer(match):
        callout_type = match.group(2)
        content = match.group(3)
        callout_class = callout_classes.get(callout_type, 'note') if callout_type else 'blockquote'
        return f'<div class="callout {callout_class}"><p>{content}</p></div>'

    return '\n'.join(re.sub(callout_pattern, callout_replacer, line) for line in text.split('\n'))

# Generate pages from Markdown files
pages = []
for filename in os.listdir(pages_dir):
    if filename.endswith('.md'):
        try:
            with open(os.path.join(pages_dir, filename), 'r', encoding='utf-8') as f:
                text = f.read()

            # Process Markdown content
            text = convert_callouts(convert_obsidian_links(text))
            html_content = md.render(text)
            page_title = filename.replace('.md', '').capitalize()

            # Render content into the template
            output_content = template.render(
                title=page_title,
                content=html_content,
                pages=[f"{file.replace('.md', '.html')}" for file in os.listdir(pages_dir) if file.endswith('.md')]
            )

            # Save HTML output to frontend directory
            output_filename_frontend = os.path.join(output_templates_dir, filename.replace('.md', '.html'))
            with open(output_filename_frontend, 'w', encoding='utf-8') as f:
                f.write(output_content)

            print(f"Generated HTML for {filename}")
            pages.append((page_title, filename.replace('.md', '.html')))

        except Exception as e:
            print(f"Error processing {filename}: {e}")

# Generate the homepage with links to all pages for the standalone version
index_content = template.render(
    title="Home",
    content="<h1>Indice dei contenuti</h1><ul>" +
            "".join(f'<li><a href="{page[1]}">{page[0]}</a></li>' for page in pages) +
            "</ul>",
    pages=[page[1] for page in pages]
)

# Save the homepage as index.html in the templates folder
output_index_path = os.path.join(output_templates_dir, 'index.html')
with open(output_index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)

print(f"Generated index.html for the homepage")

# Copy CSS file to the frontend output directory
css_source = os.path.join(templates_dir, css_filename)
css_dest_frontend = os.path.join(output_static_dir, css_filename)
if os.path.exists(css_source):
    shutil.copy(css_source, css_dest_frontend)
    print(f"CSS copied to {css_dest_frontend}")
else:
    print("CSS source not found!")

# Copy images from pages directory to static/images directory
image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')
for filename in os.listdir(pages_dir):
    if filename.lower().endswith(image_extensions):
        source_path = os.path.join(pages_dir, filename)
        destination_path = os.path.join(output_images_dir, filename)
        shutil.copy2(source_path, destination_path)
        print(f"Copied image {filename} to static/images")

# Copy any non-Markdown file from the "pages" folder to an "extra_files" folder
extra_files_dir = os.path.join(output_static_dir, 'extra_files')
os.makedirs(extra_files_dir, exist_ok=True)
for filename in os.listdir(pages_dir):
    src_path = os.path.join(pages_dir, filename)
    dest_path = os.path.join(extra_files_dir, filename)
    if not filename.endswith('.md') and not filename.lower().endswith(image_extensions):
        try:
            shutil.copy(src_path, dest_path)
            print(f"Copied {filename} to {extra_files_dir}")
        except Exception as e:
            print(f"Error copying {filename}: {e}")

print(f"Generated Flask-ready frontend saved to: {output_dir_frontend}")
