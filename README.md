# work-time-prediction

This project is an application to predict arrival and departure times at work

---

## Installation

### Prerequisites
- Python **3.12+**
- [Poetry](https://python-poetry.org/)

```bash
git clone https://github.com/EnamSon/work-time-prediction.git
cd work-time-prediction
```

## Run the server

```bash
poetry run uvicorn work_time_prediction.main:app --app-dir src
```

## Tests

Run the full test suite:

```bash
poetry run pytest
```
