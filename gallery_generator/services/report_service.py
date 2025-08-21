import os
from flask import render_template_string
import re # Import re

class ReportService:
    def __init__(self, config):
        self.config = config

    def generate_html_report(self, gallery_data, gallery_name, base_url):
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
                html += f"<div class=\"gallery-section\">"
                html += f"<h3>{full_path}</h3>"

                if node.get('comment'):
                    html += f"<div class=\"comment-box\"><p>{node.get('comment')}</p></div>"
                
                html += "<div class=\"image-grid\">";
                if node.get('images'):
                    for image in node['images']:
                        image_src = f"{base_url}/images/{gallery_name}/{image.get('full_path')}"
                        html += f"<div class=\"image-item\"><img src=\"{image_src}\" alt=\"{image.get('filename')}\"></div>"
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

        html_template = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Gallery Report</title>
            <style>
                body {{ font-family: sans-serif; }}
                .image-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }}
                .image-item img {{ width: 100%; height: auto; }}
                .comment-box {{ border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; background-color: #f9f9f9; border-radius: 5px; }}
                .comment-box p {{ margin: 0; }}
            </style>
        </head>
        <body>
            <h2>{gallery_name}</h2>
            <hr> <!-- Added horizontal rule after main title -->
            {rendered_content}
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
                    # Start HTML for 3-column grid
                    md += "<div style=\"display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;\">"
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
