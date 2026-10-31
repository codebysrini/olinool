"""`python -m olinool.conformance` — self-certify an installed olinool."""
import sys

from olinool.conformance import certify

sys.exit(certify())
