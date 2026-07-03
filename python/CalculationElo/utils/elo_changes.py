# -*- coding: utf-8 -*-

def _get_k_factor(rating):
    if rating <= 600:
        return 25
    elif 601 <= rating <= 2400:
        return 15
    elif 2401 <= rating <= 3000:
        return 10
    else:
        return 5


def calculate_elo_changes(allies_rating, enemies_rating):
    difference_rating = int(enemies_rating) - int(allies_rating)
    value_k = difference_rating * 0.0025
        
    expected1 = 1 / (1 + (pow(10, value_k)))
        
    k1 = _get_k_factor(allies_rating)

    elo_plus = int(round(k1 * (1 - expected1)))
    elo_minus = int(round(k1 * (0 - expected1)))

    return elo_plus, elo_minus