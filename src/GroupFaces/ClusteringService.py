from dataclasses import dataclass
import numpy as np
from sklearn.cluster import DBSCAN
from ..Models import Face, Group

cluster_eps = 0.425

merging_oportunity_max_distance = 0.5


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
    db = DBSCAN(eps=cluster_eps, min_samples=1).fit(encodings)

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


@dataclass(frozen=True, slots=True)
class MergeOportunity:
    """Represents a pair of groups that are close to each other."""
    group1: Group
    """The first group."""
    group2: Group
    """The second group."""
    distance: float
    """The distance between the two groups."""

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, MergeOportunity):
            return False
        return self.group1 == __o.group1 and self.group2 == __o.group2

    def __hash__(self) -> int:
        return hash((self.group1, self.group2))


def find_merge_oportunities(
        groups: list[Group],
        ignored_oportunities: list[MergeOportunity] = None,
        max_oportunities: int = 10) -> list[MergeOportunity]:
    """
    Finds a list of pairs of groups that are close to each other. The list is sorted by distance.
    Duplicate pairs are removed.

    Args:
        groups (list[Group]): The groups to search in.
        max_oportunities (int, optional): The maximum number of oportunities to find. Defaults to 10.

    Returns:
        list[MergeOportunity]: The list of pairs of groups that are close to each other.
    """
    pairs = []
    ignored = ignored_oportunities or []

    for group in groups:
        if group.centroid is None:
            group.recompute_centroid()

    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            group1 = groups[i]
            group2 = groups[j]

            if group1 in group2.dont_merge_with:
                continue

            centroid1 = group1.centroid
            centroid2 = group2.centroid
            distance = np.linalg.norm(centroid1 - centroid2)

            if distance < merging_oportunity_max_distance:
                oportunity = MergeOportunity(group1, group2, distance)
                if oportunity not in ignored:
                    pairs.append(oportunity)

    pairs.sort(key=lambda p: p.distance)

    return pairs[:max_oportunities]
