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
        "Set up this computer",
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
    assert "Open the short problem form" in html
    assert "Prepare computer details" in html
    assert "problemReportDetails" in app
    assert "safeProblemReportValue" in app
    assert "navigator.clipboard.writeText(details)" in app
    assert "Local AI model for chat, writing, and summaries" in app
    assert "Technical model name" in app
    assert "Local text model weights" not in app
    assert 'installLocationTitle.textContent = "Install location"' in app
    assert "stored beside the app" in app
    assert "Does not use Program Files or AppData" in app
    assert 'rel="noopener noreferrer"' in html
    assert 'referrerpolicy="no-referrer"' in html

    for section, step_count in (
        ("chat", 6),
        ("models", 5),
        ("system", 5),
        ("technical", 4),
        ("about", 4),
    ):
        assert f'data-tour-section="{section}"' in html, section
        assert f'{section}: Object.freeze(' in app, section
        tour_block = app.split(f'{section}: Object.freeze(', 1)[1].split("}),\n", 1)[0]
        assert tour_block.count("{ target:") == step_count, section
    for phrase in (
        'id="section-tour-dialog" role="dialog" aria-modal="true"',
        'id="section-tour-skip"',
        'id="section-tour-back"',
        'id="section-tour-next"',
        'aria-label="Close this section tour"',
    ):
        assert phrase in html, phrase
    for phrase in (
        'const SECTION_TOUR_STORAGE_KEY = "haven42.section-tours.v1"',
        "sectionTourState[activeSectionTour.section] = true",
        'event.key === "Escape"',
        'event.key !== "Tab"',
        "returnTarget.focus({ preventScroll: true })",
        "target.scrollIntoView({ behavior: motionBehavior()",
        'document.querySelector(".shell").inert = true',
        'document.querySelector(".shell").inert = false',
    ):
        assert phrase in app, phrase
    assert "localStorage" in app
    assert "resume" not in app[app.index("const SECTION_TOURS"):app.index("const state =")].lower()

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
    assert "For first-time Windows Alpha users" in quick_start
    assert "Linux and macOS do not yet have a public beginner package" in quick_start
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
    assert "Retry model download" in app
    assert "installation-component-check" in app
    assert "The model download was interrupted" in app
    assert "System → Troubleshooting logs" in app
    assert "View troubleshooting logs" in app
    assert "Cancel model download" in app
    assert "Calculating speed" in app
    assert "Existing local download data was kept" in app
    assert "Model download complete. The local test stopped" in app
    assert "Retry local AI test" in app
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
    assert "https://github.com/hysel/haven-42/issues/new?template=alpha-bug-report.yml" in html
    assert "label: Package SHA-256" not in bug_form
    assert "label: Haven 42 version" not in bug_form
    assert "label: General computer details" not in bug_form
    assert "Computer details prepared by Haven 42 (optional)" in bug_form
    assert bug_form.count("required: true") == 4
    assert "password:" not in reporting.lower()
    assert "api key:" not in reporting.lower()

    print(f"Novice-experience policy tests passed: {len(required_ui) + len(required_policy) + 54} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
