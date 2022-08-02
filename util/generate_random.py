from backend.Document import Document
from random import choice, randint



def rand_docs(num_docs=100, num_authors=12, num_features=120):
    """randomly generate docs with random eventSets (features)."""
    large_doc_list = []
    for j in range(num_docs):
        author = 'a' + str(choice(range(num_authors)))
        ev_set = dict()

        for feature in [chr(randint(97, 122))+chr(randint(97, 122)) for x in range(num_features)]:
            ev_set[feature] = randint(0, 100)
        large_doc_list.append(Document(author, "t", "t", ".", eventSet=ev_set))

    return large_doc_list

