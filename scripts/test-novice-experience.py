#!/usr/bin/env python3
"""Keep the primary Haven 42 experience understandable to local-AI novices."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    html = read("web/static/index.html")
    app = read("web/static/app.js")
    style = read("STYLEGUIDE.md")
    ai_guide = read("AI.md")
    contributing = read("CONTRIBUTING.md")
    quick_start = read("docs/wiki-quick-start.md")
    glossary = read("docs/wiki-glossary.md")
    navigation = read("config/wiki-navigation.tsv")
    sync = read("config/wiki-sync.tsv")
    issue_config = read(".github/ISSUE_TEMPLATE/config.yml")
    bug_form = read(".github/ISSUE_TEMPLATE/alpha-bug-report.yml")
    feedback_form = read(".github/ISSUE_TEMPLATE/alpha-feedback.yml")
    download_guide = read("docs/windows-alpha-download-and-feedback.md")

    required_ui = (
        "Set up this computer · Recommended",
        "Use another AI server · Advanced",
        "Look around first",
        "Choose for me · Recommended",
        "What Haven 42 will do · details",
        "Your permission is required",
        "Technical test details",
        "Private session · no tracking",
    )
    for phrase in required_ui:
        assert phrase in html or phrase in app, phrase
    assert html.count("data-wizard-progress=") == 3
    assert "STEP 4" not in html
    assert "Report an Alpha problem" in html
    assert 'rel="noopener noreferrer"' in html
    assert 'referrerpolicy="no-referrer"' in html

    required_policy = (
        "novice-first",
        "clearly labelled **Advanced**",
        "plain language",
    )
    combined_policy = f"{style}\n{ai_guide}\n{contributing}".lower()
    for phrase in required_policy:
        assert phrase.lower() in combined_policy, phrase

    for term in ("AI model", "Ollama", "AI server", "Token", "Portable package", "Quantization"):
        assert term in glossary, term
    assert "For first-time users" in quick_start
    assert "Glossary.md\tCommon Words" in navigation
    assert "docs/wiki-glossary.md\tGlossary.md\tCommon Words" in sync

    primary_html = html[: html.index('id="assurance-panel"')]
    for expert_only in (
        "Request blocked:",
        "Repository access",
        "Local session · no telemetry",
        "Provider connection",
    ):
        assert expert_only not in primary_html, expert_only
    assert "Request blocked: ${error.message}" not in app
    assert "summary.textContent = plan.summary" not in app
    assert "status.error ? ` · ${status.error}`" not in app
    assert '"Provider not connected"' not in app
    assert "relevantSoftware(item.componentId)" in app
    assert ".innerHTML" not in app

    reporting = f"{issue_config}\n{bug_form}\n{feedback_form}\n{download_guide}"
    for phrase in (
        "blank_issues_enabled: false",
        "private vulnerability reporting",
        "Do not include",
        "Privacy confirmation",
        "Get-FileHash -Algorithm SHA256",
        "Do not disable antivirus, SmartScreen, Secure Boot",
        "Never paste raw logs",
    ):
        assert phrase in reporting, phrase
    assert "https://github.com/hysel/haven-42/issues/new/choose" in html
    assert "password:" not in reporting.lower()
    assert "api key:" not in reporting.lower()

    print(f"Novice-experience policy tests passed: {len(required_ui) + len(required_policy) + 31} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
