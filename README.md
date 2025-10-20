# work-time-prediction

This project is an application to predict work start and end times.

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

- POST /api/session/create/: Create new session and return the session id

    ```bash
    curl -X POST "http://127.0.0.1:8000/api/session/create/"
    ```    

- GET /api/session/info: Get session informations
    ```bash
    curl "http://localhost:8000/api/session/info/" \
    -H "X-Session-ID: 188f9fe92fc4fdbd3bcde0e882860bc38af48f6d0f07016f86fdef8d7ff8c672"
    ```

- GET /api/session/list/: List all active sessions of user based on IP address

    ```bash
    curl  "http://localhost:8000/api/session/list/"
    ```

- DELETE /api/session/delete/

    ```bash
    curl "http://localhost:8000/api/session/delete/" \
    -H "X-Session-ID: 188f9fe92fc4fdbd3bcde0e882860bc38af48f6d0f07016f86fdef8d7ff8c672"
    ```

- POST /api/train_models: upload csv, store datas in sqlite database, train model

    ```bash
    curl -X POST "http://127.0.0.1:8000/api/train/" \
        -H "X-Session-ID: 188f9fe92fc4fdbd3bcde0e882860bc38af48f6d0f07016f86fdef8d7ff8c672" \
        -F "file=@/path/to/your/file.csv" \
        -F "id_column=YOUR_ID_COLUMN_NAME" \
        -F "data_column=YOUR_DATE_COLUMN_NAME" \
        -F "start_time_column=YOUR_START_TIME_COLUMN_NAME" \
        -F "end_time_column=YOUR_END_TIME_COLUMN_NAME"
    ```

- POST /api/predict: get predictions

    ```bash
    curl -X POST "http://127.0.0.1:8000/api/predict/" \
        -H "X-Session-ID: 188f9fe92fc4fdbd3bcde0e882860bc38af48f6d0f07016f86fdef8d7ff8c672" \
        -H "Content-Type: application/json" \
        -d '{"id": "1", "target_date": "25/12/2025", "window_size": 30}'
    ```

---

## Docs

Read documentation at http://127.0.0.1:8000/docs

---

## TODO

- improve predictions
- add summarize dataset api
- add security manager
- make tests
- clean code
