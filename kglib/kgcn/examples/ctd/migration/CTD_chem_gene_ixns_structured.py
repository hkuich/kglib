#
#  Licensed to the Apache Software Foundation (ASF) under one
#  or more contributor license agreements.  See the NOTICE file
#  distributed with this work for additional information
#  regarding copyright ownership.  The ASF licenses this file
#  to you under the Apache License, Version 2.0 (the
#  "License"); you may not use this file except in compliance
#  with the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.
#

from inspect import cleandoc

from kglib.kgcn.examples.ctd.migration.utils import parse_xml_to_tree_line_by_line
from kglib.kgcn.examples.ctd.migration.type_codes import type_codes


def exists_or_insert(tx, type, type_key, key_value):
    pm_query = f'match $x isa {type}, has {type_key} {key_value}; get;'
    results = list(tx.query(pm_query))
    if len(results) == 0:
        tx.query(f'insert $x isa {type}, has {type_key} {key_value};')


class Chemical:
    def __init__(self, tx, identifier, index):
        self.identifier = identifier
        self.index = index
        self.var = f'chem{self.index}'
        exists_or_insert(tx, 'chemical', 'identifier', identifier)
        self.match_statement = f'${self.var} isa chemical, has identifier {self.identifier};'


class Gene:
    def __init__(self, tx, identifier, index):
        self.identifier = identifier
        self.index = index
        self.var = f'gene{self.index}'
        exists_or_insert(tx, 'gene', 'identifier', identifier)
        self.match_statement = f'${self.var} isa gene, has identifier {self.identifier};'


class Interaction:
    def __init__(self, tx, identifier, index, relation_type, degree, text, pmids):
        self.tx = tx
        self.text = text
        self.pmids = pmids
        self.identifier = identifier
        self.relation_type = relation_type
        self.degree = degree
        self.index = index
        self.var = f'inter{self.index}'
        self.actor1 = None
        self.actor2 = None
        self.match_statement = f'${self.var} isa chemical-gene-interaction, has identifier {self.identifier};'

    def add_actors(self, actor1, actor2):
        self.actor1 = actor1
        self.actor2 = actor2
        return self

    def match_insert(self, actor1, actor2):
        sources_match = ''
        sources_insert = ''
        for pmid in self.pmids:
            sources_match += f'$source{pmid} isa pubmed-citation, has pmid {pmid}; '
            sources_insert += f'data-source: $source{pmid},'

        query = cleandoc(f'''match {actor1.match_statement}
                          {actor2.match_statement}
                          {sources_match}
                    insert
                        ${self.var}({sources_insert}
                        from-actor: ${actor1.var}, 
                        to-actor: ${actor2.var}
                        ) isa {self.relation_type}, has degree {self.degree}, has identifier "{self.identifier}", has text "{self.text}";
                ''')
        print(query)
        self.tx.query(query)


def recurse(tx, root, base_index):

    actor1 = None
    actor2 = None
    interaction = None
    pmids = []

    interaction_id = root.attrib['id']

    for i, child in enumerate(root):
        index = str(base_index) + str(i)
        print(child.tag, child.attrib)

        if child.tag == 'reference':
            pmid = child.attrib['pmid']
            pmids.append(pmid)
            exists_or_insert(tx, 'pubmed-citation', 'pmid', int(pmid))

        elif child.tag == 'axn':
            type_code = child.attrib['code']
            relation_type = type_codes[type_code]
            # '+' (increases), '-' (decreases), '1' (affects) or '0' (does not affect).
            degreecode = f"'{child.attrib['degreecode']}'"

            # interaction = Interaction(relation_type, degreecode)
            interaction = Interaction(tx, interaction_id, index, relation_type, degreecode, child.text, pmids)

            # TODO Add a switch statement to translate the code to words (or don't bother)

        elif child.tag == 'actor':
            type = child.attrib['type']  # 'gene' or 'chemical'
            identifier = f'"{child.attrib["id"]}"'
            position = child.attrib['position']  # 1 or 2

            if type == 'gene':
                # form = child.attrib['form'] # Sometimes present, either 'gene', 'protein', 'mRNA'
                # seqid = child.attrib['seqid']  # Only present sometimes
                actor = Gene(tx, identifier, index)

            elif type == 'chemical':
                actor = Chemical(tx, identifier, index)

            elif type == 'ixn':
                actor = recurse(tx, child, index)
            else:
                raise ValueError(f'Something not a gene nor a chemical nor an interaction was found, a {type}')

            if actor1 is None:
                actor1 = actor
            else:
                actor2 = actor

        # query = interaction.match_insert(actor1, actor2)
    interaction.add_actors(actor1, actor2)
    interaction.match_insert(actor1, actor2)


def migrate_chemical_gene_interactions(session, data_path):

    line_trees = parse_xml_to_tree_line_by_line(data_path)

    tx = session.transaction().write()
    for root in line_trees:

        if root[0].tag == 'taxon' and root[0].attrib['id'] == '9606':

            recurse(tx, root, 0)

        tx.commit()
        tx = session.transaction().write()