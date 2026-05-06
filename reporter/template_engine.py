from jinja2 import Environment, FileSystemLoader
from pathlib import Path

class TemplateEngine:
    def __init__(self, template_dir="reporter/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
    
    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(**context)