---
name: Infrastructure As Code Engineering
optional: true
globs: ["**/*.tf", "**/*.tfvars", "**/*.hcl", "**/Dockerfile*", "**/docker-compose*.yml", "**/docker-compose*.yaml", "**/compose*.yml", "**/compose*.yaml", "**/Chart.yaml", "**/values*.yaml", "**/values*.yml", ".github/workflows/*.yml", ".github/workflows/*.yaml"]
---

## Scope

Use this optional rule pack only when project detection confirms Infrastructure as Code evidence.

Strong Infrastructure as Code evidence includes Terraform files, OpenTofu files, Kubernetes manifests, Helm charts, Dockerfiles, Compose files, GitHub Actions workflows, cloud deployment templates, or inspected infrastructure docs.

If Infrastructure as Code evidence is absent or unreadable, do not apply this rule pack. Keep recommendations language-neutral and mark Terraform, Kubernetes, Docker, CI, cloud provider, and deployment assumptions as `unconfirmed`.

## Required Practices

- Identify the IaC tool, cloud/provider target, environment model, and deployment workflow from inspected files before recommending commands.
- Preserve existing module boundaries, naming conventions, state strategy, and promotion flow unless migration is explicitly requested.
- Treat state files, secrets, credentials, cloud identities, network rules, IAM policies, image tags, and deployment permissions as high-risk.
- Prefer least privilege, pinned or controlled versions, reproducible builds, and explicit environment separation.
- For Terraform/OpenTofu, review providers, state backend assumptions, variables, outputs, modules, lifecycle settings, and plan/apply separation.
- For Kubernetes, review namespaces, resource requests/limits, probes, secrets, RBAC, image pull policy, and rollout/rollback behavior.
- For CI/CD, review permissions, secrets usage, branch/tag triggers, artifact handling, and failure visibility.

## Avoid

- Assuming AWS, Azure, GCP, Terraform, Kubernetes, Helm, Docker, GitHub Actions, or another platform without repository evidence.
- Suggesting live `apply`, deploy, destroy, or credential-changing commands unless explicitly requested and reviewed.
- Committing secrets, generated state, local kubeconfigs, provider credentials, or environment-specific private endpoints.
- Recommending broad IAM permissions or public network exposure without a documented reason.
- Treating static syntax checks as enough for runtime deployment safety.

## Review Checklist

- Which files prove this is an Infrastructure as Code project?
- Which platform, toolchain, environment model, and deployment flow are confirmed versus `unconfirmed`?
- Are state, secrets, permissions, networking, and rollback risks addressed?
- Are validation steps split between static checks, plan review, and approved deployment actions?
- Do recommendations avoid live infrastructure changes unless explicitly authorized?
