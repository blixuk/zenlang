# Transitional shim. Prefer the Zen developer CLI:
#   ./scripts/zen help
#   ./scripts/zen install
#   ./scripts/zen test
#
# Full historical Makefile: archive/Makefile.legacy
# Long-term: self-hosted build tool (.zbuild), not Make.

.PHONY: help install install-bootstrap install-driver install-selfhost install-handoff handoff-soak selfhost-smoke multi-selfhost-smoke test test-core test-parity test-lib test-lib-native clean selfhost selfhost-driver

help:
	@bash scripts/zen help

install selfhost:
	@bash scripts/zen install

install-bootstrap:
	@bash scripts/zen install-bootstrap

install-driver selfhost-driver:
	@bash scripts/zen install-driver

# Stage 7: native selfhost driver binary + E2E smoke
install-selfhost:
	@bash scripts/zen install-selfhost

# Hybrid production entry: selfhost compiler + bootstrap language host
install-handoff:
	@bash scripts/zen install-handoff

handoff-soak:
	@bash scripts/zen handoff-soak

selfhost-smoke:
	@bash scripts/zen selfhost-smoke

# Heavier: multi-unit full selfhost compile + link
multi-selfhost-smoke:
	@bash scripts/zen multi-selfhost-smoke

test:
	@bash scripts/zen test

test-core:
	@bash scripts/zen test-core

test-parity:
	@bash scripts/zen test-parity

test-lib:
	@bash scripts/zen test-lib

test-lib-native:
	@bash scripts/zen test-lib-native

clean:
	@bash scripts/zen clean

# Stage 7 smoke is the supported selfhost verification path.
selfhost-regen:
	@echo "Prefer: make install-selfhost && make selfhost-smoke"
	@bash scripts/zen selfhost-smoke
