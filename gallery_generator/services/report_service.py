import os
from flask import render_template_string
import re # Import re

class ReportService:
    def __init__(self, config):
        self.config = config

    def generate_html_report(self, gallery_data, gallery_name, base_url):
        
        # List to store TOC entries
        toc_entries = []

        # Helper function to generate a slug for IDs
        def slugify(text):
            text = re.sub(r'[^\w\s-]', '', text).strip().lower()
            text = re.sub(r'[-\s]+', '-', text)
            return text

        # Helper function to render HTML nodes recursively and build full paths
        def render_node_html(node, level=1, current_path_parts=None):
            if current_path_parts is None:
                current_path_parts = []

            html = ""
            
            node_name = node.get('name')
            
            # Construct full path for the current node
            if node_name == 'root':
                full_path = ""
                new_path_parts = [] # No path parts for root
            else:
                new_path_parts = current_path_parts + [node_name]
                full_path = "/".join(new_path_parts)

            # Check if this node has direct images
            has_direct_images = bool(node.get('images'))

            # Only display heading and direct images if the node has direct images and is not the root
            if node_name != 'root' and has_direct_images:
                heading_id = slugify(full_path) # Generate ID for jump link
                toc_entries.append({'path': full_path, 'id': heading_id}) # Add to TOC entries

                html += f"<div class=\"gallery-section\">"
                html += f"<h3 id=\"{heading_id}\">{full_path}</h3>" # Add ID to heading

                if node.get('comment'):
                    html += f"<div class=\"comment-box\"><p>{node.get('comment')}</p></div>"
                
                html += "<div class=\"image-grid\">"
                if node.get('images'):
                    for image in node['images']:
                        image_src = f"{base_url}/images/{gallery_name}/{image.get('full_path')}"
                        html += f"<div class=\"image-item\"><img src=\"{image_src}\" alt=\"{image.get('filename')}\" style=\"width: 100%; height: auto;\"></div>"
                html += "</div>" # Close image-grid
                html += "</div>" # Close gallery-section
                html += "<hr>\n" # Add horizontal rule after each section

            # Recursively render children, always passing the updated path
            if node.get('children'):
                for child in node['children']:
                    html += render_node_html(child, level + 1, new_path_parts)
            
            return html

        # Start rendering from the root node's children
        rendered_content = ""
        if gallery_data.get('children'):
            for child_node in gallery_data['children']:
                rendered_content += render_node_html(child_node, 1, [])

        # Remove the last <hr> if it exists
        if rendered_content.endswith("<hr>\n"):
            rendered_content = rendered_content[:-5] # Remove "<hr>\n"

        # Generate TOC HTML
        toc_html = ""
        if toc_entries:
            toc_html += "<ul>\n"
            for entry in toc_entries:
                toc_html += f"<li><a href=\"#{entry['id']}\">{entry['path']}</a></li>\n"
            toc_html += "</ul>\n"


        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Gallery Report</title>
            <style>
                body {{ font-family: sans-serif; margin: 0; }}
                .app-header {{
                    display: flex;
                    align-items: center;
                    padding: 10px 20px;
                    background-color: #e9ecef;
                    border-bottom: 1px solid #ced4da;
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 58px;
                    z-index: 1000;
                    box-sizing: border-box;
                }}
                .app-logo {{
                    font-size: 22px;
                    font-weight: bold;
                }}
                .sidebar {{ 
                    width: 300px; 
                    padding: 20px; 
                    background-color: #f0f0f0; 
                    border-right: 1px solid #ccc; 
                    overflow-y: auto; 
                    position: fixed; 
                    height: calc(100vh - 58px); 
                    top: 58px; 
                    left: 0; 
                }}
                .sidebar h3 {{ margin-top: 0; }}
                .sidebar ul {{ list-style: none; padding: 0; }}
                .sidebar li a {{ display: block; padding: 5px 0; text-decoration: none; color: #333; font-size: 14px; }}
                .sidebar li a:hover {{ background-color: #e0e0e0; }}
                .main-content {{ padding: 20px; margin-left: 340px; margin-top: 58px; }}
                .main-content h3 {{ scroll-margin-top: 58px; }}
                .image-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }}
                .image-item img {{ width: 100%; height: auto; }}
                .comment-box {{ border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .comment-box p {{ margin: 0; }}
            </style>
        </head>
        <body>
            <div class="app-header">
                <span class="app-logo">{gallery_name} Report</span>
            </div>
            <div class="sidebar">
                <h3>Table of Contents</h3>
                {toc_html}
            </div>
            <div class="main-content">
                {rendered_content}
            </div>
        </body>
        </html>
        """
        
        return render_template_string(html_template)


    def generate_markdown_report(self, gallery_data, gallery_name, base_url):
        
        def render_node_md(node, level=1, current_path_parts=None):
            if current_path_parts is None:
                current_path_parts = []

            md = ""
            
            node_name = node.get('name')

            # Construct full path for the current node
            if node_name == 'root':
                full_path = ""
                new_path_parts = [] # No path parts for root
            else:
                new_path_parts = current_path_parts + [node_name]
                full_path = "/".join(new_path_parts)

            # Check if this node has direct images
            has_direct_images = bool(node.get('images'))

            # Only display heading and direct images if the node has direct images and is not the root
            if node_name != 'root' and has_direct_images:
                md += f"### {full_path}\n\n"
            
                if node.get('comment'):
                    md += f"```txt\n{node.get('comment')}\n```\n\n"
                
                if node.get('images'):
                    # Start HTML for 3-column grid within a Markdown code block
                    md += "<div style=\"display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;\">";
                    for image in node['images']:
                        image_path = f"{base_url}/images/{gallery_name}/{image.get('full_path')}"
                        md += f"  <div style='text-align: center;'><img src='{image_path}' alt='{image.get('filename')}' style='width: 100%; height: auto;'></div>\n"
                    md += "</div>\n\n"
                md += "---\n\n" # Add Markdown horizontal rule after each section

            if node.get('children'):
                for child in node['children']:
                    md += render_node_md(child, level + 1, new_path_parts)
            
            return md

        # Add top-level heading for Markdown report
        markdown_content = f"## {gallery_name}\n\n"
        markdown_content += "---\n\n" # Added horizontal rule after main title
        markdown_content += render_node_md(gallery_data)
        
        # Remove the last "---" if it exists, along with any trailing newlines
        # Use a regex for more robust removal of trailing horizontal rules
        markdown_content = re.sub(r'---\n\n$', '', markdown_content) # Remove "---" followed by two newlines at the end
        markdown_content = markdown_content.rstrip() # Remove any remaining trailing whitespace

        return markdown_content