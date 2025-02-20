import pytest

import geomstats.backend as gs
from geomstats.geometry.discrete_curves import DiscreteCurves
from geomstats.geometry.euclidean import Euclidean
from geomstats.test.random import ShapeBundleRandomDataGenerator
from geomstats.test.vectorization import generate_vectorization_data
from geomstats.test_cases.geometry.base import LevelSetTestCase
from geomstats.test_cases.geometry.fiber_bundle import FiberBundleTestCase
from geomstats.vectorization import get_batch_shape


class ClosedDiscreteCurvesTestCase(LevelSetTestCase):
    def _get_srv_point(self, n_points=1):
        # TODO: move into data_generator?
        return DiscreteCurves(
            ambient_manifold=self.space.ambient_manifold,
            k_sampling_points=self.space.k_sampling_points,
        ).random_point(n_points)

    def _is_planar(self):
        is_euclidean = isinstance(self.space.ambient_manifold, Euclidean)
        return is_euclidean and self.space.ambient_manifold.dim == 2

    @pytest.mark.vec
    def test_projection_vec(self, n_reps, atol):
        if not self._is_planar():
            return

        super().test_projection_vec(n_reps, atol)

    @pytest.mark.random
    def test_projection_belongs(self, n_points, atol):
        if not self._is_planar():
            return

        super().test_projection_belongs(n_points, atol)

    def test_srv_projection(self, srv, expected, atol, max_iter=1000):
        res = self.space.srv_projection(srv, atol=atol, max_iter=max_iter)
        self.assertAllClose(res, expected, atol=atol)

    @pytest.mark.vec
    def test_srv_projection_vec(self, n_reps, atol, max_iter=1000):
        if not self._is_planar():
            return

        srv = self._get_srv_point()
        expected = self.space.srv_projection(srv, atol=atol, max_iter=max_iter)

        vec_data = generate_vectorization_data(
            data=[dict(srv=srv, expected=expected, max_iter=max_iter, atol=atol)],
            arg_names=["srv"],
            expected_name="expected",
            n_reps=n_reps,
        )
        self._test_vectorization(vec_data)

    @pytest.mark.random
    def test_projection_is_itself(self, n_points, atol):
        # TODO: should this go up?
        if not self._is_planar():
            return

        point = self.space.random_point(n_points)
        proj_point = self.space.projection(point)
        self.assertAllClose(proj_point, point, atol=atol)

    @pytest.mark.random
    def test_random_point_is_closed(self, n_points, atol):
        point = self.space.random_point(n_points)
        self.assertAllClose(point[..., 0, :], point[..., -1, :], atol=atol)


class SRVShapeBundleTestCase(FiberBundleTestCase):
    def setup_method(self):
        if not hasattr(self, "data_generator"):
            n_discretized_curves = (
                5
                if not hasattr(self, "n_discretized_curves")
                else self.n_discretized_curves
            )
            self.data_generator = ShapeBundleRandomDataGenerator(
                self.total_space,
                self.sphere,
                n_discretized_curves=n_discretized_curves,
            )

    @pytest.mark.random
    def test_tangent_vector_projections_orthogonality_with_metric(self, n_points, atol):
        """Test horizontal and vertical projections.

        Check that horizontal and vertical parts of any tangent
        vector are orthogonal with respect to the SRVMetric inner
        product.
        """
        base_point = self.data_generator.random_point(n_points)
        tangent_vec = self.data_generator.random_tangent_vec(base_point)

        tangent_vec_hor = self.bundle.horizontal_projection(tangent_vec, base_point)
        tangent_vec_ver = self.bundle.vertical_projection(tangent_vec, base_point)

        res = self.total_space.metric.inner_product(
            tangent_vec_hor, tangent_vec_ver, base_point
        )
        expected_shape = get_batch_shape(self.total_space, base_point)
        expected = gs.zeros(expected_shape)
        self.assertAllClose(res, expected, atol=atol)

    def test_horizontal_geodesic(
        self, initial_point, end_point, times, expected, atol, threshold=1e-3
    ):
        res = self.bundle.horizontal_geodesic(
            initial_point, end_point, threshold=threshold
        )(times)

        self.assertAllClose(res, expected, atol=atol)

    @pytest.mark.vec
    def test_horizontal_geodesic_vec(self, n_reps, n_times, atol):
        times = gs.linspace(0.0, 1.0, n_times)

        initial_point = self.data_generator.random_point()
        end_point = self.data_generator.random_point()

        expected = self.bundle.horizontal_geodesic(initial_point, end_point)(times)

        vec_data = generate_vectorization_data(
            data=[
                dict(
                    initial_point=initial_point,
                    end_point=end_point,
                    times=times,
                    expected=expected,
                    atol=atol,
                )
            ],
            arg_names=["initial_point", "end_point"],
            expected_name="expected",
            n_reps=n_reps,
        )
        self._test_vectorization(vec_data)

    @pytest.mark.random
    def test_horizontal_geodesic_has_horizontal_derivative(
        self, n_points, n_times, atol
    ):
        """Test horizontal geodesic.

        Check that the time derivative of the geodesic is horizontal at all time.
        """
        if n_points > 1:
            raise NotImplementedError("Not implemented for n_points > 1")

        initial_point = self.data_generator.random_point(n_points)
        end_point = self.data_generator.random_point(n_points)

        hor_geo_fun = self.bundle.horizontal_geodesic(initial_point, end_point)

        n_times = 20
        times = gs.linspace(0, 1, n_times)

        horizontal_geo = hor_geo_fun(times)
        velocity_vec = n_times * (horizontal_geo[1:] - horizontal_geo[:-1])

        _, vertical_norms = self.bundle.vertical_projection(
            velocity_vec, horizontal_geo[:-1], return_norm=True
        )

        res = gs.sum(vertical_norms**2, axis=1) ** (1 / 2)
        expected = gs.zeros(n_times - 1)
        self.assertAllClose(res, expected, atol=atol)
