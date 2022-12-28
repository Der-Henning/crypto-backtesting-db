install:
	pip install -r requirements-dev.txt

lint:
	pre-commit run -a

test:
	python -m pytest --cov src/

image:
	docker build --tag cryptodb:latest .
