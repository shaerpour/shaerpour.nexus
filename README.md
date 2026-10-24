# Ansible Collection: shaerpour.nexus

**Run Sonatype Nexus Repository as code.**

`shaerpour.nexus` brings your Nexus configuration into Ansible. Describe repositories and the rest of your Nexus setup in playbooks, keep them in version control, and apply them the same way every time: repeatable, reviewable and safe to run again.

- **Declarative:** state what Nexus should look like, and the modules make it so.
- **Idempotent:** a second run changes nothing, and `--check` shows what would change before it does.
- **Agentless:** modules talk to the Nexus REST API, so nothing is installed on the Nexus host.

## Installation

```bash
ansible-galaxy collection install git+https://github.com/shaerpour/shaerpour.nexus.git
```

## Documentation

Every module documents its options, defaults and examples through `ansible-doc`:

```bash
ansible-doc shaerpour.nexus.<module>
```

To list the modules in the collection:

```bash
ansible-doc -l shaerpour.nexus
```

## Support

Found a bug or missing a feature? Open an issue in the [issue tracker](https://github.com/shaerpour/shaerpour.nexus/issues).

## Contributing

Contributions of every size are welcome: bug fixes, improvements to existing modules, new features and new modules.

1. Fork the repository and create a branch for your change.
2. Make the change, and add or update the integration tests that cover it.
3. Run the tests (see below).
4. Open a pull request that explains what changed and why.

### Development setup

`ansible-test` only runs from a directory named `ansible_collections/<namespace>/<name>`, so clone the repository into the Ansible collections path:

```bash
git clone git@github.com:shaerpour/shaerpour.nexus.git ~/.ansible/collections/ansible_collections/shaerpour/nexus
```

### Testing

Integration tests are Ansible tasks that run the modules against a real Nexus. Copy `tests/integration/integration_config.yml.template` to `tests/integration/integration_config.yml`, fill in your Nexus URL and credentials, then run:

```bash
ansible-test integration <module> --allow-unsupported
```

Pass a target name to run the tests of a single module. The tests create resources with a `test-` prefix and remove them when they finish, so use a Nexus where that is acceptable.

## License

GNU General Public License v3.0 or later. See [COPYING](COPYING).
