"""The glare model: for a pitch at latitude lat with its line at bearing b (0..180), the minutes in a season when the
sun is low (apparent altitude above 0 and at most ALT_MAX degrees) and within HALF degrees of the line of the pitch,
looking either way, from 10:00 local apparent solar time until sunset (evening matches included). Solar position from the declination
(Spencer 1971 series) and the hour angle, minute by minute, refraction by Bennett (1982)."""
import numpy as np, math

ALT_MAX, HALF = 15.0, 15.0
PLAY = (10.0, 22.0)     # hours, local apparent solar time: from 10 in the morning until the sun sets


def decl(doy):
    g = 2 * np.pi * (np.asarray(doy, float) - 1) / 365.0
    return np.degrees(0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
                      + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))


def season_days(lat):
    """cricket season: mid April to mid September north of the tropics, mid October to mid March south of 10 S and
    in the northern tropics (the South Asian and Caribbean dry seasons), every day otherwise"""
    if lat >= 23.5:
        return np.arange(105, 259)
    if lat <= -10 or lat >= 0:
        return np.r_[np.arange(288, 366), np.arange(1, 75)]
    return np.arange(1, 366)


def sun_positions(lat, days):
    t = np.arange(PLAY[0] * 60, PLAY[1] * 60) / 60.0            # hours
    H = np.radians((t - 12.0) * 15.0)[None, :]
    d = np.radians(decl(days))[:, None]
    p = math.radians(lat)
    sh = np.sin(p) * np.sin(d) + np.cos(p) * np.cos(d) * np.cos(H)
    h = np.degrees(np.arcsin(np.clip(sh, -1, 1)))
    az = np.degrees(np.arctan2(-np.cos(d) * np.sin(H), np.cos(p) * np.sin(d) - np.sin(p) * np.cos(d) * np.cos(H))) % 360
    hr = h + 1.02 / np.tan(np.radians(np.maximum(h, -1.0) + 10.3 / (np.maximum(h, -1.0) + 5.11))) / 60.0
    return hr.ravel(), az.ravel()


def glare(lat, bearings=np.arange(0, 180, 1.0), days=None):
    """minutes of glare per season for each bearing"""
    days = season_days(lat) if days is None else days
    h, az = sun_positions(lat, days)
    low = (h > 0) & (h <= ALT_MAX)
    a = az[low] % 180
    out = []
    for b in bearings:
        dd = np.abs((a - b + 90) % 180 - 90)
        out.append(int((dd <= HALF).sum()))
    return np.array(out)
