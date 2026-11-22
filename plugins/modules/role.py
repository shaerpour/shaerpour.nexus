#!/usr/bin/python
# Copyright: (c) 2026, Amirhosein Shaerpour <shaerpourr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
module: role
short_description: Manage Nexus local security roles
version_added: 0.6.0
description:
  - Create, update or delete security roles in the default local Nexus source.
  - Omitted settings are preserved when updating an existing role.
  - Built-in read-only roles cannot be changed or deleted.
  - Roles from external sources such as LDAP are not managed by this module.
author:
  - Amirhosein Shaerpour (@shaerpour)
extends_documentation_fragment:
  - shaerpour.nexus.connection
options:
  role_id:
    description: Unique ID of the role. The ID of an existing role cannot be changed.
    type: str
    required: true
  state:
    description:
      - C(present) creates the role, or updates managed settings when they differ.
      - C(absent) deletes the role without requiring other settings.
    type: str
    choices: [present, absent]
    default: present
  name:
    description:
      - Display name of the role. Must not be empty when supplied.
      - Defaults to I(role_id) on creation and is preserved when omitted on update.
    type: str
  description:
    description:
      - Description of the role.
      - Defaults to an empty string on creation and is preserved when omitted on update.
      - Set to an empty string to clear an existing description.
    type: str
  privileges:
    description:
      - IDs of existing Nexus privileges assigned to the role.
      - Replaces the assigned privileges when supplied. Order and duplicates are ignored.
      - Defaults to no privileges on creation and is preserved when omitted on update.
      - Set to an empty list to remove all directly assigned privileges.
    type: list
    elements: str
  roles:
    description:
      - IDs of existing local Nexus roles inherited by this role.
      - Replaces inherited roles when supplied. Order and duplicates are ignored.
      - Defaults to no inherited roles on creation and is preserved when omitted on update.
      - Set to an empty list to remove all inherited roles.
    type: list
    elements: str
"""

EXAMPLES = r"""
- name: Create a package reader role
  shaerpour.nexus.role:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    role_id: package-reader
    name: Package reader
    description: Read packages from all repositories
    privileges:
      - nx-repository-view-*-*-browse
      - nx-repository-view-*-*-read

- name: Inherit a role while preserving direct privileges and other settings
  shaerpour.nexus.role:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    role_id: package-reader
    roles: [nx-anonymous]

- name: Remove all directly assigned privileges
  shaerpour.nexus.role:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    role_id: package-reader
    privileges: []

- name: Delete a role
  shaerpour.nexus.role:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    role_id: package-reader
    state: absent
"""

RETURN = r""" # """

from urllib.parse import quote

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.shaerpour.nexus.plugins.module_utils.client import (
    AUTH_ARGUMENT_SPEC,
    NexusClient,
    NexusError,
)


def build_payload(params, current):
    """Build a role body, preserving settings that the task does not manage."""
    existing = current or {}
    payload = {"id": params["role_id"]}
    payload["name"] = params["name"] if params["name"] is not None else existing.get("name", params["role_id"])
    payload["description"] = params["description"] if params["description"] is not None else existing.get("description", "")
    for field in ("privileges", "roles"):
        values = params[field] if params[field] is not None else existing.get(field, [])
        payload[field] = sorted(set(values))
    return payload


def is_subset(desired, current):
    """Compare managed fields, treating privileges and inherited roles as sets."""
    if isinstance(desired, dict):
        return isinstance(current, dict) and all(
            key in current and is_subset(value, current[key]) for key, value in desired.items()
        )
    if isinstance(desired, list):
        return isinstance(current, list) and set(desired) == set(current)
    return desired == current


def ensure_absent(client, role_id, current, check_mode):
    """Delete the local role if present. Return True when something changed."""
    if current is None:
        return False
    if current.get("readOnly"):
        raise NexusError(f"Role {role_id} is read-only and cannot be deleted")
    if not check_mode:
        client.request("DELETE", f"/security/roles/{quote(role_id, safe='')}?source=default")
    return True


def ensure_present(client, params, current, check_mode):
    """Create or update the local role. Return True when something changed."""
    payload = build_payload(params, current)
    if current is None:
        if not check_mode:
            client.request("POST", "/security/roles?source=default", payload)
        return True
    if is_subset(payload, current):
        return False
    if current.get("readOnly"):
        raise NexusError(f"Role {params['role_id']} is read-only and cannot be updated")
    if not check_mode:
        client.request("PUT", f"/security/roles/{quote(params['role_id'], safe='')}?source=default", payload)
    return True


def ensure(client, params, check_mode):
    """Read the exact local role and bring it to the requested state."""
    current = client.request("GET", f"/security/roles/{quote(params['role_id'], safe='')}?source=default")
    if params["state"] == "absent":
        return ensure_absent(client, params["role_id"], current, check_mode)
    return ensure_present(client, params, current, check_mode)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **AUTH_ARGUMENT_SPEC,
            role_id=dict(type="str", required=True),
            state=dict(type="str", default="present", choices=["present", "absent"]),
            name=dict(type="str"),
            description=dict(type="str"),
            privileges=dict(type="list", elements="str"),
            roles=dict(type="list", elements="str"),
        ),
        supports_check_mode=True,
    )
    params = module.params
    if not params["role_id"]:
        module.fail_json(msg="role_id must not be empty")
    if params["state"] == "present" and params["name"] == "":
        module.fail_json(msg="name must not be empty")
    client = NexusClient(params["url"], params["username"], params["password"], params["validate_certs"])
    try:
        changed = ensure(client, params, module.check_mode)
    except NexusError as error:
        module.fail_json(msg=str(error))
    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
