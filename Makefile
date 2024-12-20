.PHONY: check-connection test

TEST_FILES := $(wildcard tools/tests/test_*.py)

check-connection:
	@echo "Checking connection"
	@cd tools && python -c 'import sys; from telephone import check_connection; sys.exit(0 if check_connection() else 1)'

test:
	@for file in $(TEST_FILES); do \
		echo "Checking connection before running $$file"; \
		( cd tools && python -c 'import sys; from telephone import check_connection; sys.exit(0 if check_connection() else 1)' ) || { echo "Connection failed. Exiting..."; exit 1; }; \
		echo "Running test $$file"; \
		( cd tools/tests && pytest $$(basename $$file) ) || exit 1; \
	done
