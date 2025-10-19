# work-time-prediction

This project is an application to predict arrival and departure times at work

---

## Work in Progress

This repository contains work-in-progress code and is not production-ready.
Use at your own risk, and expect frequent change.

---

## Installation

### Prerequisites
- Python **3.12+**
- [Poetry](https://python-poetry.org/)

```bash
git clone https://github.com/EnamSon/work-time-prediction.git
cd work-time-prediction
```

---

## Run the server

The server runs at http://127.0.0.1:8000

```bash
poetry run uvicorn work_time_prediction.main:app --app-dir src
```

### Availables enpoints:
- GET /api/: status check

    ```bash
    curl "http://127.0.0.1:8000/api/"
    ```

- POST /api/train: upload csv, store datas in sqlite database, train model

    ```bash
    curl -X POST "http://127.0.0.1:8000/api/train/" \
        -H "accept: application/json" \
        -F "file=@/path/to/your/file.csv"
    ```

- POST /api/predict: get predictions

    ```bash
    curl -X POST "http://127.0.0.1:8000/api/predict/" \
        -H "accept: application/json" \
        -H "Content-Type: application/json" \
        -d '{"employee_id": "1", "target_date": "25/12/2025"}'
    ```

---

## Docs

Read documentation at http://localhost:8000/docs

---

## Tests

Run the full test suite:

```bash
poetry run pytest
```
