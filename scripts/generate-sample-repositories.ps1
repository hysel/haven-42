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
    "sql-migrations"
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

    $normalized = $Content -replace "`r`n", "`n"
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
        [string]$Purpose
    )

    Write-SampleFile $SampleRoot "SAMPLE-METADATA.md" @"
# Sample Metadata

Name: $Name
Ecosystem: $Ecosystem
Purpose: $Purpose
Generated: deterministic local fixture

This repository is a disposable validation sample for the Local Engineering Agent Pack. It is not a production starter template.
"@
}

New-Item -ItemType Directory -Force -Path $outputRootPath | Out-Null

$root = New-SampleRoot "python-api"
Add-Metadata $root "python-api" "Python" "API-style repository discovery and review validation."
Write-SampleFile $root "README.md" @"
# Python API Sample

Small Python API-style sample used for local agent validation.

## Commands

- `python -m pytest`
- `python -m app.main`
"@

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
Set-Content -LiteralPath (Join-Path $root "app/main.py") -Value $pythonMain -NoNewline

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

Write-Host "Generated sample repositories in: $outputRootPath" -ForegroundColor Green
$samples | ForEach-Object { Write-Host "- $_" }