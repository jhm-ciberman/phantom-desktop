from math import log2
from queue import Queue

import cv2
import numpy as np
from LucyRichardsonDeconvolution import (PointSpreadFunction,
                                         ProgressiveDeblurTask)

if __name__ == '__main__':
    # Config:
    image_path = 'test_images/lena_blur_10.png'
    sigma = 11
    num_iter = 200
    preview_size = (512, 512)
    psf_preview_scale = 4
    cycles = max(1, int(log2(preview_size[0]) - 5))
    last_cycle_time = 0

    # Load image:
    image = cv2.imread(image_path)

    psf = PointSpreadFunction.gaussian(sigma)

    cv2.imshow('Image', image)

    preview_psf = PointSpreadFunction.normalize(psf, 0, 255).astype(np.uint8)
    preview_psf = cv2.resize(preview_psf, (preview_psf.shape[1] * psf_preview_scale, preview_psf.shape[0] * psf_preview_scale))
    cv2.imshow('psf', preview_psf)

    queue = Queue()

    def on_preview(preview: np.ndarray, current: int, total: int):
        queue.put(preview)

    def on_progress(progress: float):
        print(f'Progress: {progress * 100:.2f}%')

    def on_finished():
        queue.put(None)
        print('Finished')

    task = ProgressiveDeblurTask(
            image, preview_size, psf, num_iter=num_iter, cycles=cycles,
            on_preview=on_preview, on_progress=on_progress, on_finished=on_finished)

    task.start()

    while True:
        key = cv2.waitKey(1)
        if key == 27:
            break

        if not queue.empty():
            preview = queue.get()
            if preview is None:
                break
            cv2.imshow('Preview', preview)

    cv2.waitKey(0)
    cv2.destroyAllWindows()
