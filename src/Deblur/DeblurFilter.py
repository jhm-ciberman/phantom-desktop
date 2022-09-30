import cv2
import numpy as np


# Source: https://github.com/bconstanzo/phantom/blob/f48908920b9fe9282043015f8dd85b1c1160ec84/phantom/enhance.py
class DeblurFilter:
    """
    Performs Lucy-Richardson deconvolution on an image.
    """

    @staticmethod
    def _clip(img: np.ndarray, lower: float, upper: float) -> np.ndarray:
        """
        Clips an image in between two bounds.

        Args:
            img: cv2/np.ndarray image
            lower: lower bound, usually 0
            higher: upper bound, either 255 for uint8 images or 1.0 for floats

        Returns:
            The clipped image
        """
        return np.maximum(lower, np.minimum(img, upper))

    @staticmethod
    def lucy_richardson_deconv(img: np.ndarray, num_iterations: int, sigmag: float) -> np.ndarray:
        """"
        Performs a Lucy-Richardson Deconvolution on the given image.

        Args:
            img: cv2/np.ndarray image
            num_iterations: The number of iterations to perform
            sigmag: The standard deviation of the gaussian blur kernel

        Returns:
            The deconvolved image
        """

        epsilon = 2.2204e-16
        win_size = 8 * sigmag + 1   # Window size of PSF

        dtype = img.dtype

        if img.dtype == "uint8":
            clip_max = 255
            clip_min = 0
        elif img.dtype == "uint16":
            clip_max = 65535
            clip_min = 0
        else:
            # we must have a float here
            clip_max = 1.0
            clip_min = 0.0

        # Initializations Numpy
        j1 = img.copy()
        j2 = img.copy()
        w_i = img.copy()
        im_r = img.copy()

        t1 = np.zeros(img.shape, dtype=np.float32)
        t2 = np.zeros(img.shape, dtype=np.float32)
        tmp1 = np.zeros(img.shape, dtype=np.float32)
        tmp2 = np.zeros(img.shape, dtype=np.float32)
        # size = (w, h, channels), grayscale -> channels = 1

        # Lucy - Rich.Deconvolution CORE
        lambda_ = 0
        for j in range(1, num_iterations):
            # gotta clean this up, maybe a warmup before the for-loop
            if j > 1:
                # calculation of lambda
                # https://docs.opencv.org/2.4/modules/core/doc/operations_on_arrays.html#multiply
                tmp1 = t1 * t2
                tmp2 = t2 * t2

                # https://docs.opencv.org/2.4/modules/core/doc/operations_on_arrays.html#sum
                lambda_ = cv2.sumElems(tmp1)[0] / (cv2.sumElems(tmp2)[0] + epsilon)

            # y = j1 + (lambda_ * (j1 - j2))
            y = j1 + np.multiply(lambda_, np.subtract(j1, j2))

            y[(y < 0)] = 0

            # applying Gaussian filter
            re_blurred = cv2.GaussianBlur(y, (int(win_size), int(win_size)), sigmag)
            re_blurred[(re_blurred <= 0)] = epsilon

            cv2.divide(w_i, re_blurred, im_r, 1, cv2.CV_64F)
            im_r = im_r + epsilon

            # applying Gaussian filter
            im_r = cv2.GaussianBlur(im_r, (int(win_size), int(win_size)), sigmag)

            # updates before the next iteration
            j2 = j1.copy()
            j1 = y * im_r
            t2 = t1.copy()
            t1 = j1 - y

        result = DeblurFilter._clip(j1.copy(), clip_min, clip_max)
        return result.astype(dtype)
