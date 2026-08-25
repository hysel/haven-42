# Onboarding Setting Security

`config/onboarding-setting-schemas.json` defines the structured advanced controls shared by guided and existing-setup onboarding. `scripts/evaluate-onboarding-configuration.py` evaluates them without resolving a provider, opening a connection, reading a granted path, retrieving a secret, installing software, or causing any other machine effect.

## Authority Boundary

The renderer may submit only a schema version, domain ID, choice ID, and setting values. It cannot submit a configuration state, evidence result, approval, executable, command, arguments, environment, raw endpoint, raw filesystem path, or plaintext credential. Unknown fields and unknown settings are blocked.

Sensitive resources use opaque references:

- `ref:` identifies an engine- or native-authority resource without exposing its value;
- `grant:` identifies a separately issued path grant rather than a raw path;
- `secret:` identifies a native secret-store entry rather than a credential.

The evaluator validates reference shape but never resolves or returns a reference. Resolution belongs to a later native or engine authority and remains subject to its own grant, consent, evidence, and policy checks.

## State Derivation

The evaluator combines renderer settings with a trusted admission created outside the renderer:

- exact admitted base plus no changes is `validated`;
- exact admitted base plus settings inside explicit evidence bounds is `customized`;
- a structurally safe value outside those bounds is `unverified`;
- an unknown, malformed, unsafe, cross-domain, or prohibited value is `blocked`;
- an existing setup cannot inherit validation unless it was independently validated;
- `not-now` is effect-free and remains blocked for that capability.

Only `validated` and `customized` may be eligible for a later execution phase. This decision is not approval and performs no execution. Effects still require disclosure, policy evaluation, and any required effect-bound approval.

## Capability Domains

The initial schemas cover text providers, engineering surfaces, image generation, audio generation, video generation, model management, inference engines, and storage/updates. Audio and video currently have no active capability IDs, so their settings are presentation preparation rather than shipped integrations.

Raw public binding is not an option. Existing provider connections accept only loopback or explicitly trusted-remote scopes, and trusted-remote use still requires the separate privacy and network review. Automatic updates and local model conversion may be structurally representable, but remain unverified until exact evidence and runtime gates exist.

## Test Boundary

The policy self-test covers bounded customization, evidence-boundary overflow, public binding, unknown settings, plaintext credentials, forged state, unvalidated existing setups, deferral, cross-domain admission, and malformed trusted-admission shapes. Windows and shared Linux/macOS pack tests also verify zero evaluator effects and that decisions do not return trusted profile IDs or sensitive reference values. These offline tests do not admit a desktop runtime.
