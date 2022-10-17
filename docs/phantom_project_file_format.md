# Phantom Project File Specification

> **WARNING**: This specification is still a work in progress and is subject to change.

Phantom Desktop is a desktop application for forensic digital image processing. This document describes the project file format used by Phantom Desktop.

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" 
in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

The JSON object notation described in this document follows the [TypeScript](https://www.typescriptlang.org/) object notation.

## Overview

A phantom project is defined as a file that MAY end with the `.phantom` extension. The file is a JSON file, that MAY be compressed using the [gzip](https://www.gnu.org/software/gzip/) algorithm. The file header of the file MUST start one of the following bytes:

- `0x1F 0x8B` for gzip compressed files. This is the [magic number](https://en.wikipedia.org/wiki/List_of_file_signatures) for gzip files.
- `0x7B` (ASCII `{`) for uncompressed files. This is the first byte of a JSON object.

Any other file header MUST be considered invalid and the file MUST NOT be opened.

The general structure of the phantom project file is as follows:

```typescript
{
    "version": number,
    "project": Project?,
    "images": Image[]?,
    "faces": Face[]?,
    "groups": Group[]?,
    "buffers": {
        "encodings": Buffer
    }?
}
```

***version:***
The `version` field MUST be a number that represents the version of the project file format. The current version is `1`.

At the time of writing, the only valid value for this field is `1` and any other value MUST be considered invalid. This 
field is the only required field in the project file. All other fields are completely optional. This means that the
minimum valid project file is: ```{ "version": 1 }```

**project**
This is an object that represents the project settings. The `project` field MAY be `null` or `undefined`. See the
[Project](#project) section for more information.

**images**
This is an array of objects that represent the images in the project. The `images` field MAY be `null` or `undefined` if
the project does not contain any images. See the [Images](#images) section for more information.

**faces**
This is an array of objects that represent the faces in the project. The `faces` field MAY be `null` or `undefined` if
the project does not contain any faces. See the [Faces](#faces) section for more information.

**groups**
This is an array of objects that represent the groups in the project. The `groups` field MAY be `null` or `undefined` if
the project does not contain any groups. See the [Groups](#groups) section for more information.

**buffers**
This is an object that contains the buffers used by the project. The `buffers` field MAY be `null` or `undefined` if
the project does not contain any buffers. At the moment only one buffer is used, the `encodings` buffer. See the
[Buffers](#buffers) section for more information.


All entities in the project have a unique identifier. The identifier is a UUID version 4 string. The identifier MUST be
unique across all entities in the project and should be preserved accross different saves of the project file.

## Project

The `project` field is an object that contains information about the project. The structure of the object is as follows:

```typescript
{
    "client_name": string?,
    "client_version": string?,
    "files_dir": string?,
}
```

**client_name**
The name of the application that created the project file. This field is optional and MAY be `null`.
For Phantom Desktop, this field MUST be set to `Phantom Desktop`. For any other application or fork of Phantom Desktop,
this field SHOULD be set to the name of the application.

**client_version**
The version of the application that created the project file. This field is optional and MAY be `null`.
For Phantom Desktop, this field SHOULD be set to the version of Phantom Desktop that created the project file.

**files_dir**
The path to the directory where the project files are stored. This MUST be set when the project is saved
in **portable** mode. This field is optional and MAY be `null`. For more information about portable mode, see the
[Portable Mode](#portable-mode) section.


## Images

The `images` field is an array of objects that contain information about the images in the project. The structure of the object is as follows:

```typescript
{
    "id": string,
    "src": string,
    "original_src": string?,
    "faces": string[]?,
    "processed": boolean?,
    "hashes": {
        [key: string]: string
    }?
}
```

**id**
The unique identifier of the image. This is a UUIDv4 string.

**src**
The path to the image file. This field MUST be a valid URI. Two different types of URIs are supported:
- Relative paths. The URI MUST start with `file:` and MUST be followed by the relative path to the image file. 
For example: `file:./project_files/image.jpg`, `file:../project_files/image.jpg`, `file:project_files/image.jpg`.
- Absolute paths. The URI MUST start with `file:///` and MUST be followed by the absolute path to the image file. 
For example: `file:///C:/Users/username/Pictures/image.jpg`, `file:///home/username/Pictures/image.jpg`, `file:///Pictures/image.jpg`.
Any other URI MUST be considered invalid. Other schemas are reserved for future use.
The path can be a Windows path or a Unix path. Both path separators (`\` and `/`) are supported and MUST be treated as equal. It is recommended
to not mix path separators in the same path.

**original_src**
The original URI to the image file. This is the path where the image was originally located before it was moved to the project directory for the first time.
For example if the user created a new project and added an image from `C:/Users/username/Pictures/image.jpg`, the `original_src` field will be set to `file:///C:/Users/username/Pictures/image.jpg`. When the user saves the project in portable mode, the image will be copied to the project directory and the `src` field will be set to `file:./project_files/image.jpg`. The `original_src` field will remain unchanged and will still be set to `file:///C:/Users/username/Pictures/image.jpg`.
This field is only informative for the user and has no impact on the loading or saving of the project file. This field is optional and MAY be `null`.
Other schemas are reserved for future use, for example if the user adds an image from a remote server, the `original_src` field MAY be set to `http://example.com/image.jpg`.
In contrast to the `src` field, the `original_src` field MUST NOT be a relative path, only absolute URIs are supported.

**faces**
An array of UUIDv4 strings that represent the faces that are present in the image. The order of the faces in the array is not important.

**processed**
A boolean that indicates whether the image has been processed or not. This field is optional and MAY be `null`. If this field is `null`, it MUST be considered `false`.
A value of `true` indicates that the image has been processed and that the faces in the image have been detected and encoded. A value of `false` indicates that the image has not been processed yet to detect and encode the faces.

**hashes**
A dictionary of hashes that can be used to verify the integrity of the image file. The keys of the dictionary are the hash algorithm names and the values are the hashes. For example: `{"md5": "1234", "sha1": "5678"}`. 

## Faces

The `faces` field is an array of objects that contain information about the faces in the project. The structure of the object is as follows:

```typescript
{
    "id": string,
    "aabb": [number, number, number, number],  // x, y, w, h
    "encoding": number,
    "confidence": number?
}
```

**id**
The unique identifier of the face. This is a UUIDv4 string.

**aabb**
The axis-aligned bounding box of the face. This is an array of 4 numbers that represent the x, y, width and height of the bounding box measured in image pixels. For example, if the image is 1000x1000 pixels, the bounding box of a face that is located at the top-left corner of the image and has a size of 100x100 pixels will be `[0, 0, 100, 100]`.

**encoding**
The index of the encoding of the face in the `encodings` buffer. MUST be a non-negative integer.

**confidence**
The confidence of the face detection algorithm. This is a number that represents the confidence of the face detection algorithm. The value MAY be between 0 and 1 but other values are also possible. The values SHOULD be comparable between different faces inside the same project file but DO NOT need to be comparable between different projects. A higher value indicates a higher confidence. This field is optional and MAY be `null`.

## Groups

The `groups` field is an array of objects that contain information about the groups in the project. The structure of the object is as follows:


```typescript
{
    "id": string,
    "name": string,
    "faces": string[],
    "main_face_override": string?,
    "centroid": number,
    "dont_merge_with": string[]
}
```

**id**
The unique identifier of the group. This is a UUIDv4 string.

**name**
The name of the group. This is a string that can be used to identify the group. This field is optional and MAY be `null`.
The name is defined by the user and has no impact on the loading or saving of the project file.

**faces**
An array of UUIDv4 strings that represent the faces that are present in the group. The order of the faces in the array is not important.

**main_face_override**
The unique identifier of the face that is used as the main face of the group. This is a UUIDv4 string. This field is optional and MAY be `null`.
This represents the face that should be displayed in the UI as the main representative of the group. If this field is `null`, the main face of the group MAY be determined automatically by the application in any way it sees fit. The current implementation of Phantom Desktop uses the face with the highest confidence as the main face of the group.

**centroid**
The index of the encoding of the centroid of the group in the `encodings` buffer. MUST be a non-negative integer.

**dont_merge_with**
An array of UUIDv4 strings that represent the groups that should not be merged with this group. The order of the groups in the array is not important.

## Buffer

A buffer contains information about binary data that is stored in the project file. 
At the moment the buffers are only stored inline with the project JSON file, but the format is prepared to support buffers in extenal files in the future.

The structure of a buffer is as follows:

```typescript
{
    "dtype": string,
    "stride": number,
    "count": number?,
    "data": string
}
```

A buffer contains `count` arrays of `stride` number of elements with type of `dtype`. For example:

```typescript
{
    "dtype": "float64",
    "stride": 128,
    "count": 10,
    "data": "AAECAwQFBgcICQoL... (base64 encoded data)"
}
```

This buffer contains 10 arrays of 128 doubles. The data is stored in little-endian format (The same as the default byte order of the x86 architecture).

**dtype**
The data type of the buffer. This is a string that represents the data type of the buffer. At the moment, the only valid value is `"float64"`.

**stride**
The number of elements in each array. This is a non-negative integer. 

**count**
The number of arrays in the buffer. This is a non-negative integer. This field is optional and MAY be `null`. If this field is `null`, it MUST be computed by dividing the length of the `data` field by the size of the `dtype` in bytes. The current implementation of Phantom Desktop writes to this field but does not use it when reading the project file.

**data**
The data of the buffer. This is a base64 encoded string that contains the data of the buffer. The data is stored in little-endian format (The same as the default byte order of the x86 architecture).

### Encodings Buffer

At the moment, the only buffer that is used in the project file is the `encodings` buffer. This buffer contains the encodings of the faces in the project. 
The encoding of a face is a vector of 128 doubles that represent the face. Two vectors that have a closer euclidean distance between them are more likely to represent the same face. 


## Portable Mode

When a project is saved in **portable** mode, all the image files referenced by the project are copied to a 
directory that is specified by the `project.files_dir` field relative to the project file location. 

For example, supose a project that has these images with the following paths:

```
C:\images\image1.jpg
C:\images\image2.jpg
F:\some\other\image.png
```

If the user saves the project in portable mode in the following location:

```
C:\Users\John\Documents\my_project.phantom
```

All the images will be copied to the following location:

```
C:\Users\John\Documents\my_project_files\image1.jpg
C:\Users\John\Documents\my_project_files\image2.jpg
C:\Users\John\Documents\my_project_files\image.png
```

And the project file will be updated to contain the following paths:


```typescript
{
    "project": {
        "files_dir": "files",
    },
    "images": [
        {
            "id": "61d9bd97-b719-4321-b53e-763201682796",
            "src": "file:./files/image1.jpg",
        },
        {
            "id": "bcc88643-cb74-4cd1-8a0d-2fb969ce3577",
            "src": "file:./files/image2.jpg",
        },
        {
            "id": "f5b5c8f5-3b8f-4b9f-9c1f-8c8c8c8c8c8c",
            "src": "file:./files/image.png",
        }
    ]
}
```

Note that the `src` paths start with the `file:` scheme and are relative to the project file location. This is not obligatory, and could be a project with mixed
absolute and relative paths, but this is the recommended way to do it.

# Examples

## Example 1

This is an example of a project file with 2 faces in 2 groups. The project is saved in portable mode.

```typescript
{
    "version": 1,
    "project": {
        "files_dir": "files",
    },
    "images": [
        {
            "id": "61d9bd97-b719-4321-b53e-763201682796",
            "src": "file:./files/image1.jpg",
        },
        {
            "id": "bcc88643-cb74-4cd1-8a0d-2fb969ce3577",
            "src": "file:./files/image2.jpg",
        }
    ],
    "faces": [
        {
            "id": "f5b5c8f5-3b8f-4b9f-9c1f-8c8c8c8c8c8c",
            "image_id": "61d9bd97-b719-4321-b53e-763201682796",
            "rect": [0, 0, 100, 100],
            "encoding": 0,
            "confidence": 0.9,
        },
        {
            "id": "f5b5c8f5-3b8f-4b9f-9c1f-8c8c8c8c8c8d",
            "image_id": "bcc88643-cb74-4cd1-8a0d-2fb969ce3577",
            "rect": [0, 0, 100, 100],
            "encoding": 1,
            "confidence": 0.85,
        }
    ],
    "groups": [
        {
            "id": "f5b5c8f5-3b8f-4b9f-9c1f-8c8c8c8c8c8e",
            "name": "John Doe",
            "faces": ["f5b5c8f5-3b8f-4b9f-9c1f-8c8c8c8c8c8c"],
            "main_face_override": null,
            "centroid": 0,
            "dont_merge_with": [],
        },
        {
            "id": "f5b5c8f5-3b8f-4b9f-9c1f-8c8c8c8c8c8f",
            "name": "Mary Williams",
            "faces": ["f5b5c8f5-3b8f-4b9f-9c1f-8c8c8c8c8c8d"],
            "main_face_override": null,
            "centroid": 1,
            "dont_merge_with": [],
        }
    ],
    "buffers": {
        "encodings": {
            "dtype": "float64",
            "stride": 128,
            "count": 2,
            "data": "AAECAwQFBgcICQoL... (base64 encoded data)"
        }
    }
}
```








