"""Statistical Manifold of Binomial distributions with the Fisher metric.

Lead authors: Jules Deschamps, Tra My Nguyen.
"""

from scipy.stats import expon

import geomstats.backend as gs
from geomstats.geometry.base import OpenSet
from geomstats.geometry.euclidean import Euclidean
from geomstats.geometry.riemannian_metric import RiemannianMetric
from geomstats.information_geometry.base import (
    InformationManifoldMixin,
    ScipyUnivariateRandomVariable,
)


class ExponentialDistributions(InformationManifoldMixin, OpenSet):
    """Class for the manifold of exponential distributions.

    This is the parameter space of exponential distributions
    i.e. the half-line of positive reals.
    """

    def __init__(self, equip=True):
        super().__init__(
            dim=1,
            embedding_space=Euclidean(dim=1, equip=False),
            support_shape=(),
            equip=equip,
        )
        self._scp_rv = ExponentialDistributionsRandomVariable(self)

    @staticmethod
    def default_metric():
        """Metric to equip the space with if equip is True."""
        return ExponentialMetric

    def belongs(self, point, atol=gs.atol):
        """Evaluate if a point belongs to the manifold of exponential distributions.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            Point to be checked.
        atol : float
            Tolerance to evaluate positivity.
            Optional, default: gs.atol

        Returns
        -------
        belongs : array-like, shape=[...,]
            Boolean indicating whether point represents an exponential
            distribution.
        """
        belongs_shape = self.shape == point.shape[-self.point_ndim :]
        if not belongs_shape:
            shape = point.shape[: -self.point_ndim]
            return gs.zeros(shape, dtype=bool)
        return gs.squeeze(point >= -atol)

    def random_point(self, n_samples=1, lower_bound=0.1, upper_bound=1.0):
        """Sample parameters of exponential distributions.

        The uniform distribution on [0, bound] is used.

        Parameters
        ----------
        n_samples : int
            Number of samples.
            Optional, default: 1.
        bound : float
            Right-end ot the segment where exponential parameters are sampled.
            Optional, default: 1.

        Returns
        -------
        samples : array-like, shape=[n_samples,]
            Sample of points representing exponential distributions.
        """
        size = (n_samples, self.dim) if n_samples != 1 else (self.dim,)
        return (upper_bound - lower_bound) * gs.random.rand(*size) + lower_bound

    def projection(self, point, atol=gs.atol):
        """Project a point in ambient space to the open set.

        The last coordinate is floored to `gs.atol` if it is non-positive.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            Point in ambient space.
        atol : float
            Tolerance to evaluate positivity.

        Returns
        -------
        projected : array-like, shape=[..., 1]
            Projected point.
        """
        return gs.where(point < atol, atol, point)

    def sample(self, point, n_samples=1):
        """Sample from the exponential distribution.

        Sample from the exponential distribution with parameter provided
        by point.

        Parameters
        ----------
        point : array-like, shape=[...,]
            Point representing an exponential distribution.
        n_samples : int
            Number of points to sample with each parameter in point.
            Optional, default: 1.

        Returns
        -------
        samples : array-like, shape=[..., n_samples]
            Sample from exponential distributions.
        """
        return self._scp_rv.rvs(point, n_samples)

    def point_to_pdf(self, point):
        """Compute pdf associated to point.

        Compute the probability density function of the exponential
        distribution with parameters provided by point.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            Point representing an exponential distribution (scale).

        Returns
        -------
        pdf : function
            Probability density function of the exponential distribution with
            scale parameter provided by point.
        """

        def pdf(x):
            """Generate parameterized function for exponential pdf.

            The pdf is parameterized by the scale parameter of the exponential,
            which is equal to 1 / lambda, where lambda is the rate parameter.

            Parameters
            ----------
            x : array-like, shape=[n_points,]
                Points at which to compute the probability density function.

            Returns
            -------
            pdf_at_x : array-like, shape=[..., n_points]
            """
            x = gs.reshape(gs.array(x), (-1,))
            pdf_at_x = point * gs.exp(-point * x)
            return gs.where(x >= 0, pdf_at_x, 0.0)

        return pdf


class ExponentialMetric(RiemannianMetric):
    """Class for the Fisher information metric on exponential distributions.

    References
    ----------
    .. [AM1981] Atkinson, C., & Mitchell, A. F. (1981). Rao's distance measure.
        Sankhyā: The Indian Journal of Statistics, Series A, 345-365.
    """

    def squared_dist(self, point_a, point_b, **kwargs):
        """Compute squared distance associated with the exponential Fisher Rao metric.

        Parameters
        ----------
        point_a : array-like, shape=[..., 1]
            Point representing an exponential distribution (scale parameter).
        point_b : array-like, shape=[..., 1]
            Point representing a exponential distribution (scale parameter).

        Returns
        -------
        squared_dist : array-like, shape=[...,]
            Squared distance between points point_a and point_b.
        """
        return gs.squeeze(gs.log(point_a / point_b) ** 2)

    def metric_matrix(self, base_point):
        """Compute the metric matrix at the tangent space at base_point.

        Parameters
        ----------
        base_point : array-like, shape=[..., 1]
            Point representing a binomial distribution.

        Returns
        -------
        mat : array-like, shape=[..., 1, 1]
            Metric matrix.
        """
        return gs.expand_dims(1 / base_point**2, axis=-1)

    @staticmethod
    def _geodesic_path(t, initial_point, base):
        """Generate parameterized function for geodesic curve.

        Parameters
        ----------
        t : array-like, shape=[n_times,]
            Times at which to compute points of the geodesics.

        Returns
        -------
        geodesic : array-like, shape=[..., n_times, 1]
            Values of the geodesic at times t.
        """
        t = gs.reshape(gs.array(t), (-1,))
        base_aux, t_aux = gs.broadcast_arrays(base, t)
        return gs.expand_dims(initial_point * base_aux**t_aux, axis=-1)

    def _geodesic_ivp(self, initial_point, initial_tangent_vec):
        """Solve geodesic initial value problem.

        Compute the parameterized function for the geodesic starting at
        initial_point with initial velocity given by initial_tangent_vec.

        Parameters
        ----------
        initial_point : array-like, shape=[..., 1]
            Initial point.

        initial_tangent_vec : array-like, shape=[..., 1]
            Tangent vector at initial point.

        Returns
        -------
        path : function
            Parameterized function for the geodesic curve starting at
            initial_point with velocity initial_tangent_vec.
        """
        base = gs.exp(initial_tangent_vec / initial_point)
        return lambda t: self._geodesic_path(t, initial_point, base)

    def _geodesic_bvp(self, initial_point, end_point):
        """Solve geodesic boundary problem.

        Compute the parameterized function for the geodesic starting at
        initial_point and ending at end_point.

        Parameters
        ----------
        initial_point : array-like, shape=[..., 1]
            Initial point.
        end_point : array-like, shape=[..., 1]
            End point.

        Returns
        -------
        path : function
            Parameterized function for the geodesic curve starting at
            initial_point and ending at end_point.
        """
        base = end_point / initial_point
        return lambda t: self._geodesic_path(t, initial_point, base)

    def exp(self, tangent_vec, base_point):
        """Compute exp map of a base point in tangent vector direction.

        Parameters
        ----------
        tangent_vec : array-like, shape=[..., 1]
            Tangent vector at base point.
        base_point : array-like, shape=[..., 1]
            Base point.

        Returns
        -------
        exp : array-like, shape=[..., 1]
            End point of the geodesic starting at base_point with
            initial velocity tangent_vec.
        """
        return gs.exp(tangent_vec / base_point) * base_point

    def log(self, point, base_point):
        """Compute log map using a base point and an end point.

        Parameters
        ----------
        point : array-like, shape=[..., 1]
            End point.
        base_point : array-like, shape=[..., 1]
            Base point.

        Returns
        -------
        tangent_vec : array-like, shape=[..., 1]
            Initial velocity of the geodesic starting at base_point and
            reaching point at time 1.
        """
        return base_point * gs.log(point / base_point)


class ExponentialDistributionsRandomVariable(ScipyUnivariateRandomVariable):
    """An exponential random variable."""

    def __init__(self, space):
        super().__init__(space, expon.rvs, expon.pdf)

    @staticmethod
    def _flatten_params(point, pre_flat_shape):
        flat_scale_param = gs.reshape(gs.broadcast_to(1 / point, pre_flat_shape), (-1,))
        return {"scale": flat_scale_param}
