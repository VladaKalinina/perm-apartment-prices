
# Оценка цен предложения квартир в Перми

Самостоятельная работа по дисциплине «Введение в нейронные сети», НИУ ВШЭ в Перми.

## Данные и код

| Файл | Содержание |
|---|---|
| [perm_dataset.xlsx](data/perm_dataset.xlsx) | 26 406 объявлений о продаже одно- и двухкомнатных квартир в Перми после базовой очистки. Из этой выборки подготовлены входы для Нейросимулятора. |
| [perm_prepare_data.py](code/perm_prepare_data.py) | Код отбора объявлений в границах Перми и базовой очистки. Скрипт сохраняет отобранные записи в CSV. |

Полный общероссийский архив доступен на [Kaggle](https://www.kaggle.com/datasets/mrdaniilak/russia-real-estate-20182021). Для повторного отбора понадобится CSV из архива и [JSON с полигоном границы Перми](https://nominatim.openstreetmap.org/search.php?q=Perm%2C+Russia&polygon_geojson=1&format=jsonv2&limit=2), сохранённый как `perm_boundary.json`. Источник границы — [OpenStreetMap contributors](https://www.openstreetmap.org/relation/3437213).

```bash
python -m pip install pandas numpy matplotlib
python code/perm_prepare_data.py all_v2.csv perm_boundary.json runs/data
```

## Нейросимулятор 5

| Файл | Содержание |
|---|---|
| [train.xlsx](neurosimulator/input/train.xlsx) | Обучающая выборка, 20 741 строка. |
| [validation.xlsx](neurosimulator/input/validation.xlsx) | Валидационная выборка, 3 080 строк. |
| [test.xlsx](neurosimulator/input/test.xlsx) | Входные данные для вкладки «Проверка», 2 526 строк. |
| [forecast_area.xlsx](neurosimulator/input/forecast_area.xlsx) | Входные данные для вкладки «Прогноз». В 17 сценариях меняется только площадь квартиры, от 40,7 до 51,0 м². |
| [test_predictions.xlsx](neurosimulator/output/test_predictions.xlsx) | Выгрузка из вкладки «Проверка» с признаками, фактическим значением D1, прогнозом Y1 и ошибкой E1. |
| [forecast_area_y1.csv](neurosimulator/output/forecast_area_y1.csv) | 17 значений Y1 из вкладки «Прогноз» в порядке строк файла forecast_area.xlsx. |
| [Скриншоты](neurosimulator/screenshots/) | Архитектура сети, загруженные выборки, итоговый график обучения и вкладка «Проверка» перед вычислением. |

Во входных Excel-файлах числовые данные начинаются с A1. X1–X6 — стандартизированные площадь, этаж, этажность, широта, долгота и число дней с 01.01.2018. X7–X16 — индикаторы комнатности, типа дома и кода рынка. При обучении и проверке столбец D1 содержит натуральный логарифм цены в миллионах рублей. Прогноз Y1 переводится в рубли по формуле `1 000 000 × exp(Y1)`. Сеть 16–24–1 обучена методом упругого распространения за 1 000 итераций.
