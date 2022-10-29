# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2022-10-28

### Added

- Linux releases are now available on the [releases page](https://github.com/jhm-ciberman/phantom-desktop/releases) as well as the regular Windows releases.
- The tools in Phantom Desktop now opens in new tabs instead of new windows.
- Added a new welcome screen that shows when the project is empty.
- Added drag and drop support. Now you can drag and drop image files and Phantom Desktop project files to the main window to open them.
- Inspector panel: Added a button for opening the image in the default image viewer.
- Inspector panel: Now the detected faces bounding boxes are shown in the image.
- Inspector panel: Added a button to show and hide the detected faces bounding boxes.
- Main screen: Added "Edit > Select All" menu item.
- Clustering window: Added the number of faces in each group in the group label.
- Deblur window: Added a "Reset to defaults" button.

### Changed

- Clustering Window: The faces selector now lets you select multiple faces at once.
- Improved the About window.
- Improved the dialog messages when loading a project.

### Fixed

- Pressing Cancel in the "Are you sure you want to exit?" dialog closes the application instead of canceling the exit.
- The "Faces merging wizard" card shows even if there are no faces to merge.
- The program crashes when loading a project with missing or corrupt image files.
- Windows task manager shows the program as "A desktop application for forensic image processing" instead of "Phantom Desktop".

## [0.1.0] - 2022-10-20

**WARNING**: This is a pre-release version. The Project file format may change 
at any moment. There is no guarantee of backwards compatibility if you use this
version.

### Added

- Initial release
- Phantom Desktop has useful tools for forensic image processing
- Image Viewer with support for EXIF metadata and image properties
- Image Deblur tool using Lucy-Richardson deconvolution
- Visual Perspective correction tool
- Face detection and clustering with an intuitive user friendly interface
- Support for saving and loading projects


[Unreleased]: https://github.com/jhm-ciberman/phantom-desktop/compare/v0.1.0...HEAD
[1.0.0]: https://github.com/jhm-ciberman/phantom-desktop/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/jhm-ciberman/phantom-desktop/releases/tag/v0.1.0
