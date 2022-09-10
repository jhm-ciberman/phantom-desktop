import cv2
import numpy as np

class DeblurFilter:
    """
    Performs Lucy-Richardson deconvolution on an image.
    """

    def __init__(self, image: np.ndarray) -> None:
        """
        Creates a new deblur filter.

        :param image: The image to deblur.
        """

        self._image = image
        self._blurRadius = 5
        self._blurIterations = 5

    def setBlurRadius(self, radius: int) -> None:
        """
        Sets the blur radius.

        :param radius: The blur radius.
        """

        self._blurRadius = radius

    def setBlurIterations(self, iterations: int) -> None:
        """
        Sets the blur iterations.

        :param iterations: The blur iterations.
        """

        self._blurIterations = iterations

    def process(self) -> np.ndarray:
        """
        Performs Lucy-Richardson deconvolution on the image.

        :return: The deblurred image.
        """
            
        # Convert the image to float32
        image = self._image.astype(np.float32)

        # Create a Gaussian kernel
        kernel = cv2.getGaussianKernel(self._blurRadius, -1)
        kernel = kernel * kernel.T

        # Create a box filter
        boxFilter = np.ones((self._blurRadius, self._blurRadius), np.float32) / (self._blurRadius * self._blurRadius)

        # Convolve the image with the Gaussian kernel
        blurred = cv2.filter2D(image, -1, kernel, borderType=cv2.BORDER_CONSTANT)

        # Create a blurred image
        deblurred = np.copy(blurred)

        # Perform Lucy-Richardson deconvolution
        for i in range(self._blurIterations):
            # Calculate the difference between the blurred image and the deblurred image
            difference = blurred - cv2.filter2D(deblurred, -1, kernel, borderType=cv2.BORDER_CONSTANT)

            # Calculate the deconvolution
            deconvolution = cv2.filter2D(difference, -1, boxFilter, borderType=cv2.BORDER_CONSTANT)

            # Update the deblurred image
            deblurred += deconvolution

        # Return the deblurred image
        return deblurred
