.PHONY: check-connection test test-pipeline

TEST_FILES := $(wildcard tools/tests/test_*.py)
PIPELINE_TEST_FILES := tools/tests/test_telephone.py tools/tests/test_diff.py

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

test-pipeline:
	@for file in $(PIPELINE_TEST_FILES); do \
		echo "Running test $$(basename $$file)"; \
		( cd tools/tests && pytest $$(basename $$file) ) || exit 1; \
	done