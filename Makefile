# Makefile to run pytest


.PHONY: test


test:
	@echo "Running Unit Tests for Synthea and Clients"
	@cd tools/tests && pytest

