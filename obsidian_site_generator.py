import os
import sys
import re
import shutil
from markdown_it import MarkdownIt
from jinja2 import Environment, FileSystemLoader

# Function to get base directory
def get_base_dir():
    return sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

# Initialize directories
base_dir = get_base_dir()
pages_dir = os.path.join(base_dir, 'pages')
templates_dir = os.path.join(base_dir, 'templates')
css_filename = 'style.css'

# Ensure necessary directories exist
os.makedirs(pages_dir, exist_ok=True)

# Output directories for the converted files
output_dir_frontend = os.path.join(base_dir, 'frontend_files')
output_templates_dir = os.path.join(output_dir_frontend, 'templates')
output_static_dir = os.path.join(output_dir_frontend, 'static')
output_images_dir = os.path.join(output_static_dir, 'images')
extra_files_dir = os.path.join(output_static_dir, 'extra_files')

# Create output directories
os.makedirs(output_templates_dir, exist_ok=True)
os.makedirs(output_static_dir, exist_ok=True)
os.makedirs(output_images_dir, exist_ok=True)
os.makedirs(extra_files_dir, exist_ok=True)

# Set up the Jinja2 environment and Markdown renderer
env = Environment(loader=FileSystemLoader(templates_dir))
template = env.get_template('base.html')
md = MarkdownIt()

# Function to convert Obsidian-style links
# For resources-link: "![[]]" or notes-link: "[[]]"
# matches every "|text" if existing" (the custom link alias)
# and replaces it with the correct HTML (i.e., the alternative display text)
def convert_obsidian_links(text):
    md_reg = r'(!)?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]'

    # Function to replace the matched link with HTML
    def replace_link(match):
        is_embed = bool(match.group(1))
        link_target = match.group(2).strip()
        alt_text = match.group(3).strip() if match.group(3) else link_target
        if is_embed:
            # If it's an image, return an <img> tag, otherwise return a link
            return f'<img src="static/images/{link_target}" alt="{alt_text}">'
        else:
            return f'<a href="{link_target}.html">{alt_text}</a>'

    return re.sub(md_reg, replace_link, text)

# Function to convert Obsidian callouts
def convert_callouts(text):
    callout_pattern = re.compile(r'^\s*>\s*(\[\s*!?\s*([\w-]+)\s*\])?\s*(.*)$')
    
    lines = text.split("\n")
    converted_lines = []
    inside_callout = False
    callout_class = "blockquote"
    callout_content = []

    for line in lines:
        match = callout_pattern.match(line)
        
        if match:
            callout_type = match.group(2)  # Extract callout type (e.g., 'note', 'question')
            content = match.group(3)  # Extract actual content
            
            if callout_type:
                callout_class = callout_type.lower()
                inside_callout = True
                callout_content = [content]  # Start a new callout
            else:
                # Normal blockquote (no callout)
                converted_lines.append(f'<blockquote>{content}</blockquote>')
        else:
            if inside_callout:
                if line.strip().startswith(">"):
                    callout_content.append(line.lstrip("> ").strip())  # Add to callout body
                else:
                    # Callout ended, write the HTML and reset
                    converted_lines.append(f'<div class="callout {callout_class}"><p>{"<br>".join(callout_content)}</p></div>')
                    inside_callout = False
                    converted_lines.append(line)  # Process this line normally
            else:
                converted_lines.append(line)

    # If the last line was a callout, make sure to close it
    if inside_callout:
        converted_lines.append(f'<div class="callout {callout_class}"><p>{"<br>".join(callout_content)}</p></div>') 

    return "\n".join(converted_lines)

# Function to wrap code blocks and inline code with HTML tags
def wrap_code_blocks(text):
    # This function will replace triple-backtick code blocks with HTML
    # Prism.js expects <pre><code class="language-XYZ"> ... </code></pre>
    def code_block_replacer(match):
        # Group 1 is the optional language specifier; Group 2 is the code content.
        language = match.group(1) or ""
        code_content = match.group(2)
        # Clean up the language string and build the Prism class:
        language = language.strip()
        lang_class = f"language-{language}" if language else "language-none"
        return f'<pre><code class="{lang_class}">{code_content}</code></pre>'

    # The regex breakdown:
    # - ``` starts the code block
    # - (?:([\w+-]+))? optionally captures a language specifier consisting of word characters,
    #   pluses or dashes (you can adjust this pattern if needed)
    # - \n requires that the language (if provided) is followed by a newline
    # - (.*?) lazily captures everything (including newlines, because of re.DOTALL) as the code content
    # - ``` ends the code block
    text = re.sub(
        r'```(?:([\w+-]+))?\n(.*?)```',
        code_block_replacer,
        text,
        flags=re.DOTALL
    )
    
    # Convert inline code (using single backticks) to <code> tags.
    # We use negative lookbehind and lookahead to avoid conflicts with the triple backticks.
    text = re.sub(
        r'(?<!`)`([^`\n]+)`(?!`)',
        r'<code class="code-inline">\1</code>',
        text
    )
    
    return text


# Function to process Markdown files
def generate_html_from_markdown(filename):
    try:
        # Read the Markdown content
        with open(os.path.join(pages_dir, filename), 'r', encoding='utf-8') as f:
            text = f.read()

        # Process Markdown content
        text = convert_callouts(convert_obsidian_links(text))
        html_content = md.render(text)  # Convert Markdown to HTML

        # Apply code wrapping after Markdown processing
        html_content = wrap_code_blocks(html_content)

        # Wrap content with MathJax processing tag
        page_title = filename.replace('.md', '').capitalize()
        html_content = f"<main class='mathjax_process'>{html_content}</main>"

        # Render content into the template
        output_content = template.render(
            title=page_title,
            content=html_content,
            pages=[file.replace('.md', '.html') for file in os.listdir(pages_dir) if file.endswith('.md')]
        )

        # Save HTML output to frontend directory
        output_filename_frontend = os.path.join(output_templates_dir, filename.replace('.md', '.html'))
        with open(output_filename_frontend, 'w', encoding='utf-8') as f:
            f.write(output_content)

        print(f"Generated HTML for {filename}")
        return page_title, filename.replace('.md', '.html')

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return None

# Generate pages from Markdown files
pages = [generate_html_from_markdown(filename) for filename in os.listdir(pages_dir) if filename.endswith('.md')]
pages = [page for page in pages if page]  # Filter out any None results from errors

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
print("Generated index.html for the homepage")

# Function to copy assets like CSS and images
def copy_assets():
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
    for filename in os.listdir(pages_dir):
        if not filename.endswith('.md') and not filename.lower().endswith(image_extensions):
            src_path = os.path.join(pages_dir, filename)
            dest_path = os.path.join(extra_files_dir, filename)
            try:
                shutil.copy(src_path, dest_path)
                print(f"Copied {filename} to {extra_files_dir}")
            except Exception as e:
                print(f"Error copying {filename}: {e}")

# Execute asset copying
copy_assets()

print(f"Generated frontend saved to: {output_dir_frontend}")
