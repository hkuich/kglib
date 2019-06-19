#
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  'License'); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
#

import unittest

import networkx as nx

import experiment.data as data

import numpy as np


class TestDataGeneration(unittest.TestCase):
    def test_all_people_are_play_roles_in_each_relation(self):
        num_people = 3
        G = data.generate_graph(num_people)
        expected_relation_types = ['parentship'] * 4 * 2
        # We multiply by 2 since we duplicate the number of roleplayer links by creating another link in the reverse
        # direction, so that message passing can travel in both directions
        expected_relation_types.extend(['siblingship'] * 2 * 2)
        for node in G.nodes:
            if G.nodes[node]['type'] == 'person':
                neighbours = nx.all_neighbors(G, node)
                relation_types = []
                for neighbour in neighbours:
                    relation_types.append(G.nodes[neighbour]['type'])
                self.assertListEqual(sorted(relation_types), sorted(expected_relation_types))

    def test__all_parentships_have_correct_roles(self):
        num_people = 3
        G = data.generate_graph(num_people)
        for node in G.nodes:
            if G.nodes[node]['type'] == 'parentship':
                role_types = [roleplayer_data[0]['type'] for roleplayer, roleplayer_data in G[node].items()]
                self.assertListEqual(sorted(role_types), sorted(['parent', 'child']))

    def test__all_siblingships_have_correct_roles(self):
        num_people = 3
        G = data.generate_graph(num_people)
        for node in G.nodes:
            if G.nodes[node]['type'] == 'siblingship':
                role_types = [roleplayer_data[0]['type'] for roleplayer, roleplayer_data in G[node].items()]
                self.assertListEqual(role_types, ['sibling', 'sibling'])


class TestBaseLabelling(unittest.TestCase):
    def test_node_labels_added_correctly(self):
        num_people = 3
        G = data.generate_graph(num_people)
        data.add_base_labels(G, 'input')
        expected_node_input_labels = [0] * G.number_of_nodes()
        expected_node_input_labels[:num_people] = [1] * num_people

        input_labels = [G.nodes[node]['input'] for node in G.nodes]

        self.assertListEqual(input_labels, expected_node_input_labels)

    def test_edge_labels_added_correctly(self):
        num_people = 3
        G = data.generate_graph(num_people)
        data.add_base_labels(G, 'input')
        expected_edge_input_labels = [0] * G.number_of_edges()

        input_labels = [G.edges[edge]['input'] for edge in G.edges]

        self.assertListEqual(input_labels, expected_edge_input_labels)


class TestFindRelationNode(unittest.TestCase):
    def test_parentship_found_correctly(self):
        num_people = 3
        G = data.generate_graph(num_people)
        data.add_base_labels(G, 'input')

        parentship_node = data.find_relation_node(G, 'parentship', ['parent', 'child'], [0, 1])
        self.assertEqual(parentship_node, 3)


class TestAddParentship(unittest.TestCase):
    def test_parentship_node_and_role_edges_labelled(self):
        num_people = 3
        G = data.generate_graph(num_people)
        data.add_base_labels(G, 'input')

        self.assertEqual(G.nodes[3]['input'], 0)
        self.assertEqual(G.edges[3, 0, 0]['input'], 0)
        self.assertEqual(G.edges[3, 1, 0]['input'], 0)

        data.add_parentship(G, 0, 1, 'input')

        self.assertEqual(G.nodes[3]['input'], 1)
        self.assertEqual(G.edges[3, 0, 0]['input'], 1)
        self.assertEqual(G.edges[3, 1, 0]['input'], 1)


class TestAddSiblingship(unittest.TestCase):
    def test_siblingship_node_and_role_edges_labelled(self):
        num_people = 3
        G = data.generate_graph(num_people)
        data.add_base_labels(G, 'input')

        self.assertEqual(G.nodes[9]['input'], 0)
        self.assertEqual(G.edges[9, 0, 0]['input'], 0)
        self.assertEqual(G.edges[9, 1, 0]['input'], 0)

        data.add_siblingship(G, 0, 1, 'input')

        self.assertEqual(G.nodes[9]['input'], 1)
        self.assertEqual(G.edges[9, 0, 0]['input'], 1)
        self.assertEqual(G.edges[9, 1, 0]['input'], 1)


class TestOneHotEncodeTypes(unittest.TestCase):
    def test_type_encoding_is_as_expected(self):
        num_people = 2
        G = data.generate_graph(num_people)
        all_node_types = ['person', 'parentship', 'siblingship']
        all_edge_types = ['parent', 'child', 'sibling']
        data.encode_types_one_hot(G, all_node_types, all_edge_types, attribute='one_hot_type')

        for node_index, node_feature in G.nodes(data=True):
            if node_feature['type'] == 'person':
                np.testing.assert_array_equal(node_feature['one_hot_type'], np.array([1, 0, 0]))
            elif node_feature['type'] == 'parentship':
                np.testing.assert_array_equal(node_feature['one_hot_type'], np.array([0, 1, 0]))
            elif node_feature['type'] == 'siblingship':
                np.testing.assert_array_equal(node_feature['one_hot_type'], np.array([0, 0, 1]))
            else:
                raise ValueError(f'All nodes should have a type in {all_node_types}')

        for receiver, sender, edge_feature in G.edges(data=True):
            if edge_feature['type'] == 'parent':
                np.testing.assert_array_equal(edge_feature['one_hot_type'], np.array([1, 0, 0]))
            elif edge_feature['type'] == 'child':
                np.testing.assert_array_equal(edge_feature['one_hot_type'], np.array([0, 1, 0]))
            elif edge_feature['type'] == 'sibling':
                np.testing.assert_array_equal(edge_feature['one_hot_type'], np.array([0, 0, 1]))
            else:
                raise ValueError(f'All edges should have a type in {all_edge_types}')


if __name__ == "__main__":
    unittest.main()
