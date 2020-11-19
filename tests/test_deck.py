"""
Tests for the application module.
"""
import os
import random
import re
from tempfile import mkstemp
from unittest import mock

import pytest
from pinochle import deck


def test_pinochle_deck():
    test_deck = deck.create_deck()
    assert test_deck.size == 48
    assert test_deck.find_list(["2", "3", "4", "5", "6", "7", "8"]) == []


# def test_cmdline_seed_spec():
#     for arg in ["-s", "--seed="]:
#         pool_list: list = list(valid_pairs.keys())
#         random.shuffle(pool_list)
#         # Seed #0 is "special" even though it's otherwise a valid seed.
#         for item in [1, 254, 65536, 38572, 2319457662, 1726153]:
#             pool = pool_list.pop()
#             fd, path = mkstemp()
#             with mock.patch(
#                 "sys.argv", [""] + [f"-f{path}", f"-p{pool}", f"{arg}{item}"]
#             ):
#                 application()
#             with open(fd, "r") as f:
#                 captured: str = f.read()
#             os.unlink(path)
#             assert f"Exam number: {item}" in str(captured)
#             assert f"{valid_pairs[pool]}" in str(captured)


# def test_user_prompt():
#     for item in valid_pairs.keys():
#         fd, path = mkstemp()
#         with mock.patch("sys.argv", [""] + [f"-f{path}"]), mock.patch(
#             "examgenerator.pool_choice._get_input", return_value=item
#         ):
#             application()
#         with open(fd, "r") as f:
#             captured: str = f.read()
#         os.unlink(path)
#         assert valid_pairs[item] in str(captured)


# def test_text_output():
#     for item in valid_pairs.keys():
#         fd, path = mkstemp()
#         with mock.patch(
#             "sys.argv", [""] + [f"-f{path}"] + ["-p", f"{item}", "-j", "text.j2"]
#         ):
#             application()
#         with open(fd, "r") as f:
#             captured: str = f.read()
#         os.unlink(path)
#         assert r"------------------------" in str(captured)
#         assert r'content="Amateur Radio Example Exams"' not in str(captured)
#         assert r"begin{enumerate}" not in str(captured)


# def test_html_output():
#     for item in valid_pairs.keys():
#         fd, path = mkstemp()
#         with mock.patch(
#             "sys.argv", [""] + [f"-f{path}"] + ["-p", f"{item}", "-j", "html.j2"]
#         ):
#             application()
#         with open(fd, "r") as f:
#             captured: str = f.read()
#         os.unlink(path)
#         assert r"------------------------" not in str(captured)
#         assert r'content="Amateur Radio Example Exams"' in str(captured)
#         assert r"begin{enumerate}" not in str(captured)


# def test_latex_output():
#     for item in valid_pairs.keys():
#         fd, path = mkstemp()
#         with mock.patch(
#             "sys.argv", [""] + [f"-f{path}"] + ["-p", f"{item}", "-j", "latex.j2"]
#         ):
#             application()
#         with open(fd, "r") as f:
#             captured: str = f.read()
#         os.unlink(path)
#         assert r"------------------------" not in str(captured)
#         assert r'content="Amateur Radio Example Exams"' not in str(captured)
#         assert r"begin{enumerate}" in str(captured)


# def test_admonition_abcd_dcba():
#     for rand in ["ABCD", "abcd", "DCBA", "dcba"]:
#         for o_type in ["text.j2", "html.j2", "latex.j2"]:
#             for item in valid_pairs.keys():
#                 fd, path = mkstemp()
#                 with mock.patch(
#                     "sys.argv",
#                     [""]
#                     + [f"-f{path}"]
#                     + ["-p", f"{item}", "-r", f"{rand}", "-j", f"{o_type}"],
#                 ):
#                     application()
#                 with open(fd, "r") as f:
#                     captured: str = f.read()
#                 os.unlink(path)
#                 assert r"NOT A VALID AMATEUR RADIO EXAM" in str(captured)


# def test_stdout(capsys):
#     with mock.patch("sys.argv", [""] + [f"-f-"] + [f"-p1"]):
#         application()
#     captured, err = capsys.readouterr()
#     assert "Technician" in str(captured)


# def test_missing_dbfile(capsys):
#     with pytest.raises(SystemExit):
#         with mock.patch("examgenerator.constants.EXAMDB_FILE", None), mock.patch(
#             "sys.argv", [""] + ["-d", "nodatabase", "-p", "1"]
#         ):
#             application()
#     captured, err = capsys.readouterr()
#     assert "Database nodatabase is not an existing file." in str(captured)
