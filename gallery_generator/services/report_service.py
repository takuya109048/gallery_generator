import os
from flask import render_template_string

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
                html += f"<h2>{full_path}</h2>" # Fixed to <h2>

                if node.get('comment'):
                    html += f"<p>{node.get('comment')}</p>"

                html += "<div class=\"image-grid\">";
                if node.get('images'):
                    for image in node['images']:
                        image_src = f"{base_url}/images/{gallery_name}/{image.get('full_path')}"
                        html += f"<div class=\"image-item\"><img src=\"{image_src}\" alt=\"{image.get('filename')}\"></div>";
                html += "</div>" # Close image-grid
                html += "</div>" # Close gallery-section

            # Recursively render children, always passing the updated path
            if node.get('children'):
                for child in node['children']:
                    html += render_node_html(child, level + 1, new_path_parts) # Level still increases for path building
            
            return html

        # Start rendering from the root node's children
        rendered_content = ""
        if gallery_data.get('children'):
            for child_node in gallery_data['children']:
                rendered_content += render_node_html(child_node, 1, [])


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
            </style>
        </head>
        <body>
            <h1>{gallery_name}</h1> <!-- Changed to gallery_name -->
            {rendered_content}
        </body>
        </html>
        """
        
        return render_template_string(html_template) # No need to pass gallery_data, gallery_name, base_url to render_template_string
                                                    # as content is already rendered


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
                md += f"## {full_path}\n\n" # Fixed to ##
            
                if node.get('comment'):
                    md += f"{node.get('comment')}\n\n"

                if node.get('images'):
                    for image in node['images']:
                        image_path = f"{base_url}/images/{gallery_name}/{image.get('full_path')}"
                        md += f"![{image.get('filename')}]({image_path})\n"

            if node.get('children'):
                for child in node['children']:
                    md += render_node_md(child, level + 1, new_path_parts) # Level still increases for path building
            
            return md

        # Add top-level heading for Markdown report
        markdown_content = f"# {gallery_name}\n\n" # Added top-level heading
        markdown_content += render_node_md(gallery_data)
        return markdown_content