#!/usr/bin/python
# Copyright: (c) 2026, Amirhosein Shaerpour <shaerpourr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
module: user
short_description: Manage Nexus local users
version_added: 0.6.0
description:
  - Create, update or delete users in the default local Nexus user source.
  - Existing values of omitted profile and role options are preserved.
  - Nexus never returns passwords. By default passwords are set only when creating a user.
  - LDAP, SAML and other external users are not managed by this module.
author:
  - Amirhosein Shaerpour (@shaerpour)
extends_documentation_fragment:
  - shaerpour.nexus.connection
options:
  user_id:
    description: Login ID of the user to manage. This is distinct from I(username), used to connect to Nexus.
    type: str
    required: true
  state:
    description:
      - C(present) creates the user, or updates managed settings when they differ.
      - C(absent) deletes the local user without requiring profile options or a password.
    type: str
    choices: [present, absent]
    default: present
  first_name:
    description: First name. Required and must not be empty when creating a user.
    type: str
  last_name:
    description: Last name. Required and must not be empty when creating a user.
    type: str
  email:
    description: Email address. Required and must not be empty when creating a user.
    type: str
  status:
    description: Account status. Omitted values are preserved on update and default to C(active) on creation.
    type: str
    choices: [active, locked, disabled, changepassword]
  roles:
    description:
      - Nexus role IDs assigned to the user. Roles must already exist.
      - Replaces the local role assignments when supplied. Order and duplicates are ignored.
      - Defaults to no roles on creation. Omitted values are preserved on update.
    type: list
    elements: str
  user_password:
    description:
      - Password of the managed user, distinct from I(password), used to connect to Nexus.
      - Required and must not be empty when creating a user or when I(update_password=always).
    type: str
  update_password:
    description:
      - C(on_create) sets the password only when creating a user.
      - C(always) resets the password on every run and reports a change, even if the password is unchanged.
      - Check mode reports the password change without applying it.
    type: str
    choices: [on_create, always]
    default: on_create
"""

EXAMPLES = r"""
- name: Create a local package reader
  shaerpour.nexus.user:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    user_id: package-reader
    first_name: Package
    last_name: Reader
    email: package-reader@example.com
    roles: [nx-anonymous]
    user_password: "{{ package_reader_password }}"

- name: Disable a user while preserving other profile fields and roles
  shaerpour.nexus.user:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    user_id: package-reader
    status: disabled

- name: Rotate a local user's password
  shaerpour.nexus.user:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    user_id: package-reader
    user_password: "{{ package_reader_password }}"
    update_password: always

- name: Delete a local user
  shaerpour.nexus.user:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    user_id: package-reader
    state: absent
"""

RETURN = r""" # """

from urllib.parse import quote, urlencode

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.shaerpour.nexus.plugins.module_utils.client import (
    AUTH_ARGUMENT_SPEC,
    NexusClient,
    NexusError,
)

PROFILE_FIELDS = {"first_name": "firstName", "last_name": "lastName", "email": "emailAddress", "status": "status"}


def build_payload(params, current):
    """Build a full user body, preserving fields that the task does not manage."""
    payload = {"userId": params["user_id"], "source": "default"}
    for option, field in PROFILE_FIELDS.items():
        payload[field] = params[option] if params[option] is not None else (current or {}).get(field)
    if payload["status"] is None:
        payload["status"] = "active"
    roles = params["roles"] if params["roles"] is not None else (current or {}).get("roles", [])
    payload["roles"] = sorted(set(roles))
    return payload


def is_subset(desired, current):
    """Compare managed fields, treating role assignments as an unordered set."""
    if isinstance(desired, dict):
        return isinstance(current, dict) and all(
            key in current and is_subset(value, current[key]) for key, value in desired.items()
        )
    if isinstance(desired, list):
        return isinstance(current, list) and set(desired) == set(current)
    return desired == current


def ensure_absent(client, user_id, current, check_mode):
    """Delete the local user if present. Return True when something changed."""
    if current is None:
        return False
    if not check_mode:
        client.request("DELETE", f"/security/users/{quote(user_id, safe='')}")
    return True


def ensure_present(client, params, current, check_mode):
    """Create or update the user and apply the requested password policy."""
    payload = build_payload(params, current)
    if current is None:
        missing = [option for option in ("first_name", "last_name", "email", "user_password") if not params[option]]
        if missing:
            raise NexusError(f"Creating a user requires non-empty options: {', '.join(missing)}")
        if not check_mode:
            client.request("POST", "/security/users", {**payload, "password": params["user_password"]})
        return True

    profile_changed = not is_subset(payload, current)
    password_changed = params["update_password"] == "always"
    if not check_mode:
        path = f"/security/users/{quote(params['user_id'], safe='')}"
        if profile_changed:
            client.request("PUT", path, payload)
        if password_changed:
            client.request("PUT", f"{path}/change-password", params["user_password"], content_type="text/plain")
    return profile_changed or password_changed


def ensure(client, params, check_mode):
    """Find the exact local user and bring it to the requested state."""
    query = urlencode({"userId": params["user_id"], "source": "default"})
    users = client.request("GET", f"/security/users?{query}") or []
    current = next((user for user in users if user["userId"] == params["user_id"] and user["source"] == "default"), None)
    if params["state"] == "absent":
        return ensure_absent(client, params["user_id"], current, check_mode)
    return ensure_present(client, params, current, check_mode)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **AUTH_ARGUMENT_SPEC,
            user_id=dict(type="str", required=True),
            state=dict(type="str", default="present", choices=["present", "absent"]),
            first_name=dict(type="str"),
            last_name=dict(type="str"),
            email=dict(type="str"),
            status=dict(type="str", choices=["active", "locked", "disabled", "changepassword"]),
            roles=dict(type="list", elements="str"),
            user_password=dict(type="str", no_log=True),
            update_password=dict(type="str", default="on_create", choices=["on_create", "always"], no_log=False),
        ),
        supports_check_mode=True,
    )
    params = module.params
    if not params["user_id"]:
        module.fail_json(msg="user_id must not be empty")
    if params["state"] == "present" and params["update_password"] == "always" and not params["user_password"]:
        module.fail_json(msg="update_password=always requires a non-empty user_password")
    client = NexusClient(params["url"], params["username"], params["password"], params["validate_certs"])
    try:
        changed = ensure(client, params, module.check_mode)
    except NexusError as error:
        module.fail_json(msg=str(error))
    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
