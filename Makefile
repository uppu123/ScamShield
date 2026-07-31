.PHONY: install api frontend test train lint

install:
	pip install -r requirements.txt -r requirements-dev.txt

api:
	python -m backend.app

frontend:
	streamlit run frontend/app.py

test:
	pytest -q

train:
	python ml/train.py --data data/raw/emscad.csv
