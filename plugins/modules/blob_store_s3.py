#!/usr/bin/python
# Copyright: (c) 2026, Amirhosein Shaerpour <shaerpourr@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

DOCUMENTATION = r"""
module: blob_store_s3
short_description: Manage Nexus S3 blob stores
version_added: 0.5.0
description:
  - Create, update or delete a Nexus blob store that keeps its content in an S3 bucket.
  - Works with AWS S3 and with S3 compatible services such as MinIO.
  - A blob store that is used by a repository cannot be deleted.
  - Nexus does not return the secret access key and the session token, so a change to them alone is not detected.
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
  bucket:
    description:
      - Name of the S3 bucket.
      - Required when I(state=present).
    type: str
  region:
    description: Region of the bucket. Use C(DEFAULT) to let Nexus pick the default region.
    type: str
    default: DEFAULT
  prefix:
    description: Prefix of the object keys, to share one bucket between several blob stores.
    type: str
  endpoint:
    description: URL of an S3 compatible service. Leave it out to use AWS S3.
    type: str
  force_path_style:
    description: Whether to use path-style access (C(https://host/bucket)) instead of virtual-hosted style.
    type: bool
  access_key_id:
    description: Access key ID. Leave it out to use the default AWS credential chain of Nexus.
    type: str
  secret_access_key:
    description: Secret access key that belongs to I(access_key_id).
    type: str
  session_token:
    description: Session token of temporary credentials.
    type: str
  assume_role:
    description: ARN of an IAM role that Nexus assumes to access the bucket.
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
- name: Create an S3 blob store on AWS
  shaerpour.nexus.blob_store_s3:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: s3-blobs
    bucket: nexus-blobs
    region: eu-central-1
    access_key_id: "{{ aws_access_key_id }}"
    secret_access_key: "{{ aws_secret_access_key }}"

- name: Create an S3 blob store on MinIO
  shaerpour.nexus.blob_store_s3:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: minio-blobs
    bucket: nexus-blobs
    endpoint: https://minio.example.com
    force_path_style: true
    access_key_id: "{{ minio_access_key }}"
    secret_access_key: "{{ minio_secret_key }}"

- name: Delete a blob store
  shaerpour.nexus.blob_store_s3:
    url: https://nexus.example.com
    username: "{{ nexus_username }}"
    password: "{{ nexus_password }}"
    name: s3-blobs
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

# Nexus never returns these, so they cannot be compared.
SECRET_FIELDS = ("secretAccessKey", "sessionToken")


def drop_empty(values):
    """Return ``values`` without the options that were not set."""
    return {key: value for key, value in values.items() if value is not None}


def build_payload(params):
    """Build the request body that Nexus expects for the requested blob store."""
    soft_quota = None
    if params["soft_quota_type"]:
        soft_quota = {"type": QUOTA_TYPES[params["soft_quota_type"]], "limit": params["soft_quota_limit"]}

    bucket_configuration = {
        "bucket": drop_empty({"name": params["bucket"], "region": params["region"], "prefix": params["prefix"]}),
        "bucketSecurity": drop_empty(
            {
                "accessKeyId": params["access_key_id"],
                "secretAccessKey": params["secret_access_key"],
                "sessionToken": params["session_token"],
                "role": params["assume_role"],
            }
        ),
        "advancedBucketConnection": drop_empty(
            {"endpoint": params["endpoint"], "forcePathStyle": params["force_path_style"]}
        ),
    }
    return {"softQuota": soft_quota, "bucketConfiguration": bucket_configuration}


def without_secrets(payload):
    """Return a copy of the request body without the fields Nexus does not return."""
    security = payload["bucketConfiguration"]["bucketSecurity"]
    stripped = {key: value for key, value in security.items() if key not in SECRET_FIELDS}
    bucket_configuration = {**payload["bucketConfiguration"], "bucketSecurity": stripped}
    return {**payload, "bucketConfiguration": bucket_configuration}


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
    body = {"name": params["name"], **payload}

    if current is None:
        if not check_mode:
            client.request("POST", "/blobstores/s3", body)
        return True

    if is_subset(without_secrets(payload), current):
        return False
    if not check_mode:
        client.request("PUT", f"/blobstores/s3/{params['name']}", body)
    return True


def ensure(client, params, check_mode):
    """Bring the blob store to the requested state. Return True when something changed."""
    name = params["name"]
    current = client.request("GET", f"/blobstores/s3/{name}")

    if params["state"] == "absent":
        return ensure_absent(client, name, current, check_mode)
    return ensure_present(client, params, current, check_mode)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            **AUTH_ARGUMENT_SPEC,
            name=dict(type="str", required=True),
            state=dict(type="str", default="present", choices=["present", "absent"]),
            bucket=dict(type="str"),
            region=dict(type="str", default="DEFAULT"),
            prefix=dict(type="str"),
            endpoint=dict(type="str"),
            force_path_style=dict(type="bool"),
            access_key_id=dict(type="str"),
            secret_access_key=dict(type="str", no_log=True),
            session_token=dict(type="str", no_log=True),
            assume_role=dict(type="str"),
            soft_quota_type=dict(type="str", choices=list(QUOTA_TYPES)),
            soft_quota_limit=dict(type="int"),
        ),
        required_if=[("state", "present", ["bucket"])],
        required_together=[
            ("soft_quota_type", "soft_quota_limit"),
            ("access_key_id", "secret_access_key"),
        ],
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
