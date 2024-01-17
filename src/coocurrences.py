def calculate_co_occurrences(corpus, window_size=5):
    vocabulary = {}
    row_indices, col_indices, data = [], [], []
    stop_words = uf.get_stopwords()

    for key, value in corpus.items():
        for neighborhood in value:
            neighborhood_lowercase = neighborhood.lower()
            neighborhood_no_stopwords = uf.remove_stopwords(neighborhood_lowercase, stop_words)
            neighborhood_no_stopwords_filtered = uf.remove_accents(neighborhood_no_stopwords)
            neighborhood_no_stopwords_filtered = uf.remove_non_letters(neighborhood_no_stopwords_filtered)
            neighborhood_no_stopwords_filtered = uf.remove_stopwords(neighborhood_no_stopwords_filtered, stop_words)
            tokens = uf.tokenize(neighborhood_no_stopwords_filtered)
            tokens = [token for token in tokens if len(token) >= 3]
            for i, target_word in enumerate(tokens):
                for j in range(max(0, i - window_size), min(len(tokens), i + window_size + 1)):
                    if i != j:
                        context_word = tokens[j]

                        if target_word not in vocabulary:
                            vocabulary[target_word] = len(vocabulary)

                        if context_word not in vocabulary:
                            vocabulary[context_word] = len(vocabulary)

                        target_idx = vocabulary[target_word]
                        context_idx = vocabulary[context_word]

                        row_indices.append(target_idx)
                        col_indices.append(context_idx)
                        data.append(1)

    co_occurrence_matrix = coo_matrix((data, (row_indices, col_indices)), shape=(len(vocabulary), len(vocabulary)))
    return co_occurrence_matrix, vocabulary
