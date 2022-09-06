import cv2
import numpy as np

class PerspectiveTransform:
    """
    Class that offers services for transforming the perspective of an Image
    """
    @staticmethod
    def basic_transform(src_image: cv2.Mat, dst_image: cv2.Mat, src_points: list[(int, int)], linear_interpolation: bool = True) -> None:
        """
        Transforms the perspective of a source image to a destination image.
        The source and destination buffers should be in BGRA format.

        Args:
            src_image (cv2.Mat): The source image buffer
            dst_image (cv2.Mat): The destination image buffer
            src_points (list[(int, int)]): A list of 4 points in the source image
            linear_interpolation (bool): Whether to use linear interpolation or not 
        """
        if len(src_points) != 4:
            raise ValueError("src_points must have exactly 4 points")

        # Get the size of the destination image
        dst_w, dst_h = dst_image.shape[1], dst_image.shape[0]

        src_points = np.float32(src_points)
        dst_points = np.float32([[0, 0], [dst_w, 0], [dst_w, dst_h], [0, dst_h]])

        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        flags = cv2.INTER_LINEAR if linear_interpolation else cv2.INTER_NEAREST
        return cv2.warpPerspective(src_image, matrix, (dst_w, dst_h), dst_image, flags=flags)