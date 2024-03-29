import numpy as np
import math
import unittest

from imageio.v3 import imread

from util import preprocess_ncc, compute_ncc, project, unproject_corners, \
    pyrdown, pyrup

from scipy.sparse.linalg import lsqr

class TestP3(unittest.TestCase):

    def test_preprocess_ncc_zeros(self):
        ncc_size = 5

        image = np.zeros((2 * ncc_size - 1, 2 * ncc_size - 1, 3), dtype=np.float32)
        n = preprocess_ncc(image, ncc_size)

        assert n.shape == (2 * ncc_size - 1, 2 * ncc_size -
                           1, 3 * ncc_size * ncc_size)
        assert (np.abs(n) < 1e-6).all()

    def test_preprocess_ncc_delta(self):
        ncc_size = 5
        ncc_half = int(ncc_size / 2)

        image = np.zeros((2 * ncc_size - 1, 2 * ncc_size - 1, 3), dtype=np.float32)
        image[ncc_size - 1, ncc_size - 1, :] = ncc_size ** 2
        n = preprocess_ncc(image, ncc_size)

        correct = np.zeros((2 * ncc_size - 1, 2 * ncc_size - 1,
                            3 * ncc_size ** 2), dtype=np.float32)
        correct[ncc_half:-ncc_half, ncc_half:-ncc_half, :] = - \
            1.0 / (ncc_size * math.sqrt(3 * ncc_size ** 2 - 3))
        x = (ncc_size ** 2 - 1.0) / (ncc_size * math.sqrt(3 * ncc_size ** 2 - 3))
        for i in range(ncc_size):
            for j in range(ncc_size):
                correct[-(i + ncc_half + 1), -(j + ncc_half + 1), ncc_size **
                        2 * 0 + ncc_size * i + j] = x
                correct[-(i + ncc_half + 1), -(j + ncc_half + 1), ncc_size **
                        2 * 1 + ncc_size * i + j] = x
                correct[-(i + ncc_half + 1), -(j + ncc_half + 1), ncc_size **
                        2 * 2 + ncc_size * i + j] = x
        # np.set_printoptions(threshold=np.nan)
        # print(n[np.nonzero(n)]-correct[np.nonzero(correct)])

        assert n.shape == (2 * ncc_size - 1, 2 * ncc_size -
                           1, 3 * ncc_size * ncc_size)
        #for i in range(n.shape[-1]):
        diff = np.abs(n-correct)
        ndiff = n[diff>1e-6]
        cdiff = correct[diff>1e-6]
        for i in range(len(ndiff)):
            print(ndiff[i], cdiff[i])
            #print(np.abs(n-correct)[:,:,i])
        assert (np.abs(n - correct) < 1e-6).all()
        # assert (abs==basd).all()


    def test_preprocess_ncc_uniform(self):
        ncc_size = 5

        image = np.ones((2 * ncc_size - 1, 2 * ncc_size - 1, 3), dtype=np.float32)
        n = preprocess_ncc(image, ncc_size)

        assert n.shape == (2 * ncc_size - 1, 2 * ncc_size -
                           1, 3 * ncc_size * ncc_size)
        assert (np.abs(n[ncc_size - 1, ncc_size - 1, :]) < 1e-6).all()


    def test_correlated_ncc(self):
        ncc_size = 5
        ncc_half = int(ncc_size / 2)

        image1 = np.random.random((2 * ncc_size - 1, 2 * ncc_size - 1, 3))
        image2 = image1

        n1 = preprocess_ncc(image1, ncc_size)
        n2 = preprocess_ncc(image2, ncc_size)

        ncc = compute_ncc(n1, n2)

        assert (np.abs(ncc[:ncc_half, :]) < 1e-5).all()
        assert (np.abs(ncc[-ncc_half:, :]) < 1e-5).all()
        assert (np.abs(ncc[:, :ncc_half]) < 1e-5).all()
        assert (np.abs(ncc[:, -ncc_half:]) < 1e-5).all()
        assert (
            np.abs(ncc[ncc_half:-ncc_half, ncc_half:-ncc_half] - 1) < 1e-5).all()


    def test_anticorrelated_ncc(self):
        ncc_size = 5
        ncc_half = int(ncc_size / 2)

        image1 = np.random.random((2 * ncc_size - 1, 2 * ncc_size - 1, 3))
        image2 = -image1

        n1 = preprocess_ncc(image1, ncc_size)
        n2 = preprocess_ncc(image2, ncc_size)

        ncc = compute_ncc(n1, n2)

        assert (np.abs(ncc[:ncc_half, :]) < 1e-5).all()
        assert (np.abs(ncc[-ncc_half:, :]) < 1e-5).all()
        assert (np.abs(ncc[:, :ncc_half]) < 1e-5).all()
        assert (np.abs(ncc[:, -ncc_half:]) < 1e-5).all()
        assert (
            np.abs(ncc[ncc_half:-ncc_half, ncc_half:-ncc_half] - -1) < 1e-5).all()


    def test_zero_ncc(self):
        ncc_size = 5

        image1 = np.zeros(
            (2 * ncc_size - 1, 2 * ncc_size - 1, 3), dtype=np.float32)
        image2 = image1

        n1 = preprocess_ncc(image1, ncc_size)
        n2 = preprocess_ncc(image2, ncc_size)

        ncc = compute_ncc(n1, n2)

        assert (np.abs(ncc) < 1e-6).all()


    def test_offset_ncc(self):
        ncc_size = 5

        image1 = np.random.random((2 * ncc_size - 1, 2 * ncc_size - 1, 3))
        image2 = image1 + 2

        n1 = preprocess_ncc(image1, ncc_size)
        n2 = preprocess_ncc(image2, ncc_size)

        ncc = compute_ncc(n1, n2)

        assert ncc.shape == (2 * ncc_size - 1, 2 * ncc_size - 1)
        assert (np.abs(ncc[ncc_size, ncc_size] - 1) < 1e-6).all()


    def test_scale_ncc(self):
        ncc_size = 5
        ncc_half = int(ncc_size / 2)

        image1 = np.random.random((2 * ncc_size - 1, 2 * ncc_size - 1, 3))
        image2 = image1 * 2

        n1 = preprocess_ncc(image1, ncc_size)
        n2 = preprocess_ncc(image2, ncc_size)

        ncc = compute_ncc(n1, n2)

        assert ncc.shape == (2 * ncc_size - 1, 2 * ncc_size - 1)
        assert (np.abs(ncc[:ncc_half, :]) < 1e-5).all()
        assert (np.abs(ncc[-ncc_half:, :]) < 1e-5).all()
        assert (np.abs(ncc[:, :ncc_half]) < 1e-5).all()
        assert (np.abs(ncc[:, -ncc_half:]) < 1e-5).all()
        assert (
            np.abs(ncc[ncc_half:-ncc_half, ncc_half:-ncc_half] - 1) < 1e-5).all()


    def test_offset_and_scale_ncc(self):
        ncc_size = 5
        ncc_half = int(ncc_size / 2)

        image1 = np.random.random((2 * ncc_size - 1, 2 * ncc_size - 1, 3))
        image2 = image1 * 2 + 3

        n1 = preprocess_ncc(image1, ncc_size)
        n2 = preprocess_ncc(image2, ncc_size)

        ncc = compute_ncc(n1, n2)

        assert ncc.shape == (2 * ncc_size - 1, 2 * ncc_size - 1)
        assert (np.abs(ncc[:ncc_half, :]) < 1e-6).all()
        assert (np.abs(ncc[-ncc_half:, :]) < 1e-6).all()
        assert (np.abs(ncc[:, :ncc_half]) < 1e-6).all()
        assert (np.abs(ncc[:, -ncc_half:]) < 1e-6).all()
        assert (
            np.abs(ncc[ncc_half:-ncc_half, ncc_half:-ncc_half] - 1) < 1e-6).all()


    def test_project_Rt_identity_centered(self):
        width = 1
        height = 1
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = np.identity(3)

        point = np.array(((0, 0, 1), ), dtype=np.float32).reshape((1, 1, 3))

        projection = project(K, Rt, point)

        assert projection.shape == (1, 1, 2)
        assert projection[0][0][0] == width / 2.0
        assert projection[0][0][1] == height / 2.0


    def test_project_Rt_identity_20x10(self):
        width = 20
        height = 10
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = np.identity(3)

        point = np.array(height * width * [[0, 0, 1]], dtype=np.float32).reshape(
            (height, width, 3))

        projection = project(K, Rt, point)

        assert projection.shape == (height, width, 2)
        assert (projection[:, :, 0] == width / 2.0).all()
        assert (projection[:, :, 1] == height / 2.0).all()


    def test_project_Rt_identity_xoff(self):
        width = 1
        height = 1
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = np.identity(3)

        point = np.array(((0.5, 0, 1), ), dtype=np.float32).reshape((1, 1, 3))

        projection = project(K, Rt, point)

        assert projection.shape == (1, 1, 2)
        assert projection[0][0][0] == width
        assert projection[0][0][1] == height / 2.0


    def test_project_Rt_identity_yoff(self):
        width = 1
        height = 1
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = np.identity(3)

        point = np.array(((0, 0.5, 1), ), dtype=np.float32).reshape((1, 1, 3))

        projection = project(K, Rt, point)

        assert projection.shape == (1, 1, 2)
        assert projection[0][0][0] == width / 2.0
        assert projection[0][0][1] == height


    def test_project_Rt_identity_upperleft(self):
        width = 1
        height = 1
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = np.identity(3)

        point = np.array(((-0.5, -0.5, 1), ), dtype=np.float32).reshape((1, 1, 3))

        projection = project(K, Rt, point)

        assert projection.shape == (1, 1, 2)
        assert projection[0][0][0] == 0
        assert projection[0][0][1] == 0


    def test_project_Rt_rot90_upperleft(self):
        width = 1
        height = 1
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[0, 1] = 1
        Rt[1, 0] = -1
        Rt[2, 2] = 1

        point = np.array(((-0.5, -0.5, 1), ), dtype=np.float32).reshape((1, 1, 3))

        projection = project(K, Rt, point)
        assert projection.shape == (1, 1, 2)
        assert projection[0][0][0] == 0
        assert projection[0][0][1] == height


    def test_project_Rt_rot180_upperleft(self):
        width = 1
        height = 1
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[0, 0] = -1
        Rt[1, 1] = -1
        Rt[2, 2] = 1

        point = np.array(((-0.5, -0.5, 1), ), dtype=np.float32).reshape((1, 1, 3))

        projection = project(K, Rt, point)

        assert projection.shape == (1, 1, 2)
        assert projection[0][0][0] == width
        assert projection[0][0][1] == height


    def test_project_unproject_Rt_identity(self):
        width = 20
        height = 10
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = np.identity(3)

        depth = 1
        point = unproject_corners(K, width, height, depth, Rt)

        projection = project(K, Rt, point)

        assert projection.shape == (2, 2, 2)

        assert np.abs(projection[0, 0, 0]) < 1e-5
        assert np.abs(projection[0, 0, 1]) < 1e-5

        assert np.abs(projection[0, 1, 0] - (width-1)) < 1e-5
        assert np.abs(projection[0, 1, 1]) < 1e-5

        assert np.abs(projection[1, 0, 0]) < 1e-5
        assert np.abs(projection[1, 0, 1] - (height-1)) < 1e-5

        assert np.abs(projection[1, 1, 0] - (width-1)) < 1e-5
        assert np.abs(projection[1, 1, 1] - (height-1)) < 1e-5


    def test_project_unproject_Rt_identity_randdepth(self):
        width = 20
        height = 10
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = np.identity(3)

        depth = 2
        point = unproject_corners(K, width, height, depth, Rt)

        projection = project(K, Rt, point)

        assert projection.shape == (2, 2, 2)

        assert np.abs(projection[0, 0, 0]) < 1e-5
        assert np.abs(projection[0, 0, 1]) < 1e-5

        assert np.abs(projection[0, 1, 0] - (width-1)) < 1e-5
        assert np.abs(projection[0, 1, 1]) < 1e-5

        assert np.abs(projection[1, 0, 0]) < 1e-5
        assert np.abs(projection[1, 0, 1] - (height-1)) < 1e-5

        assert np.abs(projection[1, 1, 0] - (width-1)) < 1e-5
        assert np.abs(projection[1, 1, 1] - (height-1)) < 1e-5


    def test_project_unproject_Rt_random_randdepth(self):
        width = 20
        height = 10
        f = 1

        K = np.array((
                     (f, 0, width / 2.0),
                     (0, f, height / 2.0),
                     (0, 0, 1)
                     ))

        A = np.random.random((3, 3))
        U, S, Vt = np.linalg.svd(A)
        R = U.dot(Vt)

        Rt = np.zeros((3, 4), dtype=np.float32)
        Rt[:, :3] = R
        Rt[:, 3] = np.random.random(3)

        depth = 2
        point = unproject_corners(K, width, height, depth, Rt)

        projection = project(K, Rt, point)

        assert projection.shape == (2, 2, 2)

        assert np.abs(projection[0, 0, 0]) < 1e-5
        assert np.abs(projection[0, 0, 1]) < 1e-5

        assert np.abs(projection[0, 1, 0] - (width-1)) < 1e-5
        assert np.abs(projection[0, 1, 1]) < 1e-5

        assert np.abs(projection[1, 0, 0]) < 1e-5
        assert np.abs(projection[1, 0, 1] - (height-1)) < 1e-5

        assert np.abs(projection[1, 1, 0] - (width-1)) < 1e-5
        assert np.abs(projection[1, 1, 1] - (height-1)) < 1e-5


    def test_preprocess_ncc_full(self):
        ncc_size = 5
        image = imread('test_materials/fabrics.png').astype(np.float32) / 255.0
        result = preprocess_ncc(image, ncc_size)
        correct = np.load('test_materials/fabrics_normalized.npy')
        assert (np.abs(result - correct) < 1e-5).all()


    def test_ncc_full_identity(self):
        ncc_size = 5
        ncc_half = int(ncc_size / 2)

        normalized = np.load('test_materials/fabrics_normalized.npy')

        ncc = compute_ncc(normalized, normalized)

        assert ncc.shape == normalized.shape[:2]
        assert (np.abs(ncc[:ncc_half, :]) < 1e-5).all()
        assert (np.abs(ncc[-ncc_half:, :]) < 1e-5).all()
        assert (np.abs(ncc[:, :ncc_half]) < 1e-5).all()
        assert (np.abs(ncc[:, -ncc_half:]) < 1e-5).all()
        assert (
            np.abs(ncc[ncc_half:-ncc_half, ncc_half:-ncc_half] - 1) < 1e-5).all()


    def test_ncc_full_offset(self):
        ncc_size = 5

        image = imread('test_materials/justinpic_c.png').astype(np.float32) / 255.0

        split = int(image.shape[1] / 2)
        left = image[:, :split, :]
        right = image[:, split:, :]

        n1 = preprocess_ncc(left, ncc_size)
        n2 = preprocess_ncc(right, ncc_size)

        result = compute_ncc(n1, n2)

        correct = np.load('test_materials/justin_ncc.npy')

        assert result.shape == n1.shape[:2]
        assert result.shape == n2.shape[:2]
        assert (np.abs(result - correct) < 1e-5).all()


    def test_ncc_full_shapes(self):
        ncc_size = 5

        image1 = imread('test_materials/ncc1.png').astype(np.float32) / 255.0
        image2 = imread('test_materials/ncc2.png').astype(np.float32) / 255.0

        n1 = preprocess_ncc(image1, ncc_size)
        n2 = preprocess_ncc(image2, ncc_size)

        result = compute_ncc(n1, n2)

        correct = np.load('test_materials/ncc.npy')

        assert result.shape == n1.shape[:2]
        assert result.shape == n2.shape[:2]
        assert (np.abs(result - correct) < 1e-5).all()


if __name__ == '__main__':
    unittest.main()

