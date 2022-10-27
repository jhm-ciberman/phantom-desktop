from os import path
import os


app_version = "0.1.0"  # Any semver is fine
app_name = "Phantom Desktop"
app_description = "Phantom Desktop"  # This is shown in the task manager so it should be short
app_repo_url = "https://github.com/jhm-ciberman/phantom-desktop"
app_docs_url = f"{app_repo_url}/wiki"
app_bugs_url = f"{app_repo_url}/issues/new"
app_log_file = "phantom-desktop.log"

# ModelsDownloader
models_release_tag = "v0.1.0"
models_zip_filename = "models.zip"
models_zip_url = f"{app_repo_url}/releases/download/{models_release_tag}/{models_zip_filename}"
models_local_folder = path.join(os.getcwd(), "models")

app_project_extension = "phantom"
app_import_extensions = ["jpg", "jpeg", "png", "bmp", "tif", "tiff"]
app_export_extensions = ["jpg", "png"]
