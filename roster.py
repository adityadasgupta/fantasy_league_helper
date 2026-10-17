"""Editable starting roster transcribed from the supplied Yahoo screenshot."""

ROSTER = [
    (1628983, "Shai Gilgeous-Alexander", "OKC", "PG", (10.8, 19.4, 7.9, 9.0, 1.7, 31.1, 4.3, 6.6, 1.4, 0.8, 2.2)),
    (1630166, "Deni Avdija", "POR", "SG,SF,PF", (7.5, 16.1, 7.4, 9.2, 1.9, 24.2, 6.9, 6.7, 0.8, 0.6, 3.8)),
    (1630217, "Desmond Bane", "ORL", "SG,SF", (7.1, 14.7, 3.8, 4.2, 2.0, 20.1, 4.1, 4.1, 1.0, 0.5, 2.0)),
    (1629008, "Michael Porter Jr.", "BKN", "SF,PF", (8.5, 18.4, 3.8, 4.4, 3.4, 24.2, 7.1, 3.0, 1.1, 0.3, 2.3)),
    (1629675, "Naz Reid", "CHA", "PF,C", (5.2, 11.3, 1.2, 1.6, 2.1, 13.6, 6.2, 2.2, 1.0, 1.0, 1.6)),
    (1642852, "Derik Queen", "NOP", "PF,C", (4.4, 9.2, 2.7, 3.4, 0.3, 11.7, 7.1, 3.7, 1.0, 0.9, 2.3)),
    (1631105, "Jalen Duren", "DET", "C", (7.5, 11.5, 4.6, 6.1, 0.0, 19.5, 10.5, 2.0, 0.8, 0.8, 1.9)),
    (1641764, "Brandin Podziemski", "GSW", "PG,SG", (4.8, 10.6, 2.3, 2.9, 1.9, 13.8, 5.1, 3.7, 1.1, 0.2, 1.6)),
    (1627832, "Fred VanVleet", "HOU", "PG", None),
    (1628976, "Wendell Carter Jr.", "ORL", "C", (4.2, 8.2, 2.5, 3.2, 0.9, 11.8, 7.4, 2.0, 0.8, 0.6, 1.3)),
    (1631109, "Mark Williams", "PHX", "C", (4.7, 7.3, 2.3, 2.9, 0.0, 11.7, 8.0, 1.0, 0.9, 0.9, 1.1)),
    (1642272, "Jared McCain", "OKC", "PG,SG", (3.0, 7.2, 0.8, 0.9, 1.5, 8.3, 2.0, 1.3, 0.5, 0.1, 0.8)),
    (1642377, "Jaylen Wells", "MEM", "SG,SF", (4.4, 10.1, 1.9, 2.5, 1.9, 12.5, 3.2, 1.6, 0.9, 0.1, 1.1)),
    (1642866, "Joan Beringer", "MIN", "PF,C", (1.6, 2.5, 0.7, 0.9, 0.0, 3.9, 2.3, 0.3, 0.2, 0.7, 0.3)),
    (1626220, "Royce O'Neale", "CHA", "SF,PF", (3.4, 8.0, 0.3, 0.5, 2.7, 9.8, 4.8, 2.7, 1.1, 0.4, 1.3)),
]

STAT_KEYS = ("fgm", "fga", "ftm", "fta", "threes", "pts", "reb", "ast", "stl", "blk", "tov")


def initial_roster():
    return [
        {
            "id": player_id,
            "name": name,
            "team": team,
            "positions": positions.split(","),
            "available": stats is not None,
            "stats": dict(zip(STAT_KEYS, stats or (0,) * len(STAT_KEYS))),
        }
        for player_id, name, team, positions, stats in ROSTER
    ]
