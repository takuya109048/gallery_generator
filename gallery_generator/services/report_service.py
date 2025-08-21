import os
from flask import render_template_string

class ReportService:
    def __init__(self, config):
        self.config = config

    def generate_html_report(self, gallery_data, gallery_name):
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Gallery Report</title>
            <style>
                body { font-family: sans-serif; }
                .image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px; }
                .image-item img { width: 100%; height: auto; }
            </style>
        </head>
        <body>
            <h1>Gallery Report</h1>
            {% for node in gallery_data.children recursive %}
                <div class="gallery-section">
                    <h2>{{ node.name }}</h2>
                    {% if node.comment %}
                        <p>{{ node.comment }}</p>
                    {% endif %}
                    <div class="image-grid">
                        {% for image in node.images %}
                            <div class="image-item">
                                <img src="/images/{{ gallery_name }}/{{ image.full_path }}" alt="{{ image.filename }}">
                                <p>{{ image.filename }}</p>
                            </div>
                        {% endfor %}
                    </div>
                    {% if node.children %}
                        {{ loop(node.children) }}
                    {% endif %}
                </div>
            {% endfor %}
        </body>
        </html>
        """
        
        return render_template_string(html_template, gallery_data=gallery_data, gallery_name=gallery_name)


    def generate_markdown_report(self, gallery_data, gallery_name, base_url):
        
        def render_node_md(node, level=1):
            md = ""
            if node.get('name') != 'root':
                md += f"{ '#' * level} {node.get('name')}\n\n"
            
            if node.get('comment'):
                md += f"{node.get('comment')}\n\n"

            if node.get('images'):
                for image in node['images']:
                    image_path = f"{base_url}/images/{gallery_name}/{image.get('full_path')}"
                    md += f"![{image.get('filename')}]({image_path})\n"
                    md += f"*{image.get('filename')}*\n\n"

            if node.get('children'):
                for child in node['children']:
                    md += render_node_md(child, level + 1)
            
            return md

        markdown_content = render_node_md(gallery_data)
        return markdown_content
