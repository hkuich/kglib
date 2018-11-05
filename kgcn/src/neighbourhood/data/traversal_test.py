import unittest

import grakn

import kgcn.src.neighbourhood.data.executor as ex
import kgcn.src.neighbourhood.data.sampling.sampler as samp
import kgcn.src.neighbourhood.data.traversal as trv
import kgcn.src.neighbourhood.data.sampling.ordered as ordered
import kgcn.src.neighbourhood.data.traversal_mocks as mocks


class TestNeighbourTraversalFromEntity(unittest.TestCase):

    session = None

    @classmethod
    def setUpClass(cls):
        client = grakn.Grakn(uri="localhost:48555")
        cls.session = client.session(keyspace="test_schema")

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def setUp(self):
        self._tx = self.session.transaction(grakn.TxType.WRITE)

        # identifier = "Jacob J. Niesz"
        # entity_query = "match $x isa person, has identifier '{}'; get $x;".format(identifier)
        entity_query = "match $x isa person, has name 'Sundar Pichai'; get;"

        self._concept_info = ex.build_concept_info(list(self._tx.query(entity_query))[0].get('x'))

        self._executor = ex.TraversalExecutor(self._tx)

    def _neighbourhood_traverser_factory(self, neighbour_sample_sizes):
        sampling_method = ordered.ordered_sample

        samplers = []
        for sample_size in neighbour_sample_sizes:
            samplers.append(samp.Sampler(sample_size, sampling_method, limit=sample_size * 2))

        neighourhood_traverser = trv.NeighbourhoodTraverser(self._executor, samplers)
        return neighourhood_traverser

    def tearDown(self):
        self._tx.close()

    def _assert_types_correct(self, concept_info_with_neighbourhood):
        """
        Check that all of the types in the structure are as expected
        :param concept_info_with_neighbourhood:
        :return:
        """
        self.assertIsInstance(concept_info_with_neighbourhood, trv.ConceptInfoWithNeighbourhood)
        self.assertIsInstance(concept_info_with_neighbourhood.concept_info,
                              ex.ConceptInfo)
        self.assertIn(type(concept_info_with_neighbourhood.neighbourhood).__name__, ('generator', 'chain'))

        try:
            neighbour_role = next(concept_info_with_neighbourhood.neighbourhood)

            self.assertIsInstance(neighbour_role, trv.NeighbourRole)

            self.assertTrue(isinstance(neighbour_role.role_label, str))
            self.assertIn(neighbour_role.role_direction, [ex.TARGET_PLAYS,
                                                          ex.NEIGHBOUR_PLAYS])
            self.assertTrue(self._assert_types_correct(neighbour_role.neighbour_info_with_neighbourhood))
        except StopIteration:
            pass

        return True

    def _assert_depth_correct(self, concept_info_with_neighbourhood):
        neighbour_role = next(concept_info_with_neighbourhood.neighbourhood, None)
        if neighbour_role is not None:
            self._assert_depth_correct(neighbour_role.neighbour)

    def test_neighbour_traversal_structure_types(self):
        data = ((1,), (2, 3), (2, 3, 4))
        for sample_sizes in data:
            with self.subTest(sample_sizes=str(data)):
                self._concept_info_with_neighbourhood = self._neighbourhood_traverser_factory(sample_sizes)(
                    self._concept_info)
                self._assert_types_correct(self._concept_info_with_neighbourhood)

    def test_neighbour_traversal_check_depth(self):
        data = ((1,), (2, 3), (2, 3, 4))
        for sample_sizes in data:
            with self.subTest(sample_sizes=str(data)):
                self._concept_info_with_neighbourhood = self._neighbourhood_traverser_factory(sample_sizes)(
                    self._concept_info)

                collected_tree = trv.collect_to_tree(self._concept_info_with_neighbourhood)

                with self.subTest("Check number of immediate neighbours"):
                    self.assertEqual(len(collected_tree.neighbourhood), sample_sizes[0])
                with self.subTest("Check max depth of tree"):
                    self.assertEqual(len(sample_sizes), trv.get_max_depth(self._concept_info_with_neighbourhood))

    def test_neighbour_traversal_is_deterministic(self):
        data = ((1,), (2, 3), (2, 3, 4))
        for sample_sizes in data:
            def to_test():
                return trv.collect_to_tree(self._neighbourhood_traverser_factory(sample_sizes)(self._concept_info))

            with self.subTest(sample_sizes=str(data)):
                concept_info_with_neighbourhood = to_test()

                for i in range(10):
                    new_concept_info_with_neighbourhood = to_test()
                    self.assertEqual(new_concept_info_with_neighbourhood, concept_info_with_neighbourhood)

    def test_input_output(self):

        neighbour_sample_sizes = (2, 3)

        samplers = [lambda x: x for sample_size in neighbour_sample_sizes]

        starting_concept = ex.ConceptInfo("0", "person", "entity")

        neighourhood_traverser = trv.NeighbourhoodTraverser(mocks.mock_executor, samplers)

        concept_with_neighbourhood = neighourhood_traverser(starting_concept)

        a, b = trv.collect_to_tree(concept_with_neighbourhood), trv.collect_to_tree(mocks.mock_traversal_output())
        self.assertEqual(a, b)

    def test_input_output_integration(self):
        """
        Runs using real samplers
        :return:
        """

        sampling_method = ordered.ordered_sample

        samplers = [samp.Sampler(2, sampling_method, limit=2), samp.Sampler(3, sampling_method, limit=1)]

        starting_concept = ex.ConceptInfo("0", "person", "entity")

        neighourhood_traverser = trv.NeighbourhoodTraverser(mocks.mock_executor, samplers)

        concept_with_neighbourhood = neighourhood_traverser(starting_concept)

        a, b = trv.collect_to_tree(concept_with_neighbourhood), trv.collect_to_tree(mocks.mock_traversal_output())
        self.assertEqual(a, b)

