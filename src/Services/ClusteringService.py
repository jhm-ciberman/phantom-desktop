from sklearn.cluster import DBSCAN, KMeans
from sklearn import metrics
from time import perf_counter_ns
from src.Image import Face
import numpy as np


class Group:
    """
    Represents a group of faces.

    Attributes:
        centroid (numpy.ndarray): The centroid of the group.
        faces (list[Face]): The faces in the group.
        name (str): The name of the group.
    """

    def __init__(self, centroid: np.ndarray):
        """
        Initializes the Group class.

        Args:
            centroid (numpy.ndarray): The centroid of the group.
        """
        self.centroid = centroid
        self.faces = []  # type: list[Face]
        self.name = ""  # type: str


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

    db = DBSCAN(eps=0.475, min_samples=2).fit(encodings)

    # we can now approximate how many people are present...
    num_people = len(set(i for i in db.labels_ if i >= 0))

    """
    k_set = set()
    k_init = []
    for f, label in zip(encodings, db.labels_):
        if label < 0:
            continue
        if label in k_set:
            continue
        k_init.append(f)
        k_set.add(label)
    km = KMeans(init=np.array(k_init), n_clusters=num_people, n_init=1).fit(encodings)
    t2 = datetime.datetime.now()
    # now we group all the images for each cluster into a grid
    grid_images = defaultdict(list)
    grid_colors = defaultdict(list)
    grid_scores = defaultdict(list)
    count_outlier = 0
    s_scores = metrics.silhouette_samples([e.encoding for e in atlas.elements], db.labels_)
    for idx, (img, label, score) in enumerate(zip(face_images, db.labels_, s_scores)):
        if img is not None:
            #centroid = km.cluster_centers_[label]
            #distance = compare(centroid, faces[idx])
            distance = 0.5
            if distance < 0.9625:
                try:
                    grid_images[label].append(cv2.resize(img, C_GRID_SIZE))
                    grid_colors[label].append(lerp_color(score))
                    grid_scores[label].append(score)
                except cv2.error:
                    print(f"Raised -: {paths[images_x_faces[idx]]}")
                    pass
            else:
                print(f"Clustered face too far away from the centroid."
                      f"({label}_{count_outlier}, {distance})")
                try:
                    out = cv2.resize(img, C_GRID_SIZE)
                    cv2.imwrite(f"{output_folder_path}/outlier_grid_{label}_{count_outlier}.jpg", out)
                    count_outlier += 1
                except cv2.error:
                    pass

    print(f"Number of people found: {num_people}")
    print(f"DBSCAN took {t1 - t0}")
    print(f"KMeans took {t2 - t1}")
    return None
    """

    groups = []  # type: list[Group]

    for i in range(num_people):
        groups.append(Group(np.zeros(128)))

    for face, label in zip(faces, db.labels_):
        if label >= 0:
            groups[label].faces.append(face)

    return groups
