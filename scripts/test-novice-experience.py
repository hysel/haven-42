#!/usr/bin/env python3
"""Keep the primary Haven 42 experience understandable to local-AI novices."""

from __future__ import annotations

import json
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
    repository_instructions = read("AGENTS.md")
    quick_start = read("docs/wiki-quick-start.md")
    glossary = read("docs/wiki-glossary.md")
    navigation = read("config/wiki-navigation.tsv")
    sync = read("config/wiki-sync.tsv")
    issue_config = read(".github/ISSUE_TEMPLATE/config.yml")
    bug_form = read(".github/ISSUE_TEMPLATE/alpha-bug-report.yml")
    feedback_form = read(".github/ISSUE_TEMPLATE/alpha-feedback.yml")
    model_test_form = read(".github/ISSUE_TEMPLATE/model-test-request.yml")
    download_guide = read("docs/windows-alpha-download-and-feedback.md")
    power_evidence = read("docs/wiki-model-power-evidence.md")
    power_coverage = json.loads(read("config/alpha-2-gpu-power-coverage.json"))

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
        ("system", 6),
        ("technical", 4),
        ("about", 4),
    ):
        assert f'data-tour-section="{section}"' in html, section
        assert f'{section}: Object.freeze(' in app, section
        tour_block = app.split(f'{section}: Object.freeze(', 1)[1].split("}),\n", 1)[0]
        assert tour_block.count("{ target:") == step_count, section
    assert 'id="energy-estimator-panel"' in html
    assert "This estimates graphics-card electricity only" in html
    assert "does not detect your location or change your model choice" in html
    assert "Use the price from my electricity bill · most accurate" in html
    assert "Use an average U.S. household price" in html
    assert "Use an average European household price" in html
    assert "Country and usual currency" in html
    assert "United States — USD" in html
    assert "Germany — EUR" in html
    assert "Another country — enter currency below" in html
    assert "Keep kWh and price in the status sidebar" in html
    assert "Its values are not saved and disappear when the app closes" in html
    assert "Your electricity-bill information stays private" in html
    for card in (
        "GeForce GTX 1650 Super 4 GiB",
        "GeForce RTX 3060 12 GiB",
        "Quadro RTX 5000 16 GiB",
        "Tesla V100 32 GiB",
        "Radeon RX 580 8 GiB",
        "Radeon RX 6800 non-XT 16 GiB",
        "Radeon RX 7800 XT 16 GiB",
        "Intel Arc B580 12 GiB",
    ):
        assert card in power_evidence, card
    assert power_coverage["kind"] == "haven42-gpu-power-coverage"
    assert power_coverage["policy"]["everyPhysicalCardModelRequiresReference"] is True
    assert power_coverage["policy"]["singleAndMultiGpuConfigurationsRemainDistinct"] is True
    assert power_coverage["policy"]["missingMeasurementMeansUnknownNotZero"] is True
    assert len(power_coverage["hardware"]) == 8
    allowed_power_statuses = set(power_coverage["allowedStatuses"])
    for hardware in power_coverage["hardware"]:
        assert hardware["status"] in allowed_power_statuses, hardware["id"]
        display_name = f'{hardware["model"]} {hardware["memoryGiB"]} GiB'
        assert display_name in power_evidence, display_name
        for evidence_path in hardware["measurementEvidence"]:
            assert (ROOT / evidence_path).is_file(), evidence_path
        if hardware["status"] == "measured":
            assert hardware["measurementEvidence"], hardware["id"]
    quadro = next(item for item in power_coverage["hardware"] if item["id"] == "nvidia-quadro-rtx-5000-16g")
    assert quadro["status"] == "measured"
    v100 = next(item for item in power_coverage["hardware"] if item["id"] == "nvidia-tesla-v100-32g")
    assert v100["status"] == "measured"
    assert len(v100["measurementEvidence"]) == 3
    assert "151.060 W active average" in power_evidence
    assert "152.509 W active average" in power_evidence
    assert "unmeasured card cannot be mistaken for a zero-power result" in power_evidence
    assert "Single-card and two-card records are available" in power_evidence
    for phrase in (
        '"Processor", processor',
        '"Available space", storage',
        '"Linux kernel"',
        '"Desktop session"',
        '"Linux compatibility"',
        'graphics memory Unavailable',
        '`${item.driverName} · version ${item.driverVersion || "Unavailable"}`',
        '"amd-runtime": "AMD graphics tools"',
        '"intel-runtime": "Intel graphics tools"',
        'function linuxSetupRemediation(blockers)',
        'This portable local AI engine requires a glibc-based Linux distribution.',
        'Free more space beside Haven 42, then run the computer check again.',
    ):
        assert phrase in app, phrase
    assert "Closing Haven 42 clears them" in html
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
        "sectionTourState[activeSectionTour.section] = configuration.revision",
        "sectionTourState[section] === configuration.revision",
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

    for phrase in (
        "UI accessibility and compatibility lifecycle",
        "They are not a one-time audit",
        "increment only that section's revision",
        "Automated checks do not replace",
        "accessibility or supported-platform regression as a release blocker",
    ):
        assert phrase in repository_instructions, phrase
    for phrase in (
        "README and wiki documentation lifecycle",
        "Maintain one canonical source for each topic",
        "README stays concise and points to those sources",
        "single Engineering and Validation Index",
        "linear Quick Start to Using Haven 42 to Troubleshooting flow",
        "Do not declare documentation complete while the two repositories disagree",
    ):
        assert phrase in repository_instructions, phrase
    for phrase in (
        "accessibility and compatibility lifecycle",
        "materially changed section tour increments only that section's revision",
        "without implying certification",
    ):
        assert phrase in contributing, phrase

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

    reporting = (
        f"{issue_config}\n{bug_form}\n{feedback_form}\n{model_test_form}\n"
        f"{download_guide}"
    )
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
    for phrase in (
        "name: Request a model test",
        "Which model would you like us to test?",
        "Official model page (optional)",
        "What would you like to use this model for?",
        "What kind of computer should we consider? (optional)",
        "does not guarantee the model will be downloaded, tested, supported",
    ):
        assert phrase in model_test_form, phrase
    assert "multiple: true" in model_test_form
    assert model_test_form.count("required: true") == 5
    assert "https://github.com/hysel/haven-42/issues/new?template=model-test-request.yml" in read(
        "README.md"
    )
    assert "password:" not in reporting.lower()
    assert "api key:" not in reporting.lower()

    print(f"Novice-experience policy tests passed: {len(required_ui) + len(required_policy) + 63} checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
