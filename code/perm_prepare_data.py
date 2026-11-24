"""Подготовка объявлений Перми. Запуск: python perm_prepare_data.py АРХИВ ГРАНИЦА ПАПКА."""
import argparse
import json
from pathlib import Path

from matplotlib.path import Path as Polygon
import numpy as np
import pandas as pd

ARCHIVE_URL = "https://www.kaggle.com/datasets/mrdaniilak/russia-real-estate-20182021"
BOUNDARY_URL = (
    "https://nominatim.openstreetmap.org/search.php?"
    "q=Perm%2C+Russia&polygon_geojson=1&format=jsonv2&limit=2"
)
PERM_RELATION = 3437213


def inside_city(frame, geometry):
    points = frame[["geo_lon", "geo_lat"]].to_numpy()
    inside = np.zeros(len(frame), dtype=bool)
    for outer, *holes in geometry["coordinates"]:
        inside_polygon = Polygon(outer).contains_points(points)
        for hole in holes:
            inside_polygon &= ~Polygon(hole).contains_points(points)
        inside |= inside_polygon
    return inside


def prepare(archive, boundary, output):
    places = json.loads(boundary.read_text(encoding="utf-8"))
    perm = next(place for place in places if place["osm_id"] == PERM_RELATION)
    south, north, west, east = map(float, perm["boundingbox"])
    geometry = perm["geojson"]
    if geometry["type"] == "Polygon":
        geometry = {"type": "MultiPolygon", "coordinates": [geometry["coordinates"]]}
    if geometry["type"] != "MultiPolygon":
        raise ValueError("Ожидается полигон границ Перми")

    parts = []
    source_rows = 0
    for chunk in pd.read_csv(archive, chunksize=250_000):
        source_rows += len(chunk)
        box = chunk["geo_lat"].between(south, north) & chunk["geo_lon"].between(west, east)
        nearby = chunk.loc[box]
        parts.append(nearby.loc[inside_city(nearby, geometry)])
    city = pd.concat(parts, ignore_index=True)

    # Код 1 указан для вторичного рынка. Коды остальных сегментов
    # сохраняем исходными до проверки расхождения в описании архива.
    city["date"] = pd.to_datetime(city["date"], errors="coerce")
    valid = city["date"].notna() & city["rooms"].isin([1, 2])
    valid &= city["area"].gt(0) & city["price"].gt(0)
    valid &= city["level"].ge(1) & city["level"].le(city["levels"])
    selected = city.loc[valid].drop(columns=["time", "region"]).copy()
    # Удаляем совпадающие записи одного дня. Повторные публикации
    # в другие дни без идентификатора нельзя уверенно признать дублями.
    cleaned = selected.drop_duplicates().copy()
    cleaned.insert(0, "listing_id", cleaned.index + 1)
    cleaned["year"] = cleaned["date"].dt.year

    output.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output / "perm_listing_candidates.csv", index=False)
    print(f"Строк в источнике: {source_rows:,}")
    print(f"В границах города: {len(city):,}")
    print(f"В городе по кодам рынка: {city['object_type'].value_counts().sort_index().to_dict()}")
    print(f"После отбора и базовой очистки: {len(cleaned):,}")
    print(f"Удалено совпадающих записей одного дня: {len(selected) - len(cleaned):,}")
    print(pd.crosstab(cleaned["year"], cleaned["object_type"]).to_string())
    print(f"Период: {cleaned['date'].min().date()} — {cleaned['date'].max().date()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, help="ZIP с all_v2.csv или распакованный CSV")
    parser.add_argument("boundary", type=Path, help="JSON ответа Nominatim для Перми")
    parser.add_argument("output", type=Path, help="Папка для CSV и результатов")
    args = parser.parse_args()
    prepare(args.archive, args.boundary, args.output)
