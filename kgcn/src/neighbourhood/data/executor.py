import kgcn.src.neighbourhood.data.utils as utils

TARGET_PLAYS = 0  # In this case, the neighbour is a relationship in which this concept plays a role
NEIGHBOUR_PLAYS = 1  # In this case the target

ROLES_PLAYED = 0
ROLEPLAYERS = 1


class TraversalExecutor:

    ROLES_PLAYED_QUERY = {
        'query': "match $x id {}; $relationship($role: $x); get $relationship, $role;",
        'role_variable': 'role',
        'role_direction': TARGET_PLAYS,
        'neighbour_variable': 'relationship'}

    ROLEPLAYERS_QUERY = {
        'query': "match $relationship id {}; $relationship($role: $x) isa {}; get $x, $role;",
        'role_variable': 'role',
        'role_direction': NEIGHBOUR_PLAYS,
        'neighbour_variable': 'x'}

    def __init__(self, grakn_tx, roles_played_query=ROLES_PLAYED_QUERY, roleplayers_query=ROLEPLAYERS_QUERY):
        self._grakn_tx = grakn_tx
        self.roles_played_query = roles_played_query
        self.roleplayers_query = roleplayers_query

    def __call__(self, query_direction, *args):
            """
            Takes a query to execute and the variables to return
            :param query_direction: whether we want to retrieve roles played or role players
            :param concept_id: id for the concept to find connections for
            :return:
            """

            if query_direction == ROLES_PLAYED:
                base_query = self.ROLES_PLAYED_QUERY
            elif query_direction == ROLEPLAYERS:
                base_query = self.ROLEPLAYERS_QUERY
            else:
                raise ValueError('query_direction isn\'t properly defined')

            query = base_query['query'].format(*args)
            print(query)
            roles_iterator = self._grakn_tx.query(query)

            def _roles_iterator():
                for answer in roles_iterator:
                    role_label = answer.get(base_query['role_variable']).label()
                    relationship_concept = answer.get(base_query['neighbour_variable'])
                    relationship_info = build_concept_info(relationship_concept)

                    yield {'role_label': role_label, 'role_direction': base_query['role_direction'],
                           'neighbour_info': relationship_info}

            return _roles_iterator()


class ConceptInfo(utils.PropertyComparable):
    def __init__(self, id, type_label, base_type_label, data_type=None, value=None):
        self.id = id
        self.type_label = type_label
        self.base_type_label = base_type_label  # TODO rename to base_type in line with Client Python

        # If the concept is an attribute
        self.data_type = data_type
        self.value = value


def build_concept_info(concept):

    id = concept.id
    type_label = concept.type().label()
    metatype_label = concept.base_type.lower()

    if metatype_label == 'ATTRIBUTE':
        data_type = concept.data_type()
        value = concept.value()

        return ConceptInfo(id, type_label, metatype_label, data_type, value)

    return ConceptInfo(id, type_label, metatype_label)