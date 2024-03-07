def levenshtein_distance(s1, s2):
    s1 = s1.lower()
    s2 = s2.lower()

    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


# def recommend_word(word, dict_keys):
#     closest_word = None
#     min_distance = float('inf')
#
#     for key in dict_keys:
#         distance = levenshtein_distance(word, key)
#         if distance < min_distance:
#             min_distance = distance
#             closest_word = key
#
#     return closest_word


def recommend_words(word, seq):
    closest_words = []
    min_distance = float('inf')

    for key in seq:
        distance = levenshtein_distance(word, key)
        if distance < min_distance:
            min_distance = distance
            closest_words = [key]
        elif distance == min_distance:
            closest_words.append(key)

    return closest_words
