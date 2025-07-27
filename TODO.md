# TODO List for Code Hygiene

This checklist is a guide to maintaining a clean, stable, and error-free codebase. Following these practices will help prevent common issues related to imports, dependencies, and Docker builds.

## Code Structure and Imports

- [ ] Verify that all new modules follow the established project structure.
- [ ] Ensure all Python packages have `__init__.py` files to make them recognizable as packages.
- [ ] Double-check that all imports are absolute (e.g., `from src.api.schemas import TokenData`) and not relative.
- [ ] Regularly review and refactor code to keep modules focused on a single responsibility.

## Dependency Management

- [ ] Pin all primary dependencies in `requirements.txt` to specific, known-good versions (e.g., `fastapi==0.104.1`).
- [ ] Periodically run a dependency audit to check for incompatibilities or security vulnerabilities.
- [ ] Remove unused dependencies from `requirements.txt` to keep the environment lean.

## Docker and Build Process

- [ ] Before committing new files, ensure that any large or unnecessary files (e.g., virtual environments, log files, IDE settings) are added to `.dockerignore`.
- [ ] Regularly prune unused Docker images, containers, and build caches to free up disk space (`docker image prune`, `docker builder prune -a`).
- [ ] Optimize `Dockerfile` instructions to leverage caching, such as by copying `requirements.txt` and installing dependencies before copying the rest of the application code.

## Code Quality and Cleanup

- [ ] Before merging new features, run a linter (like `flake8` or `pylint`) and a code formatter (like `black`) to maintain a consistent style.
- [ ] Use tools to detect unused code (e.g., `vulture`) and remove dead functions, classes, and variables.
- [ ] Periodically review and remove feature-flagged or obsolete code that is no longer needed.
- [ ] Ensure that all new functions and modules have clear docstrings explaining their purpose, arguments, and return values. 