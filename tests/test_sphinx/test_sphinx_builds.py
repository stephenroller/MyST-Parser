"""Uses sphinx's pytest fixture to run builds.

see conftest.py for fixture usage
"""
import os

import pytest


SOURCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "sourcedirs"))


@pytest.mark.sphinx(
    buildername="html", srcdir=os.path.join(SOURCE_DIR, "basic"), freshenv=True
)
def test_basic(
    app,
    status,
    warning,
    get_sphinx_app_doctree,
    get_sphinx_app_output,
    remove_sphinx_builds,
):
    """basic test."""
    app.build()

    assert "build succeeded" in status.getvalue()  # Build succeeded
    warnings = warning.getvalue().strip()
    assert warnings == ""

    get_sphinx_app_doctree(app, docname="content", regress=True)
    get_sphinx_app_doctree(app, docname="content", resolve=True, regress=True)
    get_sphinx_app_output(app, filename="content.html", regress_html=True)


@pytest.mark.sphinx(
    buildername="html", srcdir=os.path.join(SOURCE_DIR, "references"), freshenv=True
)
def test_references(
    app,
    status,
    warning,
    get_sphinx_app_doctree,
    get_sphinx_app_output,
    remove_sphinx_builds,
):
    """basic test."""
    app.build()

    assert "build succeeded" in status.getvalue()  # Build succeeded
    warnings = warning.getvalue().strip()
    assert warnings == ""

    get_sphinx_app_doctree(app, docname="index", regress=True)
    get_sphinx_app_doctree(app, docname="index", resolve=True, regress=True)
    get_sphinx_app_output(app, filename="index.html", regress_html=True)


@pytest.mark.sphinx(
    buildername="html", srcdir=os.path.join(SOURCE_DIR, "conf_values"), freshenv=True
)
def test_conf_values(
    app,
    status,
    warning,
    get_sphinx_app_doctree,
    get_sphinx_app_output,
    remove_sphinx_builds,
    monkeypatch,
):
    """test setting addition configuration values."""
    from myst_parser.sphinx_renderer import SphinxRenderer

    monkeypatch.setattr(SphinxRenderer, "_random_label", lambda self: "mock-uuid")
    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded
    warnings = warning.getvalue().strip()
    assert warnings == ""

    try:
        get_sphinx_app_doctree(app, docname="index", regress=True)
    finally:
        get_sphinx_app_output(app, filename="index.html", regress_html=True)


@pytest.mark.sphinx(
    buildername="html", srcdir=os.path.join(SOURCE_DIR, "includes"), freshenv=True
)
def test_includes(
    app,
    status,
    warning,
    get_sphinx_app_doctree,
    get_sphinx_app_output,
    remove_sphinx_builds,
):
    """Test of include directive."""
    app.build()

    assert "build succeeded" in status.getvalue()  # Build succeeded
    warnings = warning.getvalue().strip()
    assert warnings == ""

    try:
        get_sphinx_app_doctree(app, docname="index", regress=True)
    finally:
        get_sphinx_app_output(app, filename="index.html", regress_html=True)


@pytest.mark.sphinx(
    buildername="html", srcdir=os.path.join(SOURCE_DIR, "footnotes"), freshenv=True
)
def test_footnotes(
    app,
    status,
    warning,
    get_sphinx_app_doctree,
    get_sphinx_app_output,
    remove_sphinx_builds,
):
    """Test of include directive."""
    app.build()

    assert "build succeeded" in status.getvalue()  # Build succeeded
    warnings = warning.getvalue().strip()
    assert warnings == ""

    try:
        get_sphinx_app_doctree(app, docname="footnote_md", regress=True)
    finally:
        get_sphinx_app_output(app, filename="footnote_md.html", regress_html=True)


@pytest.mark.sphinx(
    buildername="html",
    srcdir=os.path.join(SOURCE_DIR, "commonmark_only"),
    freshenv=True,
)
def test_commonmark_only(
    app,
    status,
    warning,
    get_sphinx_app_doctree,
    get_sphinx_app_output,
    remove_sphinx_builds,
):
    """test setting addition configuration values."""
    app.build()
    assert "build succeeded" in status.getvalue()  # Build succeeded
    warnings = warning.getvalue().strip()
    assert "lexer name '{note}'" in warnings

    try:
        get_sphinx_app_doctree(app, docname="index", regress=True)
    finally:
        get_sphinx_app_output(app, filename="index.html", regress_html=True)
