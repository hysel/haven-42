#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_ROOT="$REPO_ROOT/runtime-validation-output/sample-repositories"
FORCE=false
LIST=false
SAMPLES=(
  "python-api"
  "typescript-frontend"
  "node-service"
  "java-spring-api"
  "go-service"
  "rust-cli"
  "iac-terraform-kubernetes"
  "sql-migrations"
  "python-layered-api"
  "typescript-service-medium"
  "multi-language-platform"
)

usage() {
  cat <<'EOF_USAGE'
Usage: generate-sample-repositories.shared.sh [--output-root <path>] [--force] [--list]

Creates disposable local validation repositories. Generated output is not a production starter template.
EOF_USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --output-root|-OutputRoot)
      if [ "$#" -lt 2 ]; then
        printf 'Missing value for %s\n' "$1" >&2
        exit 1
      fi
      OUTPUT_ROOT="$2"
      shift 2
      ;;
    --force|-Force)
      FORCE=true
      shift
      ;;
    --list|-List)
      LIST=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [ "$LIST" = true ]; then
  printf '%s\n' "${SAMPLES[@]}"
  exit 0
fi

case "$OUTPUT_ROOT" in
  /*) ;;
  *) OUTPUT_ROOT="$REPO_ROOT/$OUTPUT_ROOT" ;;
esac

write_file() {
  sample_root="$1"
  relative_path="$2"
  path="$sample_root/$relative_path"
  mkdir -p "$(dirname "$path")"
  cat > "$path"
}

new_sample_root() {
  name="$1"
  sample_root="$OUTPUT_ROOT/$name"
  if [ -e "$sample_root" ] && [ "$FORCE" != true ]; then
    printf "Sample '%s' already exists at '%s'. Use --force to overwrite generated samples.\n" "$name" "$sample_root" >&2
    exit 1
  fi
  rm -rf "$sample_root"
  mkdir -p "$sample_root"
  printf '%s' "$sample_root"
}

add_metadata() {
  sample_root="$1"
  name="$2"
  ecosystem="$3"
  purpose="$4"
  complexity="${5:-minimal}"
  write_file "$sample_root" "SAMPLE-METADATA.md" <<EOF_METADATA
# Sample Metadata

Name: $name
Ecosystem: $ecosystem
Purpose: $purpose
Complexity: $complexity
Generated: deterministic local fixture

This repository is a disposable validation sample for Haven 42. It is not a production starter template.
EOF_METADATA
}

mkdir -p "$OUTPUT_ROOT"

root="$(new_sample_root python-api)"
add_metadata "$root" "python-api" "Python" "API-style repository discovery and review validation."
write_file "$root" "README.md" <<'EOF_FILE'
# Python API Sample

Small Python API-style sample used for local agent validation.

## Commands

Create a local virtual environment before running tests. The environment and
test cache are ignored by Git.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip pytest
python -m pytest
python -m app.main
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip pytest
python -m pytest
python -m app.main
```
EOF_FILE

write_file "$root" ".gitignore" <<'EOF_FILE'
.venv/
__pycache__/
.pytest_cache/
EOF_FILE

write_file "$root" "pyproject.toml" <<'EOF_FILE'
[project]
name = "sample-python-api"
version = "0.1.0"
description = "Generated Python API validation fixture"
requires-python = ">=3.9"

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF_FILE

write_file "$root" "app/main.py" <<'EOF_FILE'
from app.settings import Settings


def build_health_response(settings: Settings) -> dict[str, str]:
    return {"service": settings.service_name, "status": "ok"}


if __name__ == "__main__":
    print(build_health_response(Settings()))
EOF_FILE
write_file "$root" "app/settings.py" <<'EOF_FILE'
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str = "sample-python-api"
EOF_FILE
write_file "$root" "tests/test_main.py" <<'EOF_FILE'
from app.main import build_health_response
from app.settings import Settings


def test_build_health_response():
    assert build_health_response(Settings()) == {"service": "sample-python-api", "status": "ok"}
EOF_FILE

root="$(new_sample_root typescript-frontend)"
add_metadata "$root" "typescript-frontend" "TypeScript" "Frontend repository discovery and review validation."
write_file "$root" "README.md" <<'EOF_FILE'
# TypeScript Frontend Sample

Small TypeScript frontend-style sample used for local agent validation.
EOF_FILE
write_file "$root" "package.json" <<'EOF_FILE'
{
  "name": "typescript-frontend-sample",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest run",
    "build": "tsc --noEmit"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest"
  },
  "devDependencies": {
    "typescript": "latest",
    "vitest": "latest"
  }
}
EOF_FILE
write_file "$root" "tsconfig.json" <<'EOF_FILE'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "strict": true,
    "jsx": "react-jsx"
  }
}
EOF_FILE
write_file "$root" "src/App.tsx" <<'EOF_FILE'
export function App() {
  return <main><h1>Sample frontend</h1></main>;
}
EOF_FILE
write_file "$root" "src/app.test.ts" <<'EOF_FILE'
import { describe, expect, it } from 'vitest';

describe('sample frontend', () => {
  it('has a placeholder test', () => {
    expect('frontend').toBe('frontend');
  });
});
EOF_FILE

root="$(new_sample_root node-service)"
add_metadata "$root" "node-service" "Node.js" "Node service repository discovery and review validation."
write_file "$root" "README.md" <<'EOF_FILE'
# Node Service Sample

Small Node service-style sample used for local agent validation.
EOF_FILE
write_file "$root" "package.json" <<'EOF_FILE'
{
  "name": "node-service-sample",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node src/server.js",
    "test": "node --test"
  }
}
EOF_FILE
write_file "$root" "src/server.js" <<'EOF_FILE'
export function createHealthPayload() {
  return { service: 'node-service-sample', status: 'ok' };
}
EOF_FILE
write_file "$root" "test/server.test.js" <<'EOF_FILE'
import test from 'node:test';
import assert from 'node:assert/strict';
import { createHealthPayload } from '../src/server.js';

test('health payload', () => {
  assert.equal(createHealthPayload().status, 'ok');
});
EOF_FILE
write_file "$root" "Dockerfile" <<'EOF_FILE'
FROM node:22-alpine
WORKDIR /app
COPY package.json ./
COPY src ./src
CMD ["node", "src/server.js"]
EOF_FILE

root="$(new_sample_root java-spring-api)"
add_metadata "$root" "java-spring-api" "Java" "Java/Spring-style repository discovery and review validation."
write_file "$root" "README.md" <<'EOF_FILE'
# Java Spring API Sample

Small Java/Spring-style sample used for local agent validation.
EOF_FILE
write_file "$root" "pom.xml" <<'EOF_FILE'
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId>
  <artifactId>java-spring-api-sample</artifactId>
  <version>0.1.0</version>
</project>
EOF_FILE
write_file "$root" "src/main/java/example/HealthController.java" <<'EOF_FILE'
package example;

public final class HealthController {
    public String status() {
        return "ok";
    }
}
EOF_FILE
write_file "$root" "src/test/java/example/HealthControllerTest.java" <<'EOF_FILE'
package example;

class HealthControllerTest {
    void returnsOk() {
        assert "ok".equals(new HealthController().status());
    }
}
EOF_FILE
write_file "$root" "src/main/resources/application.properties" <<'EOF_FILE'
spring.application.name=java-spring-api-sample
EOF_FILE

root="$(new_sample_root go-service)"
add_metadata "$root" "go-service" "Go" "Go service repository discovery and review validation."
write_file "$root" "README.md" <<'EOF_FILE'
# Go Service Sample

Small Go service-style sample used for local agent validation.
EOF_FILE
write_file "$root" "go.mod" <<'EOF_FILE'
module example.com/go-service-sample

go 1.22
EOF_FILE
write_file "$root" "cmd/server/main.go" <<'EOF_FILE'
package main

import "fmt"

func healthStatus() string {
	return "ok"
}

func main() {
	fmt.Println(healthStatus())
}
EOF_FILE
write_file "$root" "cmd/server/main_test.go" <<'EOF_FILE'
package main

import "testing"

func TestHealthStatus(t *testing.T) {
	if healthStatus() != "ok" {
		t.Fatal("expected ok")
	}
}
EOF_FILE

root="$(new_sample_root rust-cli)"
add_metadata "$root" "rust-cli" "Rust" "Rust CLI repository discovery and review validation."
write_file "$root" "README.md" <<'EOF_FILE'
# Rust CLI Sample

Small Rust CLI-style sample used for local agent validation.
EOF_FILE
write_file "$root" "Cargo.toml" <<'EOF_FILE'
[package]
name = "rust-cli-sample"
version = "0.1.0"
edition = "2021"
EOF_FILE
write_file "$root" "src/main.rs" <<'EOF_FILE'
fn status() -> &'static str {
    "ok"
}

fn main() {
    println!("{}", status());
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn status_is_ok() {
        assert_eq!(status(), "ok");
    }
}
EOF_FILE

root="$(new_sample_root iac-terraform-kubernetes)"
add_metadata "$root" "iac-terraform-kubernetes" "Infrastructure as Code" "Terraform, Kubernetes, and workflow validation sample."
write_file "$root" "README.md" <<'EOF_FILE'
# Infrastructure Sample

Small Terraform/Kubernetes/GitHub Actions sample used for local agent validation.
EOF_FILE
write_file "$root" "terraform/main.tf" <<'EOF_FILE'
terraform {
  required_version = ">= 1.6.0"
}

variable "environment" {
  type    = string
  default = "dev"
}
EOF_FILE
write_file "$root" "k8s/deployment.yaml" <<'EOF_FILE'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sample-service
  template:
    metadata:
      labels:
        app: sample-service
    spec:
      containers:
        - name: sample-service
          image: example/sample-service:latest
EOF_FILE
write_file "$root" ".github/workflows/validate.yml" <<'EOF_FILE'
name: Validate
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - run: echo validate infrastructure sample
EOF_FILE

root="$(new_sample_root sql-migrations)"
add_metadata "$root" "sql-migrations" "SQL" "Database migration repository discovery and review validation."
write_file "$root" "README.md" <<'EOF_FILE'
# SQL Migration Sample

Small SQL migration sample used for local agent validation.
EOF_FILE
write_file "$root" "schema/001_create_items.sql" <<'EOF_FILE'
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
EOF_FILE
write_file "$root" "migrations/002_add_item_status.sql" <<'EOF_FILE'
ALTER TABLE items ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
EOF_FILE
write_file "$root" "seeds/items.sql" <<'EOF_FILE'
INSERT INTO items (id, name, created_at, status) VALUES (1, 'sample', '2026-01-01T00:00:00Z', 'active');
EOF_FILE
write_file "$root" "VALIDATION.md" <<'EOF_FILE'
# Validation Notes

Review migration ordering, defaults, rollback strategy, and seed-data safety.
EOF_FILE

root="$(new_sample_root python-layered-api)"
add_metadata "$root" "python-layered-api" "Python" "Layered API planning, review, and scoped-write validation." "medium"
write_file "$root" "README.md" <<'EOF_FILE'
# Python Layered API Sample

Medium-complexity Python fixture with configuration, domain, repository,
service, entry-point, and test boundaries.

## Commands

Create a local virtual environment before running tests. The environment and
test cache are ignored by Git.

macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip pytest
python -m pytest
python -m app.main
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip pytest
python -m pytest
python -m app.main
```
EOF_FILE

write_file "$root" ".gitignore" <<'EOF_FILE'
.venv/
__pycache__/
.pytest_cache/
EOF_FILE
write_file "$root" "SCENARIO.md" <<'EOF_FILE'
# Validation Scenario

Review item-name normalization across the service and repository boundaries.
For a scoped-write test, reject blank item names in `app/service.py` and add
only the corresponding tests in `tests/test_service.py`.
EOF_FILE
write_file "$root" "pyproject.toml" <<'EOF_FILE'
[project]
name = "sample-python-layered-api"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF_FILE
write_file "$root" "app/config.py" <<'EOF_FILE'
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str = "sample-python-layered-api"
    max_items: int = 100
EOF_FILE
write_file "$root" "app/domain.py" <<'EOF_FILE'
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    item_id: int
    name: str
EOF_FILE
write_file "$root" "app/repository.py" <<'EOF_FILE'
from app.domain import Item


class ItemRepository:
    def __init__(self) -> None:
        self._items: dict[int, Item] = {}

    def save(self, item: Item) -> Item:
        self._items[item.item_id] = item
        return item

    def find(self, item_id: int) -> Item | None:
        return self._items.get(item_id)
EOF_FILE
write_file "$root" "app/service.py" <<'EOF_FILE'
from app.domain import Item
from app.repository import ItemRepository


class ItemService:
    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    def create(self, item_id: int, name: str) -> Item:
        item = Item(item_id=item_id, name=name.strip())
        return self._repository.save(item)
EOF_FILE
write_file "$root" "app/main.py" <<'EOF_FILE'
from app.repository import ItemRepository
from app.service import ItemService


def build_service() -> ItemService:
    return ItemService(ItemRepository())


if __name__ == "__main__":
    print(build_service().create(1, "sample"))
EOF_FILE
write_file "$root" "tests/test_service.py" <<'EOF_FILE'
from app.repository import ItemRepository
from app.service import ItemService


def test_create_trims_item_name():
    service = ItemService(ItemRepository())
    assert service.create(1, " sample ").name == "sample"
EOF_FILE
write_file "$root" "config/settings.example.json" <<'EOF_FILE'
{
  "serviceName": "sample-python-layered-api",
  "maxItems": 100
}
EOF_FILE

root="$(new_sample_root typescript-service-medium)"
add_metadata "$root" "typescript-service-medium" "TypeScript" "Layered service planning, review, and scoped-write validation." "medium"
write_file "$root" "README.md" <<'EOF_FILE'
# TypeScript Service Medium Sample

Medium-complexity TypeScript fixture with domain, repository, service,
configuration, entry-point, and test boundaries.
EOF_FILE
write_file "$root" "SCENARIO.md" <<'EOF_FILE'
# Validation Scenario

Review identifier and display-name validation across the service boundary. For
a scoped-write test, reject blank display names in `src/service.ts` and change
only `src/service.ts` plus `tests/service.test.ts`.
EOF_FILE
write_file "$root" "package.json" <<'EOF_FILE'
{
  "name": "typescript-service-medium-sample",
  "private": true,
  "type": "module",
  "scripts": { "build": "tsc --noEmit", "test": "vitest run" },
  "devDependencies": { "typescript": "latest", "vitest": "latest" }
}
EOF_FILE
write_file "$root" "tsconfig.json" <<'EOF_FILE'
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noUncheckedIndexedAccess": true
  },
  "include": ["src", "tests"]
}
EOF_FILE
write_file "$root" "src/domain.ts" <<'EOF_FILE'
export interface Account {
  id: string;
  displayName: string;
}
EOF_FILE
write_file "$root" "src/repository.ts" <<'EOF_FILE'
import type { Account } from './domain.js';

export class AccountRepository {
  private readonly accounts = new Map<string, Account>();
  save(account: Account): Account { this.accounts.set(account.id, account); return account; }
  find(id: string): Account | undefined { return this.accounts.get(id); }
}
EOF_FILE
write_file "$root" "src/service.ts" <<'EOF_FILE'
import type { Account } from './domain.js';
import { AccountRepository } from './repository.js';

export class AccountService {
  constructor(private readonly repository: AccountRepository) {}
  create(id: string, displayName: string): Account {
    return this.repository.save({ id, displayName: displayName.trim() });
  }
}
EOF_FILE
write_file "$root" "src/config.ts" <<'EOF_FILE'
export interface ServiceConfig { serviceName: string; port: number; }
export const defaultConfig: ServiceConfig = {
  serviceName: 'typescript-service-medium-sample',
  port: 3000,
};
EOF_FILE
write_file "$root" "src/index.ts" <<'EOF_FILE'
import { AccountRepository } from './repository.js';
import { AccountService } from './service.js';
export const accountService = new AccountService(new AccountRepository());
EOF_FILE
write_file "$root" "tests/service.test.ts" <<'EOF_FILE'
import { describe, expect, it } from 'vitest';
import { AccountRepository } from '../src/repository.js';
import { AccountService } from '../src/service.js';

describe('AccountService', () => {
  it('trims display names', () => {
    const service = new AccountService(new AccountRepository());
    expect(service.create('a-1', ' Sample ').displayName).toBe('Sample');
  });
});
EOF_FILE

root="$(new_sample_root multi-language-platform)"
add_metadata "$root" "multi-language-platform" "Java, Go, Rust, SQL, and Infrastructure as Code" "Polyglot platform discovery, planning, review, and scoped-write validation." "medium"
write_file "$root" "README.md" <<'EOF_FILE'
# Multi-Language Platform Sample

Medium-complexity polyglot fixture containing a Java API, Go worker, Rust tool,
SQL migrations, Terraform, and Kubernetes deployment configuration.
EOF_FILE
write_file "$root" "SCENARIO.md" <<'EOF_FILE'
# Validation Scenario

Discover each component before applying language guidance. Planning and review
must keep service boundaries separate. Scoped-write tests must name one
component and may not edit another component without explicit approval.
EOF_FILE
write_file "$root" "services/catalog/pom.xml" <<'EOF_FILE'
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example.platform</groupId>
  <artifactId>catalog-service</artifactId>
  <version>0.1.0</version>
</project>
EOF_FILE
write_file "$root" "services/catalog/src/main/java/example/CatalogService.java" <<'EOF_FILE'
package example;
public final class CatalogService {
    public String normalizeName(String name) { return name.trim(); }
}
EOF_FILE
write_file "$root" "services/catalog/src/test/java/example/CatalogServiceTest.java" <<'EOF_FILE'
package example;
class CatalogServiceTest {
    void trimsNames() { assert "sample".equals(new CatalogService().normalizeName(" sample ")); }
}
EOF_FILE
write_file "$root" "workers/events/go.mod" <<'EOF_FILE'
module example.com/platform/events

go 1.22
EOF_FILE
write_file "$root" "workers/events/event.go" <<'EOF_FILE'
package events
import "strings"
func NormalizeTopic(topic string) string { return strings.TrimSpace(topic) }
EOF_FILE
write_file "$root" "workers/events/event_test.go" <<'EOF_FILE'
package events
import "testing"
func TestNormalizeTopic(t *testing.T) {
	if NormalizeTopic(" updates ") != "updates" { t.Fatal("expected trimmed topic") }
}
EOF_FILE
write_file "$root" "tools/manifest/Cargo.toml" <<'EOF_FILE'
[package]
name = "manifest-tool"
version = "0.1.0"
edition = "2021"
EOF_FILE
write_file "$root" "tools/manifest/src/lib.rs" <<'EOF_FILE'
pub fn normalize_key(value: &str) -> String { value.trim().to_lowercase() }
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn normalizes_keys() { assert_eq!(normalize_key(" Item-Key "), "item-key"); }
}
EOF_FILE
write_file "$root" "database/schema/001_catalog.sql" <<'EOF_FILE'
CREATE TABLE catalog_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
EOF_FILE
write_file "$root" "database/migrations/002_catalog_status.sql" <<'EOF_FILE'
ALTER TABLE catalog_items ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
EOF_FILE
write_file "$root" "infrastructure/terraform/main.tf" <<'EOF_FILE'
terraform { required_version = ">= 1.6.0" }
variable "environment" { type = string }
output "service_name" { value = "catalog-${var.environment}" }
EOF_FILE
write_file "$root" "infrastructure/k8s/catalog.yaml" <<'EOF_FILE'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: catalog-service
  template:
    metadata:
      labels:
        app: catalog-service
    spec:
      containers:
        - name: catalog-service
          image: example/catalog-service:latest
EOF_FILE

printf 'Generated sample repositories in: %s\n' "$OUTPUT_ROOT"
printf -- '- %s\n' "${SAMPLES[@]}"
