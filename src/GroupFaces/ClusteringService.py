from sklearn.cluster import DBSCAN
from ..Models import Face, Group


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
    db = DBSCAN(eps=0.425, min_samples=1).fit(encodings)

    groups = {}  # type: dict[int, Group]

    for face, label in zip(faces, db.labels_):
        if label not in groups:
            groups[label] = Group()
        groups[label].add_face(face)

    groups = list(groups.values())

    # sort groups by size
    groups.sort(key=lambda g: len(g.faces), reverse=True)

    return groups
