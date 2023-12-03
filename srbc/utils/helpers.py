# -*- coding: utf-8 -*-


def pluralize(num, word_forms):
    if not isinstance(word_forms, list):
        raise TypeError("Word forms should be a list")
    if len(word_forms) < 1:
        raise AttributeError("Bad word forms")

    if len(word_forms) < 2:
        word_forms.append(word_forms[0])

    if len(word_forms) < 3:
        word_forms.append(word_forms[1])

    if num % 10 == 1 and num % 100 != 11:
        return word_forms[0]
    elif 2 <= num % 10 <= 4 and (num % 100 < 10 or num % 100 >= 20):
        return word_forms[1]
    else:
        return word_forms[2]
