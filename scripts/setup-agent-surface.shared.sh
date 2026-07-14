#!/usr/bin/env bash
set -euo pipefail

SURFACE="aider"
ACTION="Plan"
TARGET_REPO=""
MODEL=""
RECOMMENDATION_PATH=""
LANE="WriteSafe"
OLLAMA_BASE_URL="http://127.0.0.1:11434"
INSTALL_METHOD="aider-install"
AIDER_COMMAND="aider"
DRY_RUN=0
FORCE=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --surface|-Surface) SURFACE="$2"; shift 2 ;;
    --action|-Action) ACTION="$2"; shift 2 ;;
    --target-repo|-TargetRepo) TARGET_REPO="$2"; shift 2 ;;
    --model|-Model) MODEL="$2"; shift 2 ;;
    --recommendation-path|-RecommendationPath) RECOMMENDATION_PATH="$2"; shift 2 ;;
    --lane|-Lane) LANE="$2"; shift 2 ;;
    --ollama-base-url|-OllamaBaseUrl) OLLAMA_BASE_URL="$2"; shift 2 ;;
    --install-method|-InstallMethod) INSTALL_METHOD="$2"; shift 2 ;;
    --aider-command|-AiderCommand) AIDER_COMMAND="$2"; shift 2 ;;
    --dry-run|-DryRun) DRY_RUN=1; shift ;;
    --force|-Force) FORCE=1; shift ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; exit 1 ;;
  esac
done

[ "$SURFACE" = "aider" ] || { printf 'Unsupported surface: %s\n' "$SURFACE" >&2; exit 1; }
case "$ACTION" in Plan|Install|Configure|Health) ;; *) printf 'Unsupported action: %s\n' "$ACTION" >&2; exit 1 ;; esac
case "$LANE" in WriteSafe|PlanOnly|DeepReview) ;; *) printf 'Unsupported lane: %s\n' "$LANE" >&2; exit 1 ;; esac
case "$INSTALL_METHOD" in aider-install|pipx|uv) ;; *) printf 'Unsupported install method: %s\n' "$INSTALL_METHOD" >&2; exit 1 ;; esac

config_name=".aider.conf.local.yml"

print_install_plan() {
  case "$INSTALL_METHOD" in
    pipx) printf '%s\n' 'python3 -m pip install pipx' 'pipx install aider-chat' ;;
    uv) printf '%s\n' 'python3 -m pip install uv' 'uv tool install --force --python python3.12 --with pip aider-chat@latest' ;;
    *) printf '%s\n' 'python3 -m pip install aider-install' 'aider-install' ;;
  esac
}

if [ "$ACTION" = "Plan" ]; then
  printf 'Surface: Aider\nInstall method: %s\n' "$INSTALL_METHOD"
  print_install_plan | sed 's/^/Install step: /'
  printf 'Config file: %s\nLaunch command: %s --config %s\nSafety: generated config is local-only and must not be committed.\n' "$config_name" "$AIDER_COMMAND" "$config_name"
  exit 0
fi

if [ "$ACTION" = "Install" ]; then
  print_install_plan | sed 's/^/Aider install step: /'
  [ "$DRY_RUN" -eq 0 ] || { printf 'Dry run complete; no network install was executed.\n'; exit 0; }
  case "$INSTALL_METHOD" in
    pipx) python3 -m pip install pipx; pipx install aider-chat ;;
    uv) python3 -m pip install uv; uv tool install --force --python python3.12 --with pip aider-chat@latest ;;
    *) python3 -m pip install aider-install; aider-install ;;
  esac
  printf 'Aider installation completed. Run this script with --action Health next.\n'
  exit 0
fi

[ -n "$TARGET_REPO" ] || { printf 'Target repo is required for %s.\n' "$ACTION" >&2; exit 1; }
[ -d "$TARGET_REPO" ] || { printf 'Target repo does not exist: %s\n' "$TARGET_REPO" >&2; exit 1; }
target_repo="$(cd "$TARGET_REPO" && pwd)"
config_path="$target_repo/$config_name"

if [ "$ACTION" = "Configure" ]; then
  command -v python3 >/dev/null 2>&1 || { printf 'python3 is required to generate Aider config.\n' >&2; exit 1; }
  if [ -z "$MODEL" ]; then
    [ -n "$RECOMMENDATION_PATH" ] || { printf 'Model or recommendation path is required for Configure.\n' >&2; exit 1; }
    [ -f "$RECOMMENDATION_PATH" ] || { printf 'Recommendation path does not exist.\n' >&2; exit 1; }
    MODEL="$(python3 - "$RECOMMENDATION_PATH" "$LANE" <<'PY'
import json, sys
with open(sys.argv[1], "r", encoding="utf-8") as handle:
    report = json.load(handle)
value = report.get("Recommendation", {}).get(sys.argv[2] + "Model")
if not value:
    raise SystemExit("Recommendation does not contain the requested lane model.")
print(value)
PY
)"
  fi
  [[ "$MODEL" =~ ^[A-Za-z0-9._:/-]+$ ]] || { printf 'Model contains unsupported characters.\n' >&2; exit 1; }
  if [ -e "$config_path" ] && [ "$FORCE" -eq 0 ]; then printf '%s already exists. Use --force to replace it.\n' "$config_name" >&2; exit 1; fi
  printf 'Aider config target: %s\nSelected lane/model: %s / %s\n' "$config_path" "$LANE" "$MODEL"
  [ "$DRY_RUN" -eq 0 ] || { printf 'Dry run complete; no config was written.\n'; exit 0; }
  python3 - "$config_path" "$MODEL" "$OLLAMA_BASE_URL" <<'PY'
import pathlib, sys
from urllib.parse import urlsplit
path, model, endpoint = sys.argv[1:4]
parsed = urlsplit(endpoint)
if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password or parsed.query or parsed.fragment:
    raise SystemExit("Ollama base URL must be absolute HTTP(S) without credentials, query, or fragment.")
endpoint = endpoint.rstrip("/")
text = f"""# Generated local-only Aider config. Do not commit this file.
model: ollama_chat/{model}
set-env:
  - OLLAMA_API_BASE={endpoint}
auto-commits: false
dirty-commits: false
gitignore: false
check-update: false
analytics-disable: true
map-tokens: 0
line-endings: platform"""
pathlib.Path(path).write_text(text, encoding="utf-8")
PY
  if [ -d "$target_repo/.git" ]; then
    mkdir -p "$target_repo/.git/info"
    touch "$target_repo/.git/info/exclude"
    grep -Fxq "$config_name" "$target_repo/.git/info/exclude" || printf '%s\n' "$config_name" >> "$target_repo/.git/info/exclude"
  fi
  printf 'Aider config written. Launch with: %s --config %s\n' "$AIDER_COMMAND" "$config_name"
  exit 0
fi

failures=0
if command -v "$AIDER_COMMAND" >/dev/null 2>&1; then printf 'PASS aider-command: %s is available\n' "$AIDER_COMMAND"; else printf 'FAIL aider-command: %s was not found on PATH\n' "$AIDER_COMMAND"; failures=$((failures + 1)); fi
if [ -f "$config_path" ]; then
  printf 'PASS local-config: %s\n' "$config_name"
  grep -q '^model: ollama_chat/' "$config_path" || { printf 'FAIL ollama-model\n'; failures=$((failures + 1)); }
  grep -q '^auto-commits: false$' "$config_path" && grep -q '^dirty-commits: false$' "$config_path" || { printf 'FAIL safe-git-mode\n'; failures=$((failures + 1)); }
else
  printf 'FAIL local-config: %s\n' "$config_name"
  failures=$((failures + 1))
fi
[ "$failures" -eq 0 ] || exit 1
printf 'Aider adapter health: healthy\n'
