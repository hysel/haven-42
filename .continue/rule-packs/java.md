---
name: Java Engineering
optional: true
---

## Scope

Use this optional rule pack only when project detection confirms Java evidence.

Strong Java evidence includes `pom.xml`, `build.gradle`, `settings.gradle`, `gradle.properties`, `mvnw`, `gradlew`, `src/main/java`, `src/test/java`, or inspected Java source and test files.

If Java evidence is absent or unreadable, do not apply this rule pack. Keep recommendations language-neutral and mark Java, Spring, Maven, Gradle, and test-runner assumptions as `unconfirmed`.

## Required Practices

- Read build metadata before naming Maven, Gradle, plugins, dependencies, Java versions, or test commands.
- Preserve the repository's existing build tool and module layout unless migration is explicitly requested.
- Keep application, domain, infrastructure, configuration, and test code separated according to existing packages and modules.
- Treat controllers, message consumers, scheduled jobs, file input, deserialization, SQL, and external service calls as validation boundaries.
- Match tests to inspected tooling such as JUnit, TestNG, Mockito, Spring test support, Maven Surefire/Failsafe, or Gradle test tasks.
- Check dependency scopes, plugin configuration, and generated artifacts before recommending packaging or release changes.
- Keep Spring, Jakarta EE, Quarkus, Micronaut, Android, or other framework advice tied to inspected evidence.

## Avoid

- Recommending Spring, Maven, Gradle, JUnit, Mockito, Lombok, MapStruct, Hibernate, or Jakarta APIs without repository evidence.
- Flattening package boundaries or introducing broad service classes without a clear design reason.
- Adding static global state, hidden singleton dependencies, or mutable shared configuration.
- Treating compile success as enough validation for runtime wiring, configuration binding, database migrations, or serialization behavior.
- Suggesting integration tests that require live services when deterministic seams or test containers are not already part of the project.

## Review Checklist

- Which files prove this is a Java project?
- Which build tool, Java version, framework, and test runner are confirmed versus `unconfirmed`?
- Are package boundaries and dependency directions preserved?
- Are configuration, secrets, serialization, database, and external-service boundaries validated?
- Do test and build recommendations match inspected project metadata?
