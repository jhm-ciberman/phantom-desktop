# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2022-11-03

### Added

- Clustering: Added a button to generate a report of the clustering results in HTML format. You can select which groups to include in the report. The option is accesible via "Groups > Export as HTML" in the menu bar.
- Clustering: Added options for "Groups > Rename group...", "Groups > Combine group...", "Faces > Move to group...", "Faces > Remove from group..." and "Faces > Use as main face..." in the menu bar.
- Clustering: Added a new option "Groups > Delete all groups" in the menu bar. This will delete all groups from the project and you will be able to start a new clustering session.
- Clustering: Added a new screen that shows when there are no groups in the project. This screen will allow you to start a new clustering session.
- Clustering: Added a new right-click menu option in each image to "Export Image(s)...".

### Changed

- Clustering: The merging wizard has less padding and the buttons are smaller so they can fit in smaller screens.
- Clustering: The icons in the groups list and group details are now smaller.
- Clustering: Now new faces are automatically added to the best group (or a new group) when they are added to the project and the project has groups.
- Project explorer: The "Export Image" text changes to "Export images" when multiple images are selected.

### Fixed

- Clustering: The program crashes when adding a new face to the project while the clustering page is open.
- Clustering: Keyboard navigation in the groups list doesn't work properly.
- Project explorer: Clicking the "Group similar faces" button opens a new Clustering tab each time even if there is already one open.
- General: The "File > Export Image" option only exports the selected image/s in the project explorer, but not the selected image/s in the clustering page.

## [1.1.0] - 2022-10-30

### Added

- Added support for multiple languages. Spanish and english are currently supported.

### Fixed

- The text in the main toolbar was cut off with the default font in Ubuntu.

## [1.0.0] - 2022-10-28

### Added

- Linux releases are now available on the [releases page](https://github.com/jhm-ciberman/phantom-desktop/releases) as well as the regular Windows releases.
- Tools in Phantom Desktop now open in new tabs instead of new windows.
- Added a new welcome screen that shows when the project is empty.
- Added drag and drop support. Now you can drag and drop image files and Phantom Desktop project files to the main window to open them.
- Inspector panel: Added a button for opening the image in the default image viewer.
- Inspector panel: Now the detected faces bounding boxes are shown in the image.
- Inspector panel: Added a button to show and hide the detected faces bounding boxes.
- Main screen: Added "Edit > Select All" menu item.
- Clustering window: Added the number of faces in each group in the group label.
- Clustering window: The inspector panel is now shown when a face is selected.
- Deblur window: Added a "Reset to defaults" button.

### Changed

- Clustering Window: The faces selector now lets you select multiple faces at once.
- Improved the About window.
- Improved the dialog messages when loading a project.
- Main screen: The left toolbar icons are now smaller.
- Main screen: Added a "New Project" button to the toolbar.

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
[1.1.0]: https://github.com/jhm-ciberman/phantom-desktop/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jhm-ciberman/phantom-desktop/compare/v0.1.0...v1.0.0
[0.1.0]: https://github.com/jhm-ciberman/phantom-desktop/releases/tag/v0.1.0
