# Makefile to check connections and run pytest

.PHONY: check-connection test

check-connection:
	@echo "Checking connection"
	@cd tools && python -c 'import sys; import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning); from telephone import check_connection; sys.exit(0 if check_connection() else 1)'

test: check-connection
	@echo "Running Unit Tests for Synthea and Clients"
	@cd tools/tests && pytest
