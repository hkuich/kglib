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

import grakn

import examples.kgcn.adr.migration.query_executor as ex
import examples.kgcn.adr.migration.xml_migrate as xml_migrate


def main():
    migrator = xml_migrate.XMLMigrator(tag_mapping={'Label': 'tag-label',
                                                    'Text': 'tag-text',
                                                    'Section': 'tag-section',
                                                    'Mentions': 'tag-mentions',
                                                    'Mention': 'tag-mention',
                                                    'Relations': 'tag-relations',
                                                    'Relation': 'tag-relation',
                                                    'Reactions': 'tag-reactions',
                                                    'Reaction': 'tag-reaction',
                                                    'Normalization': 'tag-normalization',
                                                    },
                                       attr_tag_mapping={
                                           'Label': {'drug': 'label-drug', 'track': 'label-track'},
                                           'Section': {'name': 'section-name', 'id': 'section-id'},
                                           'Mention': {'id': 'mention-id', 'section': 'section-id',
                                                       'type': 'mention-type', 'start': 'mention-start',
                                                       'len': 'mention-len', 'str': 'name'},
                                           'Relation': {'id': 'relation-id', 'type': 'relation-type', 'arg1': 'arg1',
                                                        'arg2': 'arg2'},
                                           'Reaction': {'id': 'reaction-id', 'str': 'name'},
                                           'Normalization': {'id': 'normalization-id', 'meddra_pt': 'meddra_pt',
                                                             'meddra_pt_id': 'meddra_pt_id', 'meddra_llt': 'name',
                                                             'meddra_llt_id': 'meddra_llt_id'}

                                       },
                                       tag_containment={'relation': 'tag-containment',
                                                        'container_role': 'tag-container',
                                                        'containee_role': 'tag-containee'}
                                       )

    define_statements = migrator.get_define_statements()

    client = grakn.client.GraknClient(uri="localhost:48555")
    session = client.session(keyspace="adr")
    tx = session.transaction().write()

    for define_statement in define_statements:
        tx.query(define_statement)

    tx.commit()
    executor = ex.QueryTreeExecutor(session)

    xml = 'data/adrs/train_xml/ADCETRIS.xml'
    insert_tree = migrator.get_insert_statements(xml)

    # def recursive_print(tree):
    #     print(tree.query)
    #     if tree.children:
    #         for child in tree.children:
    #             recursive_print(child)
    # recursive_print(insert_tree)

    executor.insert(insert_tree)

    session.close()
    client.close()


"""
Query for 
match 
$label isa tag-label, has label-drug $drug;
$section isa tag-section, has section-id $sec-id; $rsl($section, $label) isa tag-containment;
$mention isa tag-mention, has section-id $sec-id, has mention-type $mt; $rml($mention, $label) isa tag-containment;
get; offset 0; limit 8;
"""

"""
define
transitive-tag-containment sub rule,
when {
    (tag-container: $x1, tag-containee: $x2) isa tag-containment;
    (tag-container: $x2, tag-containee: $x3) isa tag-containment;
} then {
    (tag-container: $x1, tag-containee: $x3) isa tag-containment;
};
"""

"""
define transitive-tag-containment sub rule, when {(tag-container: $x1, tag-containee: $x2) isa tag-containment; (tag-container: $x2, tag-containee: $x3) isa tag-containment;}, then {(tag-container: $x1, tag-containee: $x3) isa tag-containment;};
"""

if __name__ == "__main__":
    main()