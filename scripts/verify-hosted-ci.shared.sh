#!/usr/bin/env bash
set -uo pipefail

repository=""
commit_sha=""
workflow="Validate Pack"
run_id=""
discovery_timeout=300
poll_interval=10

usage() {
  cat <<'EOF'
Usage: verify-hosted-ci.shared.sh [options]

Options:
  --repository OWNER/REPO
  --commit-sha FULL_SHA
  --workflow NAME
  --run-id ID
  --discovery-timeout-seconds N
  --poll-interval-seconds N
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repository) repository="$2"; shift 2 ;;
    --commit-sha) commit_sha="$2"; shift 2 ;;
    --workflow) workflow="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    --discovery-timeout-seconds) discovery_timeout="$2"; shift 2 ;;
    --poll-interval-seconds) poll_interval="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
done

command -v gh >/dev/null 2>&1 || {
  printf "GitHub CLI was not found. Install gh and authenticate with 'gh auth login'.\n" >&2
  exit 1
}

gh auth status >/dev/null

if [ -z "$repository" ]; then
  repository="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
fi
if [ -z "$commit_sha" ]; then
  commit_sha="$(git rev-parse HEAD)"
fi

case "$commit_sha" in
  *[!0-9a-fA-F]*|'') printf 'Commit SHA must contain exactly 40 hexadecimal characters.\n' >&2; exit 2 ;;
esac
[ "${#commit_sha}" -eq 40 ] || {
  printf 'Commit SHA must contain exactly 40 hexadecimal characters.\n' >&2
  exit 2
}

print_state() {
  printf 'State: %s\nCommit: %s\n' "$1" "$commit_sha"
  [ -n "${2:-}" ] && printf 'Run: %s\n' "$2"
}

print_state "Pushed" ""

if [ -z "$run_id" ]; then
  started_at="$(date +%s)"
  while :; do
    run_id="$(gh run list --repo "$repository" --workflow "$workflow" --commit "$commit_sha" --event push --limit 20 --json databaseId,headSha,createdAt --jq ".[] | select(.headSha == \"$commit_sha\") | .databaseId" | head -n 1)"
    [ -n "$run_id" ] && break
    now="$(date +%s)"
    if [ $((now - started_at)) -ge "$discovery_timeout" ]; then
      print_state "CI failed" ""
      printf "No '%s' push run appeared for exact commit %s within %s seconds.\n" "$workflow" "$commit_sha" "$discovery_timeout" >&2
      exit 1
    fi
    sleep "$poll_interval"
  done
fi

run_sha="$(gh run view "$run_id" --repo "$repository" --json headSha --jq '.headSha')"
run_url="$(gh run view "$run_id" --repo "$repository" --json url --jq '.url')"
if [ "$run_sha" != "$commit_sha" ]; then
  print_state "CI failed" "$run_url"
  printf 'Run %s belongs to %s, not exact commit %s.\n' "$run_id" "$run_sha" "$commit_sha" >&2
  exit 1
fi

print_state "CI running" "$run_url"
watch_exit=0
gh run watch "$run_id" --repo "$repository" --exit-status || watch_exit=$?

run_status="$(gh run view "$run_id" --repo "$repository" --json status --jq '.status')"
run_conclusion="$(gh run view "$run_id" --repo "$repository" --json conclusion --jq '.conclusion')"
jobs="$(gh run view "$run_id" --repo "$repository" --json jobs --jq '.jobs[] | [.name, .status, .conclusion] | @tsv')"

failed=0
[ "$watch_exit" -eq 0 ] || failed=1
[ "$run_status" = "completed" ] || failed=1
[ "$run_conclusion" = "success" ] || failed=1

required_jobs='Wiki synchronization
Windows PowerShell validation
Linux script smoke tests
macOS script smoke tests'
while IFS= read -r required_job; do
  [ -n "$required_job" ] || continue
  if ! printf '%s\n' "$jobs" | awk -F '\t' -v name="$required_job" '$1 == name && $2 == "completed" && $3 == "success" { found=1 } END { exit(found ? 0 : 1) }'; then
    printf "Required job '%s' is missing or unsuccessful.\n" "$required_job" >&2
    failed=1
  fi
done <<EOF
$required_jobs
EOF
if [ "$failed" -ne 0 ]; then
  print_state "CI failed" "$run_url"
  printf 'Failed GitHub Actions logs:\n' >&2
  gh run view "$run_id" --repo "$repository" --log-failed || true
  exit 1
fi

print_state "CI passed" "$run_url"
printf 'Required jobs:\n'
while IFS= read -r required_job; do
  [ -n "$required_job" ] && printf -- '- %s: success\n' "$required_job"
done <<EOF
$required_jobs
EOF
