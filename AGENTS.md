# Haven 42 repository instructions

## Model-family version certification

- When the owner prompts for model-version research or certification, check official primary sources for newer families and versions of every model family in scope. Do not rely on mutable `latest` tags or community claims as release evidence.
- When a newer version is found, inventory its official release status, license, local weights or registry artifacts, exact tags and digests, supported runtimes, sizes, quantizations, and hardware fit. Keep local, hosted-API-only, announced-but-unreleased, and unavailable candidates visibly distinct.
- Identify every credible candidate that can run on a supported local computer. Prepare a version-pinned capability matrix and a fail-closed soak-test definition for each eligible candidate.
- Preparing a soak does not authorize running it. Do not download a new model, start or reconfigure hardware, or execute a newly prepared soak until the owner explicitly prompts to start that hardware-dependent test.
- Version discovery and test evidence must not change an automatic model default, selection ladder, managed runtime, or release policy without explicit owner approval.
- Never write private lab addresses, host identities, credentials, keys, or other internal infrastructure details to the repository.
