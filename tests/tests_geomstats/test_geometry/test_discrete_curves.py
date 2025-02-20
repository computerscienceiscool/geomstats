import random

import pytest

from geomstats.geometry.discrete_curves import (
    ClosedDiscreteCurves,
    DiscreteCurves,
    ElasticMetric,
    L2CurvesMetric,
    SRVMetric,
    SRVShapeBundle,
)
from geomstats.geometry.euclidean import Euclidean
from geomstats.geometry.hypersphere import Hypersphere
from geomstats.test.parametrizers import DataBasedParametrizer
from geomstats.test.random import DiscreteCurvesRandomDataGenerator
from geomstats.test_cases.geometry.discrete_curves import (
    ClosedDiscreteCurvesTestCase,
    ShapeBundleRandomDataGenerator,
    SRVShapeBundleTestCase,
)
from geomstats.test_cases.geometry.manifold import ManifoldTestCase
from geomstats.test_cases.geometry.mixins import ProjectionTestCaseMixins
from geomstats.test_cases.geometry.pullback_metric import PullbackDiffeoMetricTestCase
from geomstats.test_cases.geometry.quotient_metric import QuotientMetricTestCase
from geomstats.test_cases.geometry.riemannian_metric import RiemannianMetricTestCase

from .data.discrete_curves import (
    ClosedDiscreteCurvesTestData,
    DiscreteCurvesTestData,
    ElasticMetricTestData,
    L2CurvesMetricTestData,
    SRVMetricTestData,
    SRVQuotientMetricTestData,
    SRVShapeBundleTestData,
)


@pytest.fixture(
    scope="class",
    params=[
        (2, random.randint(5, 10)),
        (3, random.randint(5, 10)),
    ],
)
def discrete_curves_spaces(request):
    dim, k_sampling_points = request.param

    ambient_manifold = Euclidean(dim=dim)
    request.cls.space = DiscreteCurves(
        ambient_manifold, k_sampling_points=k_sampling_points, equip=False
    )


@pytest.mark.usefixtures("discrete_curves_spaces")
class TestDiscreteCurves(
    ProjectionTestCaseMixins, ManifoldTestCase, metaclass=DataBasedParametrizer
):
    testing_data = DiscreteCurvesTestData()

    def setup_method(self):
        if not hasattr(self, "data_generator"):
            self.data_generator = DiscreteCurvesRandomDataGenerator(self.space)


@pytest.fixture(
    scope="class",
    params=[
        (2, random.randint(5, 10)),
        (3, random.randint(5, 10)),
    ],
)
def closed_discrete_curves_spaces(request):
    dim, k_sampling_points = request.param
    ambient_manifold = Euclidean(dim=dim)

    request.cls.space = ClosedDiscreteCurves(
        ambient_manifold, k_sampling_points=k_sampling_points
    )


@pytest.mark.usefixtures("closed_discrete_curves_spaces")
class TestClosedDiscreteCurves(
    ClosedDiscreteCurvesTestCase, metaclass=DataBasedParametrizer
):
    testing_data = ClosedDiscreteCurvesTestData()


@pytest.fixture(
    scope="class",
    params=[
        (2, random.randint(5, 10)),
        (3, random.randint(5, 10)),
    ],
)
def l2_discrete_curves_spaces(request):
    dim, k_sampling_points = request.param

    ambient_manifold = Euclidean(dim=dim)
    space = request.cls.space = DiscreteCurves(
        ambient_manifold, k_sampling_points=k_sampling_points, equip=False
    )
    space.equip_with_metric(L2CurvesMetric)


@pytest.mark.usefixtures("l2_discrete_curves_spaces")
class TestL2CurvesMetric(RiemannianMetricTestCase, metaclass=DataBasedParametrizer):
    testing_data = L2CurvesMetricTestData()


@pytest.fixture(
    scope="class",
    params=[
        (2, random.randint(5, 10)),
    ],
)
def elastic_metric_discrete_curves_spaces(request):
    dim, k_sampling_points = request.param

    ambient_manifold = Euclidean(dim=dim)
    space = request.cls.space = DiscreteCurves(
        ambient_manifold,
        k_sampling_points=k_sampling_points,
        start_at_the_origin=True,
        equip=False,
    )
    space.equip_with_metric(ElasticMetric, a=1.0, b=0.5)


@pytest.mark.usefixtures("elastic_metric_discrete_curves_spaces")
class TestElasticMetric(PullbackDiffeoMetricTestCase, metaclass=DataBasedParametrizer):
    testing_data = ElasticMetricTestData()


@pytest.fixture(
    scope="class",
    params=[
        (2, random.randint(5, 10)),
        (3, random.randint(5, 10)),
    ],
)
def srv_discrete_curves_spaces(request):
    dim, k_sampling_points = request.param

    ambient_manifold = Euclidean(dim=dim)
    space = request.cls.space = DiscreteCurves(
        ambient_manifold,
        k_sampling_points=k_sampling_points,
        start_at_the_origin=True,
        equip=False,
    )
    space.equip_with_metric(SRVMetric)


@pytest.mark.usefixtures("srv_discrete_curves_spaces")
class TestSRVMetric(PullbackDiffeoMetricTestCase, metaclass=DataBasedParametrizer):
    testing_data = SRVMetricTestData()


@pytest.fixture(
    scope="class",
    params=[
        (2, random.randint(5, 10)),
        (3, random.randint(5, 10)),
    ],
)
def shape_bundles(request):
    dim, k_sampling_points = request.param

    ambient_manifold = Euclidean(dim=dim)
    space = DiscreteCurves(
        ambient_manifold, k_sampling_points=k_sampling_points, equip=True
    )
    request.cls.total_space = request.cls.base = space

    request.cls.bundle = SRVShapeBundle(space)

    request.cls.sphere = Hypersphere(dim=dim - 1)


@pytest.mark.usefixtures("shape_bundles")
class TestSRVShapeBundle(SRVShapeBundleTestCase, metaclass=DataBasedParametrizer):
    testing_data = SRVShapeBundleTestData()


@pytest.fixture(
    scope="class",
    params=[
        (2, random.randint(5, 10)),
        (3, random.randint(5, 10)),
    ],
)
def spaces_with_quotient(request):
    dim, k_sampling_points = request.param

    ambient_manifold = Euclidean(dim=dim)
    space = DiscreteCurves(
        ambient_manifold, k_sampling_points=k_sampling_points, equip=True
    )

    space.equip_with_group_action("reparametrizations")
    space.equip_with_quotient_structure()

    request.cls.space = space.quotient

    request.cls.sphere = Hypersphere(dim=dim - 1)


@pytest.mark.skip
@pytest.mark.usefixtures("spaces_with_quotient")
class TestSRVQuotientMetric(QuotientMetricTestCase, metaclass=DataBasedParametrizer):
    testing_data = SRVQuotientMetricTestData()

    def setup_method(self):
        if not hasattr(self, "data_generator"):
            n_discretized_curves = (
                5
                if not hasattr(self, "n_discretized_curves")
                else self.n_discretized_curves
            )
            self.data_generator = ShapeBundleRandomDataGenerator(
                self.space,
                self.sphere,
                n_discretized_curves=n_discretized_curves,
            )
