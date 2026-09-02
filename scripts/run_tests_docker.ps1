Param()

docker build -t journal-search-tests:latest .
docker run --rm -v "${PWD}:/app" journal-search-tests:latest pytest -q
