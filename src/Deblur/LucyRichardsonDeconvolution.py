import threading
from typing import Callable, Tuple
import cv2
import numpy as np


class CancellationToken:
    def __init__(self):
        """Initializes a new instance of the CancellationToken class."""
        self._is_cancelled = False

    def cancel(self):
        """Signals the task in progress to be cancelled."""
        self._is_cancelled = True

    @property
    def is_cancelled(self):
        """Returns True if the task in progress should be cancelled."""
        return self._is_cancelled


class LucyRichardsonDeconvolution:
    """
    Performs Lucy-Richardson deconvolution on an image. This class is optimized
    for generating intermediate results for the deconvolution process for UI applications.
    """

    def __init__(
            self, image: np.ndarray, psf: np.ndarray, num_iter: int = 50,
            clip: bool = True, filter_epsilon: float = None):
        """
        Initializes a new instance of the LucyRichardsonDeconvolution class.

        Args:
            image: cv2/np.ndarray The image to deconvolve.
            psf: cv2/np.ndarray The point spread function to use. You can use
                the PointSpreadFunction class to generate some common PSFs.
            num_iter: int The number of iterations to perform.
            clip: bool Whether to clip the image to the range [0, 1].
            filter_epsilon: float The epsilon value to use for the filter. If None, no filter is used.
        """
        self.num_iter: int = num_iter
        self.clip: bool = clip
        self.filter_epsilon: float = filter_epsilon
        self._epsilon = 1e-12
        self._original_dtype = image.dtype
        if image.dtype == np.uint8:
            self._image = image.astype(np.float32, copy=True) / 255
        else:
            self._image = image.astype(np.float32, copy=True)
        self._psf = psf.astype(np.float32, copy=True)
        self._psf_mirror = np.flip(psf)
        self._im_deconv = np.full(self._image.shape, 0.5, dtype=np.float32)
        self._conv = self._im_deconv.copy()  # Used for intermediate results

    def _run_iteration(self):
        """
        Performs a single iteration of the Lucy-Richardson algorithm.
        """
        cv2.filter2D(self._im_deconv, -1, self._psf_mirror, dst=self._conv,
                     delta=self._epsilon, borderType=cv2.BORDER_REPLICATE)
        if self.filter_epsilon:
            relative_blur = np.where(self._conv < self.filter_epsilon, 0, self._image / self._conv)
        else:
            relative_blur = self._image / self._conv
        cv2.filter2D(relative_blur, -1, self._psf, dst=self._conv, borderType=cv2.BORDER_REPLICATE)
        self._im_deconv *= self._conv

    def _clip(self):
        """
        Clips the image to the range [0, 1].
        """
        self._im_deconv[self._im_deconv > 1] = 1
        self._im_deconv[self._im_deconv < -1] = -1

    def run(self, on_progress: Callable[[int, int], None] = None, token: CancellationToken = None) -> np.ndarray:
        """
        Performs Richardson-Lucy deconvolution on an image.

        Args:
            on_progress: A callback function that is called after each iteration.
                The function must have the following signature:
                on_progress(current: int, total: int)
            token: A CancellationToken that can be used to cancel the deconvolution.

        Returns:
            The deconvolved image using the Lucy-Richardson algorithm.
        """
        token = token or CancellationToken()

        for i in range(self.num_iter):
            self._run_iteration()

            if token.is_cancelled:
                break

            if on_progress:
                on_progress(i, self.num_iter)

        if self.clip:
            self._clip()

        # Convert back to uint8 if necessary
        if self._original_dtype == np.uint8:
            return (self._im_deconv * 255).astype(np.uint8)
        else:
            return self._im_deconv

    def run_step(self) -> np.ndarray:
        """
        Performs a single iteration of the Lucy-Richardson algorithm.

        Returns:
            The deconvolved image after a single iteration.
        """
        self._run_iteration()
        if self.clip:
            self._clip()

        return self._im_deconv

    @property
    def image(self) -> np.ndarray:
        """
        Gets the image that is being deconvolved.
        """
        return self._image

    @property
    def psf(self) -> np.ndarray:
        """
        Gets the PSF that is being used.
        """
        return self._psf

    @property
    def deconvolved(self) -> np.ndarray:
        """
        Gets the deconvolved image.
        """
        return self._im_deconv


class PointSpreadFunction:
    """
    A helper class for generating point spread functions.
    All generated PSFs are normalized meaning that the sum of all values is 1.
    """

    @staticmethod
    def gaussian(sigma: float, size: int = None) -> np.ndarray:
        """
        Creates a Gaussian point spread function.

        Args:
            sigma: float The standard deviation of the Gaussian
            size: int The size of the PSF. If None, the size is calculated from sigma.

        Returns:
            The PSF
        """
        if sigma <= 0:
            raise ValueError('sigma must be greater than 0')

        if size is None:
            size = int(2 * np.ceil(3 * sigma) + 1)

        if size < 1:
            raise ValueError('Size must be greater than 0')

        x = np.arange(0, size, 1, float)
        y = x[:, np.newaxis]
        x0 = y0 = size // 2
        pfs = np.exp(-((x - x0) ** 2 + (y - y0) ** 2) / (2 * sigma ** 2))
        return pfs / np.sum(pfs)

    @staticmethod
    def box_blur(size: int) -> np.ndarray:
        """
        Creates a box blur point spread function.

        Args:
            size: int The size of the box blur

        Returns:
            The PSF
        """
        if size < 1:
            raise ValueError('Size must be greater than 0')

        return np.ones((size, size)) / (size * size)

    @staticmethod
    def disk_blur(size: int) -> np.ndarray:
        """
        Creates a disk blur point spread function.

        Args:
            size: int The size of the disk blur. This is the diameter of the disk.

        Returns:
            The PSF
        """
        if size < 1:
            raise ValueError('Size must be greater than 0')

        psf = np.zeros((size, size))
        center = size // 2
        for i in range(size):
            for j in range(size):
                if np.sqrt((i - center) ** 2 + (j - center) ** 2) <= center:
                    psf[i, j] = 1
        return psf / psf.sum()

    @staticmethod
    def motion_blur(angle: float, length: int, width: int = 1) -> np.ndarray:
        """
        Creates a motion blur point spread function.

        Args:
            angle: float The angle of the motion blur in degrees
            length: int The length of the motion blur
            width: int The width of the motion blur

        Returns:
            The PSF
        """
        # 1. Initialize the canvas to (length + 2) x (length + 2)
        # 2. Generate a line of ones with the specified length and width in the center of the canvas
        # 3. Rotate the line by the specified angle
        # 4. Normalize the PSF

        if length < 1:
            raise ValueError('Length must be greater than 0')

        if width < 1:
            raise ValueError('Width must be greater than 0')

        size = length + 4
        psf = np.zeros((size, size))
        center = size // 2
        psf[center - width // 2:center + width // 2 + 1, center - length // 2:center + length // 2 + 1] = 1
        psf = PointSpreadFunction._rotate(psf, angle)
        psf = PointSpreadFunction._trim_padding(psf)
        return psf / psf.sum()

    @staticmethod
    def _rotate(image: np.ndarray, angle: float) -> np.ndarray:
        """
        Rotates an image by the specified angle.

        Args:
            image: The image to rotate
            angle: The angle to rotate the image by in degrees

        Returns:
            The rotated image
        """
        image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
        return cv2.warpAffine(image, rot_mat, image.shape[1::-1], flags=cv2.INTER_LINEAR)

    @staticmethod
    def _trim_padding(image: np.ndarray) -> np.ndarray:
        """
        Trims the padding from an image. The padding is any area that is all zeros
        in each side of the image (top, bottom, left, right).

        Args:
            image: The image to trim the padding from

        Returns:
            The trimmed image
        """
        non_zero = np.nonzero(image)
        return image[np.min(non_zero[0]):np.max(non_zero[0]) + 1, np.min(non_zero[1]):np.max(non_zero[1]) + 1]

    @staticmethod
    def to_grayscale(psf: np.ndarray) -> np.ndarray:
        """
        Converts a PSF to a grayscale image with values in the range [0, 255] as uint8.

        Args:
            psf: np.ndarray The color PSF

        Returns:
            The grayscale PSF as a uint8 image
        """
        psf = psf / psf.max()
        return (psf * 255).astype(np.uint8)


class ProgressiveDeblurTask:
    """
    The ProgressiveDeblurrer generates succesive results of an image for preview in a UI application.

    Given a preview_size (W,H), the class will generate asynchronusly a number of preview images.
    For example, if 4 cycles are used, the class will first generate a preview image of (W/8, H/8),
    then (W/4, H/4), (W/2, H/2) and finally (W, H).

    The process will run in a separate thread and the results can be retrieved using the preview property
    or by subscribing to the on_preview callback.
    """

    def __init__(
            self,
            image: np.ndarray,
            preview_size: Tuple[int, int],
            psf: np.ndarray,
            *,
            num_iter: int = 10,
            cycles: int = None,
            on_preview: Callable[[np.ndarray, int, int], None] = None,
            on_progress: Callable[[float], None] = None,
            on_finished: Callable[[], None] = None):
        """
        Creates a new instance of the ProgressiveDeblurrer class.

        Args:
            image: np.ndarray The image to deblur
            preview_size: Tuple[int, int] The size of the preview image (W, H)
            psf: np.ndarray The point spread function
            num_iter: int The number of iterations to perform.
            cycles: int The number of cycles to perform. If None, the number of cycles is calculated from the preview size.
            on_preview: Callable[[np.ndarray, int, int], None] A callback that is called when a new preview image is generated.
                The callback receives the preview image, the current cycle and the total number of cycles.
            on_progress: Callable[[float], None] A callback that is called when the progress of the preview generation changes.
                The callback receives a value between 0 and 1.
            on_finished: Callable[[], None] A callback that is called when the preview generation is finished.
        """
        self._image = image
        self._preview_size = preview_size
        self._psf = psf
        self._num_iter = num_iter

        if cycles is None:
            skip_sizes = 5  # skip the first 5 sizes because they are too small to be useful
            cycles = int(np.log2(min(preview_size))) - skip_sizes
            cycles = max(1, cycles)

        self._cycles = cycles

        self._preview = None
        self._token = CancellationToken()

        self._cycle_index = 0  # in the range [0, 3]
        self._scales = [1 / (2 ** i) for i in range(cycles)]
        self._scales.reverse()

        # Weight factors used to weight the progress of the different preview sizes
        total_weight = 0
        for i in range(cycles):
            total_weight += 2 ** i
        self._weights = [2 ** i / total_weight for i in range(cycles)]

        self._progresses = [0] * cycles

        self._on_preview = on_preview
        self._on_progress = on_progress
        self._on_finished = on_finished

        self._thread = threading.Thread(target=self._run, daemon=True)

    @property
    def preview(self) -> np.ndarray:
        """
        Gets the current preview image.
        """
        return self._preview

    def start(self):
        """
        Starts the preview generation.
        """
        self._thread.start()

    def cancel(self):
        """
        Cancels the preview generation.
        """
        self._token.cancel()

    def _run_cycle(self):
        scale = self._scales[self._cycle_index]

        # If the pfs size or image size after scaling is too small, skip this cycle
        pfs_w, pfs_h = self._psf.shape[:2]
        img_w, img_h = self._image.shape[:2]
        if pfs_w * scale < 1 or pfs_h * scale < 1 or img_w * scale < 1 or img_h * scale < 1:
            return

        scaled_psf = cv2.resize(self._psf, (0, 0), fx=scale, fy=scale)
        scaled_image = cv2.resize(self._image, (0, 0), fx=scale, fy=scale)
        deblur = LucyRichardsonDeconvolution(scaled_image, scaled_psf, self._num_iter)
        result = deblur.run(self._on_progress_cycle, token=self._token)

        if self._token.is_cancelled:
            return

        self._preview = cv2.resize(result, self._preview_size)

        if self._on_preview is not None:
            self._on_preview(self._preview, self._cycle_index, self._cycles)

    def _on_progress_cycle(self, current: int, total: int):
        w = self._weights[self._cycle_index]
        self._progresses[self._cycle_index] = w * current / total

        if self._on_progress is not None:
            self._on_progress(sum(self._progresses))

    def _run(self):
        for i in range(self._cycles):
            self._cycle_index = i
            self._run_cycle()

            if self._token.is_cancelled:
                return

        if self._on_finished is not None:
            self._on_finished()
