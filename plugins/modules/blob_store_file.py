#!/usr/bin/python
# Copyright: (c) 2026, Amirhosein Shaerpour <shaerpourr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
module: blob_store_file
short_description: Manage Nexus file blob stores
version_added: 0.5.0
description:
  - Create, update or delete a Nexus blob store that keeps its content on the local file system.
  - A blob store that is used by a repository cannot be deleted.
author:
  - Amirhosein Shaerpour (@shaerpour)
extends_documentation_fragment:
  - shaerpour.nexus.connection
options:
  name:
    description: Name of the blob store.
    type: str
    required: true
  state:
    description:
      - C(present) creates the blob store, or updates it when its settings differ.
      - C(absent) deletes the blob store.
    type: str
    choices: [present, absent]
    default: present
  path:
    description:
      - Directory of the blob store, relative to the blob directory of Nexus.
      - Defaults to I(name).
      - Changing the path of an existing blob store does not move its content.
    type: str
  soft_quota_type:
    description:
      - Kind of the soft quota. Nexus only raises an alert when the quota is reached.
      - C(space_used) alerts when the blob store uses more than I(soft_quota_limit) bytes.
      - C(space_remaining) alerts when less than I(soft_quota_limit) bytes are free.
      - Without a soft quota, an existing one is removed.
      - Must be used together with I(soft_quota_limit).
    type: str
    choices: [space_used, space_remaining]
  soft_quota_limit:
    description:
      - Limit of the soft quota in bytes.
      - Must be used together with I(soft_quota_type).
    type: int
"""

EXAMPLES = r"""
- name: Create a file blob store
  shaerpour.nexus.blob_store_file:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: docker-blobs

- name: Create a file blob store that alerts at 100 GiB
  shaerpour.nexus.blob_store_file:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: maven-blobs
    path: maven
    soft_quota_type: space_used
    soft_quota_limit: 107374182400

- name: Delete a blob store
  shaerpour.nexus.blob_store_file:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: docker-blobs
    state: absent
"""

RETURN = r""" # """

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.shaerpour.nexus.plugins.module_utils.client import (
    AUTH_ARGUMENT_SPEC,
    NexusClient,
    NexusError,
)

QUOTA_TYPES = {"space_used": "spaceUsedQuota", "space_remaining": "spaceRemainingQuota"}


def build_payload(params):
    """Build the request body that Nexus expects for the requested blob store."""
    soft_quota = None
    if params["soft_quota_type"]:
        soft_quota = {"type": QUOTA_TYPES[params["soft_quota_type"]], "limit": params["soft_quota_limit"]}
    return {"path": params["path"] or params["name"], "softQuota": soft_quota}


def is_subset(desired, current):
    """Return True when every value in ``desired`` is also set in ``current``.

    Nexus does not return the name and may return other fields we do not send, so only the fields we manage are compared.
    """
    if isinstance(desired, dict):
        return isinstance(current, dict) and all(
            key in current and is_subset(value, current[key]) for key, value in desired.items()
        )
    return desired == current


def ensure_absent(client, name, current, check_mode):
    """Delete the blob store if it exists. Return True when something changed."""
    if current is None:
        return False
    if not check_mode:
        client.request("DELETE", f"/blobstores/{name}")
    return True


def ensure_present(client, params, current, check_mode):
    """Create the blob store, or update it when it differs. Return True when something changed."""
    payload = build_payload(params)

    if current is None:
        if not check_mode:
            client.request("POST", "/blobstores/file", {"name": params["name"], **payload})
        return True

    if is_subset(payload, current):
        return False
    if not check_mode:
        client.request("PUT", f"/blobstores/file/{params['name']}", payload)
    return True


def ensure(client, params, check_mode):
    """Bring the blob store to the requested state. Return True when something changed."""
    name = params["name"]
    current = client.request("GET", f"/blobstores/file/{name}")

    if params["state"] == "absent":
        return ensure_absent(client, name, current, check_mode)
    return ensure_present(client, params, current, check_mode)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **AUTH_ARGUMENT_SPEC,
            name=dict(type="str", required=True),
            state=dict(type="str", default="present", choices=["present", "absent"]),
            path=dict(type="str"),
            soft_quota_type=dict(type="str", choices=list(QUOTA_TYPES)),
            soft_quota_limit=dict(type="int"),
        ),
        required_together=[("soft_quota_type", "soft_quota_limit")],
        supports_check_mode=True,
    )
    params = module.params
    client = NexusClient(params["url"], params["username"], params["password"], params["validate_certs"])

    try:
        changed = ensure(client, params, module.check_mode)
    except NexusError as error:
        module.fail_json(msg=str(error))

    module.exit_json(changed=changed)


if __name__ == "__main__":
    main()
