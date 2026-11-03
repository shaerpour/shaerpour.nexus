# Contributing to shaerpour.nexus

Thank you for helping. The goal of this collection is to manage the whole of Sonatype Nexus Repository Manager 3 from Ansible. Bug reports, fixes, documentation, tests and new modules are all welcome, and so is a short issue that says "I need X".

## Before you start

- Search the [issues](https://github.com/shaerpour/shaerpour.nexus/issues) to see whether the work is already planned or in progress.
- For a new module or a bigger change, open a [feature request](https://github.com/shaerpour/shaerpour.nexus/issues/new/choose) first, so the design can be agreed before you write code.
- For a small fix, open a pull request directly.

## Development setup

`ansible-test` only runs from a directory named `ansible_collections/<namespace>/<name>`, so clone the repository there:

```bash
git clone git@github.com:shaerpour/shaerpour.nexus.git ~/.ansible/collections/ansible_collections/shaerpour/nexus
cd ~/.ansible/collections/ansible_collections/shaerpour/nexus
python3 -m venv .venv
.venv/bin/pip install ansible-core
```

Create a branch for your change. Do not work on `main`.

## How the collection is organised

| Path | Contents |
| --- | --- |
| `plugins/modules/` | One module per Nexus object type, such as `repository_docker` or `blob_store_file`. |
| `plugins/module_utils/client.py` | The Nexus REST API client and the shared connection options. |
| `plugins/doc_fragments/connection.py` | Documentation of the connection options every module accepts. |
| `meta/runtime.yml` | The Ansible version requirement and the `all` action group, which lists every module. |
| `tests/integration/targets/<module>/` | The integration tests of one module. |
| `changelogs/fragments/` | Changelog entries that are not yet released. |

## Adding a module

Each repository format and each blob store type is a standalone module. Modules deliberately repeat a little code instead of sharing helpers, so that every module can be read from top to bottom and changed without affecting the others.

1. **Name it** `repository_<format>` or `blob_store_<type>`. Use the same prefix for related modules.
2. **Start from the closest existing module.** `repository_raw` is the simplest repository module and `blob_store_file` is the simplest blob store module. Copy it and change only what the new type needs. Keep the same structure: `DOCUMENTATION`, `EXAMPLES`, `build_payload`, `is_subset`, `ensure_absent`, `ensure_present`, `ensure` and `main`.
3. **Check what Nexus really accepts.** Create the object by hand or with `curl`, read it back with `GET`, and compare. Nexus often returns more fields than you send, and sometimes leaves out some you did (for example `name` or secrets). Compare only the fields the module manages.
4. **Follow these rules:**
   - The module must be idempotent: a second run reports no change.
   - It must support check mode and must not change anything when `check_mode` is on.
   - Options that hold secrets use `no_log: true` and are left out of the comparison when Nexus does not return them.
   - Use clear option names in `snake_case` and document every option, including its default and when it applies.
   - Set `version_added` to the version of the next release.
   - Do not add options or features that nothing needs yet.
5. **Add the module to `meta/runtime.yml`** in the `all` action group.
6. **Add an integration test** (see below).
7. **Check the documentation:**

   ```bash
   ansible-doc shaerpour.nexus.<module>
   ```

## Tests

The tests are Ansible tasks that run the modules against a real Nexus. There are no unit tests, because most of the logic is the behaviour of the Nexus API.

Copy `tests/integration/integration_config.yml.template` to `tests/integration/integration_config.yml`, fill in your Nexus URL and credentials, and run a target:

```bash
ansible-test integration <module> --allow-unsupported
```

The config file is ignored by git. Use a Nexus where creating and deleting test objects is acceptable.

A test target is a folder `tests/integration/targets/<module>/` with an `aliases` file that contains `unsupported`, and `tasks/main.yml`. Copy the target of a similar module and cover at least:

- creating the object, in check mode and for real
- creating it again, which must report no change
- changing a setting
- every type or option combination the module supports
- an invalid combination that must fail
- deleting the object, in the `always` section, so a failed test cleans up after itself

Name every object `test-<something>` so that leftovers are easy to find. The `blob_store_s3` target needs an S3 compatible service and takes its settings from the S3 lines of the config file. CI starts a mock S3 service for it.

CI also runs `ansible-test sanity`, which checks the documentation, argument specs, code style and licence headers. If it reports something for your change, fix it in the same pull request.

## Changelog

Releases are built from changelog fragments with [antsibull-changelog](https://github.com/ansible-community/antsibull-changelog).

- **A new module needs no fragment.** It is listed under "New Modules" from its `version_added`.
- **Any other user-facing change needs one.** Add a YAML file in `changelogs/fragments/`, named after the change, for example `fix-docker-anonymous-pull.yml`:

  ```yaml
  bugfixes:
    - repository_docker - keep the anonymous pull setting when updating a repository.
  ```

  Use `minor_changes` for new options and improvements, and `bugfixes` for fixes.
- Test-only and CI-only changes need no fragment.

Maintainers prepare releases. Do not change the version in `galaxy.yml` or edit `CHANGELOG.rst` in a normal pull request.

## Commits and pull requests

- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/), with the module as the scope:

  ```
  feat(repository_nuget): add module to manage NuGet repositories
  fix(repository_docker): keep the anonymous pull setting on update
  docs: explain the soft quota options
  ci: run sanity tests in a virtual environment
  ```

- Pull requests are squash-merged, so the title of the pull request becomes the commit message. Write it in the same style.
- Fill in the pull request template: what changed and why, the Nexus version you tested against, and the checklist.
- Keep a pull request to one change. A new module, a fix and a refactoring belong in three pull requests.
- Link the issue it belongs to. Use `Closes #123` when the pull request finishes it and `Refs #123` when it does not.

## License

The collection is licensed under the GNU General Public License v3.0 or later. By contributing, you agree that your contribution is licensed the same way. New files carry the same licence header as the existing ones.
