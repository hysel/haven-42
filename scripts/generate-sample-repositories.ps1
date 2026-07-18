param(
    [string]$OutputRoot = "runtime-validation-output/sample-repositories",
    [switch]$Force,
    [switch]$List
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$outputRootPath = if ([System.IO.Path]::IsPathRooted($OutputRoot)) {
    $OutputRoot
} else {
    Join-Path $repoRoot $OutputRoot
}

$samples = @(
    "python-api",
    "typescript-frontend",
    "node-service",
    "java-spring-api",
    "go-service",
    "rust-cli",
    "iac-terraform-kubernetes",
    "sql-migrations",
    "python-layered-api",
    "typescript-service-medium",
    "multi-language-platform"
)

if ($List) {
    $samples | ForEach-Object { Write-Output $_ }
    exit 0
}

function Write-SampleFile {
    param(
        [string]$SampleRoot,
        [string]$RelativePath,
        [string]$Content
    )

    $path = Join-Path $SampleRoot $RelativePath
    $directory = Split-Path -Parent $path
    if ($directory) {
        New-Item -ItemType Directory -Force -Path $directory | Out-Null
    }

    $normalized = ($Content -replace "`r`n", "`n").TrimEnd("`n") + "`n"
    Set-Content -LiteralPath $path -Value $normalized -NoNewline
}

function New-SampleRoot {
    param([string]$Name)

    $sampleRoot = Join-Path $outputRootPath $Name
    if ((Test-Path -LiteralPath $sampleRoot) -and -not $Force) {
        throw "Sample '$Name' already exists at '$sampleRoot'. Use -Force to overwrite generated samples."
    }

    if (Test-Path -LiteralPath $sampleRoot) {
        Remove-Item -LiteralPath $sampleRoot -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path $sampleRoot | Out-Null
    return $sampleRoot
}

function Add-Metadata {
    param(
        [string]$SampleRoot,
        [string]$Name,
        [string]$Ecosystem,
        [string]$Purpose,
        [string]$Complexity = "minimal"
    )

    Write-SampleFile $SampleRoot "SAMPLE-METADATA.md" @"
# Sample Metadata

Name: $Name
Ecosystem: $Ecosystem
Purpose: $Purpose
Complexity: $Complexity
Generated: deterministic local fixture

This repository is a disposable validation sample for the Local Engineering Agent Pack. It is not a production starter template.
"@
}

New-Item -ItemType Directory -Force -Path $outputRootPath | Out-Null

$root = New-SampleRoot "python-api"
Add-Metadata $root "python-api" "Python" "API-style repository discovery and review validation."
Write-SampleFile $root "README.md" @'
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
'@

Write-SampleFile $root ".gitignore" @'
.venv/
__pycache__/
.pytest_cache/
'@

Write-SampleFile $root "pyproject.toml" @'
[project]
name = "sample-python-api"
version = "0.1.0"
description = "Generated Python API validation fixture"
requires-python = ">=3.9"

[tool.pytest.ini_options]
testpaths = ["tests"]
'@

Write-SampleFile $root "app/main.py" @'
from app.settings import Settings


def build_health_response(settings: Settings) -> dict[str, str]:
    return {"service": settings.service_name, "status": "ok"}


if __name__ == "__main__":
    print(build_health_response(Settings()))
'@
Write-SampleFile $root "app/settings.py" @"
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str = "sample-python-api"
"@
Write-SampleFile $root "tests/test_main.py" @"
from app.main import build_health_response
from app.settings import Settings


def test_build_health_response():
    assert build_health_response(Settings()) == {"service": "sample-python-api", "status": "ok"}
"@
$pythonMain = @'
from app.settings import Settings


def build_health_response(settings: Settings) -> dict[str, str]:
    return {"service": settings.service_name, "status": "ok"}


if __name__ == "__main__":
    print(build_health_response(Settings()))
'@
New-Item -ItemType Directory -Force -Path (Join-Path $root "app") | Out-Null
Set-Content -LiteralPath (Join-Path $root "app/main.py") -Value ($pythonMain.TrimEnd("`n") + "`n") -NoNewline

$root = New-SampleRoot "typescript-frontend"
Add-Metadata $root "typescript-frontend" "TypeScript" "Frontend repository discovery and review validation."
Write-SampleFile $root "README.md" @"
# TypeScript Frontend Sample

Small TypeScript frontend-style sample used for local agent validation.
"@
Write-SampleFile $root "package.json" @"
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
"@
Write-SampleFile $root "tsconfig.json" @"
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "strict": true,
    "jsx": "react-jsx"
  }
}
"@
Write-SampleFile $root "src/App.tsx" @"
export function App() {
  return <main><h1>Sample frontend</h1></main>;
}
"@
Write-SampleFile $root "src/app.test.ts" @"
import { describe, expect, it } from 'vitest';

describe('sample frontend', () => {
  it('has a placeholder test', () => {
    expect('frontend').toBe('frontend');
  });
});
"@

$root = New-SampleRoot "node-service"
Add-Metadata $root "node-service" "Node.js" "Node service repository discovery and review validation."
Write-SampleFile $root "README.md" @"
# Node Service Sample

Small Node service-style sample used for local agent validation.
"@
Write-SampleFile $root "package.json" @"
{
  "name": "node-service-sample",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "node src/server.js",
    "test": "node --test"
  }
}
"@
Write-SampleFile $root "src/server.js" @"
export function createHealthPayload() {
  return { service: 'node-service-sample', status: 'ok' };
}
"@
Write-SampleFile $root "test/server.test.js" @"
import test from 'node:test';
import assert from 'node:assert/strict';
import { createHealthPayload } from '../src/server.js';

test('health payload', () => {
  assert.equal(createHealthPayload().status, 'ok');
});
"@
Write-SampleFile $root "Dockerfile" @"
FROM node:22-alpine
WORKDIR /app
COPY package.json ./
COPY src ./src
CMD ["node", "src/server.js"]
"@

$root = New-SampleRoot "java-spring-api"
Add-Metadata $root "java-spring-api" "Java" "Java/Spring-style repository discovery and review validation."
Write-SampleFile $root "README.md" @"
# Java Spring API Sample

Small Java/Spring-style sample used for local agent validation.
"@
Write-SampleFile $root "pom.xml" @"
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example</groupId>
  <artifactId>java-spring-api-sample</artifactId>
  <version>0.1.0</version>
</project>
"@
Write-SampleFile $root "src/main/java/example/HealthController.java" @"
package example;

public final class HealthController {
    public String status() {
        return "ok";
    }
}
"@
Write-SampleFile $root "src/test/java/example/HealthControllerTest.java" @"
package example;

class HealthControllerTest {
    void returnsOk() {
        assert "ok".equals(new HealthController().status());
    }
}
"@
Write-SampleFile $root "src/main/resources/application.properties" @"
spring.application.name=java-spring-api-sample
"@

$root = New-SampleRoot "go-service"
Add-Metadata $root "go-service" "Go" "Go service repository discovery and review validation."
Write-SampleFile $root "README.md" @"
# Go Service Sample

Small Go service-style sample used for local agent validation.
"@
Write-SampleFile $root "go.mod" @"
module example.com/go-service-sample

go 1.22
"@
Write-SampleFile $root "cmd/server/main.go" @"
package main

import "fmt"

func healthStatus() string {
	return "ok"
}

func main() {
	fmt.Println(healthStatus())
}
"@
Write-SampleFile $root "cmd/server/main_test.go" @"
package main

import "testing"

func TestHealthStatus(t *testing.T) {
	if healthStatus() != "ok" {
		t.Fatal("expected ok")
	}
}
"@

$root = New-SampleRoot "rust-cli"
Add-Metadata $root "rust-cli" "Rust" "Rust CLI repository discovery and review validation."
Write-SampleFile $root "README.md" @"
# Rust CLI Sample

Small Rust CLI-style sample used for local agent validation.
"@
Write-SampleFile $root "Cargo.toml" @"
[package]
name = "rust-cli-sample"
version = "0.1.0"
edition = "2021"
"@
Write-SampleFile $root "src/main.rs" @"
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
"@

$root = New-SampleRoot "iac-terraform-kubernetes"
Add-Metadata $root "iac-terraform-kubernetes" "Infrastructure as Code" "Terraform, Kubernetes, and workflow validation sample."
Write-SampleFile $root "README.md" @"
# Infrastructure Sample

Small Terraform/Kubernetes/GitHub Actions sample used for local agent validation.
"@
Write-SampleFile $root "terraform/main.tf" @"
terraform {
  required_version = ">= 1.6.0"
}

variable "environment" {
  type    = string
  default = "dev"
}
"@
Write-SampleFile $root "k8s/deployment.yaml" @"
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
"@
Write-SampleFile $root ".github/workflows/validate.yml" @"
name: Validate
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo validate infrastructure sample
"@

$root = New-SampleRoot "sql-migrations"
Add-Metadata $root "sql-migrations" "SQL" "Database migration repository discovery and review validation."
Write-SampleFile $root "README.md" @"
# SQL Migration Sample

Small SQL migration sample used for local agent validation.
"@
Write-SampleFile $root "schema/001_create_items.sql" @"
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"@
Write-SampleFile $root "migrations/002_add_item_status.sql" @"
ALTER TABLE items ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
"@
Write-SampleFile $root "seeds/items.sql" @"
INSERT INTO items (id, name, created_at, status) VALUES (1, 'sample', '2026-01-01T00:00:00Z', 'active');
"@
Write-SampleFile $root "VALIDATION.md" @"
# Validation Notes

Review migration ordering, defaults, rollback strategy, and seed-data safety.
"@

$root = New-SampleRoot "python-layered-api"
Add-Metadata $root "python-layered-api" "Python" "Layered API planning, review, and scoped-write validation." "medium"
Write-SampleFile $root "README.md" @'
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
'@

Write-SampleFile $root ".gitignore" @'
.venv/
__pycache__/
.pytest_cache/
'@
Write-SampleFile $root "SCENARIO.md" @'
# Validation Scenario

Review item-name normalization across the service and repository boundaries.
For a scoped-write test, reject blank item names in `app/service.py` and add
only the corresponding tests in `tests/test_service.py`.
'@
Write-SampleFile $root "pyproject.toml" @'
[project]
name = "sample-python-layered-api"
version = "0.1.0"
requires-python = ">=3.10"

[tool.pytest.ini_options]
testpaths = ["tests"]
'@
Write-SampleFile $root "app/config.py" @'
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str = "sample-python-layered-api"
    max_items: int = 100
'@
Write-SampleFile $root "app/domain.py" @'
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    item_id: int
    name: str
'@
Write-SampleFile $root "app/repository.py" @'
from app.domain import Item


class ItemRepository:
    def __init__(self) -> None:
        self._items: dict[int, Item] = {}

    def save(self, item: Item) -> Item:
        self._items[item.item_id] = item
        return item

    def find(self, item_id: int) -> Item | None:
        return self._items.get(item_id)
'@
Write-SampleFile $root "app/service.py" @'
from app.domain import Item
from app.repository import ItemRepository


class ItemService:
    def __init__(self, repository: ItemRepository) -> None:
        self._repository = repository

    def create(self, item_id: int, name: str) -> Item:
        item = Item(item_id=item_id, name=name.strip())
        return self._repository.save(item)
'@
Write-SampleFile $root "app/main.py" @'
from app.repository import ItemRepository
from app.service import ItemService


def build_service() -> ItemService:
    return ItemService(ItemRepository())


if __name__ == "__main__":
    print(build_service().create(1, "sample"))
'@
Write-SampleFile $root "tests/test_service.py" @'
from app.repository import ItemRepository
from app.service import ItemService


def test_create_trims_item_name():
    service = ItemService(ItemRepository())
    assert service.create(1, " sample ").name == "sample"
'@
Write-SampleFile $root "config/settings.example.json" @'
{
  "serviceName": "sample-python-layered-api",
  "maxItems": 100
}
'@

$root = New-SampleRoot "typescript-service-medium"
Add-Metadata $root "typescript-service-medium" "TypeScript" "Layered service planning, review, and scoped-write validation." "medium"
Write-SampleFile $root "README.md" @'
# TypeScript Service Medium Sample

Medium-complexity TypeScript fixture with domain, repository, service,
configuration, entry-point, and test boundaries.
'@
Write-SampleFile $root "SCENARIO.md" @'
# Validation Scenario

Review identifier and display-name validation across the service boundary. For
a scoped-write test, reject blank display names in `src/service.ts` and change
only `src/service.ts` plus `tests/service.test.ts`.
'@
Write-SampleFile $root "package.json" @'
{
  "name": "typescript-service-medium-sample",
  "private": true,
  "type": "module",
  "scripts": {
    "build": "tsc --noEmit",
    "test": "vitest run"
  },
  "devDependencies": {
    "typescript": "latest",
    "vitest": "latest"
  }
}
'@
Write-SampleFile $root "tsconfig.json" @'
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
'@
Write-SampleFile $root "src/domain.ts" @'
export interface Account {
  id: string;
  displayName: string;
}
'@
Write-SampleFile $root "src/repository.ts" @'
import type { Account } from './domain.js';

export class AccountRepository {
  private readonly accounts = new Map<string, Account>();

  save(account: Account): Account {
    this.accounts.set(account.id, account);
    return account;
  }

  find(id: string): Account | undefined {
    return this.accounts.get(id);
  }
}
'@
Write-SampleFile $root "src/service.ts" @'
import type { Account } from './domain.js';
import { AccountRepository } from './repository.js';

export class AccountService {
  constructor(private readonly repository: AccountRepository) {}

  create(id: string, displayName: string): Account {
    return this.repository.save({ id, displayName: displayName.trim() });
  }
}
'@
Write-SampleFile $root "src/config.ts" @'
export interface ServiceConfig {
  serviceName: string;
  port: number;
}

export const defaultConfig: ServiceConfig = {
  serviceName: 'typescript-service-medium-sample',
  port: 3000,
};
'@
Write-SampleFile $root "src/index.ts" @'
import { AccountRepository } from './repository.js';
import { AccountService } from './service.js';

export const accountService = new AccountService(new AccountRepository());
'@
Write-SampleFile $root "tests/service.test.ts" @'
import { describe, expect, it } from 'vitest';
import { AccountRepository } from '../src/repository.js';
import { AccountService } from '../src/service.js';

describe('AccountService', () => {
  it('trims display names', () => {
    const service = new AccountService(new AccountRepository());
    expect(service.create('a-1', ' Sample ').displayName).toBe('Sample');
  });
});
'@

$root = New-SampleRoot "multi-language-platform"
Add-Metadata $root "multi-language-platform" "Java, Go, Rust, SQL, and Infrastructure as Code" "Polyglot platform discovery, planning, review, and scoped-write validation." "medium"
Write-SampleFile $root "README.md" @'
# Multi-Language Platform Sample

Medium-complexity polyglot fixture containing a Java API, Go worker, Rust tool,
SQL migrations, Terraform, and Kubernetes deployment configuration.
'@
Write-SampleFile $root "SCENARIO.md" @'
# Validation Scenario

Discover each component before applying language guidance. Planning and review
must keep service boundaries separate. Scoped-write tests must name one
component and may not edit another component without explicit approval.
'@
Write-SampleFile $root "services/catalog/pom.xml" @'
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>example.platform</groupId>
  <artifactId>catalog-service</artifactId>
  <version>0.1.0</version>
</project>
'@
Write-SampleFile $root "services/catalog/src/main/java/example/CatalogService.java" @'
package example;

public final class CatalogService {
    public String normalizeName(String name) {
        return name.trim();
    }
}
'@
Write-SampleFile $root "services/catalog/src/test/java/example/CatalogServiceTest.java" @'
package example;

class CatalogServiceTest {
    void trimsNames() {
        assert "sample".equals(new CatalogService().normalizeName(" sample "));
    }
}
'@
Write-SampleFile $root "workers/events/go.mod" @'
module example.com/platform/events

go 1.22
'@
Write-SampleFile $root "workers/events/event.go" @'
package events

import "strings"

func NormalizeTopic(topic string) string {
	return strings.TrimSpace(topic)
}
'@
Write-SampleFile $root "workers/events/event_test.go" @'
package events

import "testing"

func TestNormalizeTopic(t *testing.T) {
	if NormalizeTopic(" updates ") != "updates" {
		t.Fatal("expected trimmed topic")
	}
}
'@
Write-SampleFile $root "tools/manifest/Cargo.toml" @'
[package]
name = "manifest-tool"
version = "0.1.0"
edition = "2021"
'@
Write-SampleFile $root "tools/manifest/src/lib.rs" @'
pub fn normalize_key(value: &str) -> String {
    value.trim().to_lowercase()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn normalizes_keys() {
        assert_eq!(normalize_key(" Item-Key "), "item-key");
    }
}
'@
Write-SampleFile $root "database/schema/001_catalog.sql" @'
CREATE TABLE catalog_items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
'@
Write-SampleFile $root "database/migrations/002_catalog_status.sql" @'
ALTER TABLE catalog_items ADD COLUMN status TEXT NOT NULL DEFAULT 'active';
'@
Write-SampleFile $root "infrastructure/terraform/main.tf" @'
terraform {
  required_version = ">= 1.6.0"
}

variable "environment" {
  type = string
}

output "service_name" {
  value = "catalog-${var.environment}"
}
'@
Write-SampleFile $root "infrastructure/k8s/catalog.yaml" @'
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
'@

Write-Host "Generated sample repositories in: $outputRootPath" -ForegroundColor Green
$samples | ForEach-Object { Write-Host "- $_" }
