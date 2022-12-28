install:
	pip install -r requirements-dev.txt

lint:
	pre-commit run -a
