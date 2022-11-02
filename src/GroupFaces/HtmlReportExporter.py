# Path: ./res/html/report.html
# <!DOCTYPE html>
# <html lang="{{ language }}">
# <head>
#     <meta charset="UTF-8">
#     <meta http-equiv="X-UA-Compatible" content="IE=edge">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <link rel="stylesheet" href="gutenberg.min.css" media="print">
#     <link rel="stylesheet" href="styles.css" media="all">
#     <title>{{ __("title") }}</title>
# </head>
# <body>
#     <div class="page-header">
#         <img src="icon.png" alt="Phantom Desktop" width="62" height="62">
#         <h1>Phantom<span>Desktop</span></h1>

#         <ul class="info">
#             <li><span>{{ __("generated_at") }}</span> {{ generated_at }}</li>
#             <li><span>{{ __("phantom_version") }} </span> {{ phantom_version }}</li>
#             <li><span>{{ __("total_images") }}</span> {{ total_images }}</li>
#         </ul>
#     </div>

#     {% for group in groups %}
#         <div class="group-header">
#             <img src="{{ group.icon }}" alt="{{ group.name }}" width="62" height="62">
#             <div>
#                 <h2>{{ group.name }}</h2>
#                 <p>{{ group.description }}</p>
#             </div>
#         </div>

#         <div class="images-grid">
#             {% for image in group.images %}
#                 <div class="image-item">
#                     <img src="{{ image.path }}" alt="{{ image.name }}">
#                     <div>{{ image.name }}</div>
#                 </div>
#             {% endfor %}
#         </div>

#         <div style="page-break-after: always;"></div>
#     {% endfor %}
# </body>
# </html>

from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from ..Models import Group
from ..Application import Application
import os
import shutil
from ..l10n import LocalizationService, __


@dataclass
class ImageInfo:
    name: str
    path: str


@dataclass
class GroupInfo:
    name: str
    description: str
    icon: str
    images: list[ImageInfo]


@dataclass
class ReportInfo:
    language: str
    generated_at: str
    phantom_version: str
    total_images: int
    groups: list[GroupInfo]


class HtmlReportExporter:
    """
    Exports a list of groups as an HTML Report to a given folder. Images are copied to a subfolder in "./img/".
    All HTML resources are copied to the given folder.
    """

    def __init__(self, groups: list[Group], filename: str):
        """
        Initializes a new instance of the HtmlReportExporter class.

        Args:
            groups (list[Group]): The list of groups to export.
            filename (str): The filename of the HTML report.
            language (str, optional): The language to use. Defaults to "en".
        """
        self.groups = groups
        self.filename = filename
        self.folder = os.path.dirname(filename)
        self.language = LocalizationService.instance().get_language()

    def export(self):
        """
        Exports the report
        """
        img_folder = os.path.join(self.folder, "img")
        if not os.path.exists(img_folder):
            os.makedirs(img_folder)

        report_info = self._get_report_info()
        self._generate_html(report_info)
        self._copy_resources()

    def _copy_resources(self):
        """
        Copies all HTML resources to the given folder
        """

        resources = [
            ("res/html/gutenberg.min.css", "gutenberg.min.css"),
            ("res/html/styles.css", "styles.css"),
            ("res/html/icon.png", "icon.png"),
        ]

        for src, dest in resources:
            shutil.copy(src, os.path.join(self.folder, dest))

    def _generate_html(self, report_info: ReportInfo):
        """
        Generates the HTML report
        """
        # Load template
        env = Environment(loader=FileSystemLoader("res/html"))
        template = env.get_template("report.html")

        def trans(key: str) -> str:
            """Returns a localized string for the given key"""
            return LocalizationService.instance().get("@groups_report." + key)

        # Register localization function
        env.globals["__"] = trans

        # Render template
        html = template.render(report_info.__dict__)

        # Write to file
        with open(self.filename, "w", encoding="utf-8") as file:
            file.write(html)

    def _get_report_info(self) -> ReportInfo:
        """
        Returns the report info for the given groups
        """
        groups = []
        total_images_count = 0

        for group in self.groups:
            images = []

            for face in group.faces:
                image = face.image
                original_ext = os.path.splitext(image.path)[1]
                display_name = os.path.basename(image.path)
                dest = os.path.join("img", f"{image.id}{original_ext}")
                images.append(ImageInfo(display_name, dest))
                shutil.copyfile(image.path, os.path.join(self.folder, dest))

            count = len(images)
            description = __("{count} images", count=count) if count > 1 else __("{count} image", count=count)
            main_face = group.main_face
            icon_path = os.path.join("img", f"group_{group.id}.png")
            main_face.get_square_pixmap(128).save(os.path.join(self.folder, icon_path))
            group_name = group.name if group.name else __("Unnamed")
            groups.append(GroupInfo(group_name, description, icon_path, images))
            total_images_count += len(images)

        now = datetime.now()

        return ReportInfo(
            language=self.language,
            generated_at=now.strftime("%Y/%m/%d %H:%M:%S"),
            phantom_version="v" + Application.applicationVersion(),
            total_images=total_images_count,
            groups=groups,
        )
