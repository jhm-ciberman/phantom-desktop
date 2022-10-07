import numpy as np
from sklearn.cluster import DBSCAN
from ..Models import Face, Group

cluster_max_distance = 0.425

nearest_candidate_max_distance = 0.6


def cluster(faces: list[Face]) -> list[Group]:
    """
    Clusters the faces using the DBSCAN algorithm.

    Args:
        faces (list[Face]): The faces to cluster.

    Returns:
        list[Group]: The groups of faces.
    """
    encodings = []  # flat list of encodings

    for face in faces:
        encodings.append(face.encoding)

    # Original values from phantom: eps=0.475, min_samples=2
    # I tuned them to have more groups because I think it's easier in the UI
    # to combine two groups than to split one face by face.
    # min_samples=1 because I want to have groups with only one face.
    db = DBSCAN(eps=cluster_max_distance, min_samples=1).fit(encodings)

    groups_by_label = {}  # type: dict[int, Group]

    for face, label in zip(faces, db.labels_):
        if label not in groups_by_label:
            groups_by_label[label] = Group()
        groups_by_label[label].add_face(face)

    groups = list(groups_by_label.values())

    # sort groups by size
    groups.sort(key=lambda g: len(g.faces), reverse=True)

    for group in groups:
        group.recompute_centroid()

    return groups


def find_best_group(face: Face, groups: list[Group]) -> Group:
    """
    Finds the best group for the face.

    Args:
        face (Face): The face to find the best group for.
        groups (list[Group]): The groups to search in.

    Returns:
        Group: The best group.
    """
    if face.encoding is None:
        raise ValueError("Face has no encoding.")

    best_group = None
    best_distance = np.inf

    for group in groups:
        if group.centroid is None:
            group.recompute_centroid()

        # Compute the distance between the face and the group centroid. (np.array)
        centroid = group.centroid
        encoding = face.encoding
        distance = np.linalg.norm(centroid - encoding)

        if distance < best_distance:
            best_group = group
            best_distance = distance

    return best_group


def find_nearest_groups(groups: list[Group]) -> tuple[Group, Group]:
    """
    Finds the two nearest groups.

    Args:
        groups (list[Group]): The groups to search in.

    Returns:
        tuple[Group, Group]: The two nearest groups.
    """
    best_distance = np.inf
    best_groups = None

    # O(n^2) algorithm, but n is small (usually < 100)
    for group1 in groups:
        for group2 in groups:
            if group1 == group2:
                continue

            if group1.centroid is None:
                group1.recompute_centroid()
            if group2.centroid is None:
                group2.recompute_centroid()

            distance = np.linalg.norm(group1.centroid - group2.centroid)

            if distance > nearest_candidate_max_distance:
                continue  # too far, the face is probably not the same person

            if distance < best_distance:
                best_distance = distance
                best_groups = (group1, group2)

    return best_groups
