"""Tests for domain_match utility — 10 cases."""
import pytest
from src.utils.domain_match import match_domain, normalize_domain

TARGETS = ["wypasionydraminek.pl", "draminek.pl"]


def test_exact_match():
    assert match_domain("https://wypasionydraminek.pl/produkt/", TARGETS)


def test_www_stripped():
    assert match_domain("https://www.wypasionydraminek.pl", TARGETS)


def test_draminek_exact():
    assert match_domain("https://draminek.pl", TARGETS)


def test_draminek_www():
    assert match_domain("http://www.draminek.pl/sklep/", TARGETS)


def test_subdomain_matches():
    assert match_domain("https://sklep.wypasionydraminek.pl/", TARGETS)


def test_trailing_slash():
    assert match_domain("https://wypasionydraminek.pl/", TARGETS)


def test_no_match_allegro():
    assert not match_domain("https://allegro.pl/szukaj?q=draminek", TARGETS)


def test_no_match_google():
    assert not match_domain("https://google.pl/search?q=draminek", TARGETS)


def test_no_match_similar_name():
    assert not match_domain("https://draminek-podobny.pl", TARGETS)


def test_http_no_prefix():
    # URL without scheme should still be handled
    assert match_domain("wypasionydraminek.pl/oferta", TARGETS)


def test_normalize_strips_www():
    assert normalize_domain("https://www.wypasionydraminek.pl") == "wypasionydraminek.pl"


def test_normalize_lowercase():
    assert normalize_domain("https://WWW.DRAMINEK.PL") == "draminek.pl"
