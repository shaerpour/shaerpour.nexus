=============================
shaerpour.nexus Release Notes
=============================

.. contents:: Topics

v0.5.1
======

Bugfixes
--------

- repository_apt - do not require ``distribution`` for proxy repositories.

v0.5.0
======

Minor Changes
-------------

- blob_store_file - add module to manage file blob stores
- blob_store_s3 - add module to manage S3 blob stores

New Modules
-----------

- shaerpour.nexus.blob_store_file - Manage Nexus file blob stores.
- shaerpour.nexus.blob_store_s3 - Manage Nexus S3 blob stores.

v0.4.0
======

Minor Changes
-------------

- repository_go - add module to manage go repositories
- repository_helm - add module to manage Helm repositories
- repository_nuget - add module to manage Nuget repositories
- repository_yum - add module to manage yum repositories

New Modules
-----------

- shaerpour.nexus.repository_go - Manage Nexus Go repositories.
- shaerpour.nexus.repository_helm - Manage Nexus Helm repositories.
- shaerpour.nexus.repository_nuget - Manage Nexus NuGet repositories.
- shaerpour.nexus.repository_yum - Manage Nexus Yum repositories.

v0.3.0
======

Minor Changes
-------------

- repository_alpine - add module to manage Alpine repositories
- repository_apt - add module to manage APT repositories
- repository_npm - add module to manage NPM repositories

New Modules
-----------

- shaerpour.nexus.repository_alpine - Manage Nexus Alpine repositories.
- shaerpour.nexus.repository_apt - Manage Nexus APT repositories.
- shaerpour.nexus.repository_npm - Manage Nexus npm repositories.

v0.2.0
======

Minor Changes
-------------

- repository_composer - add module to manage Composer repositories
- repository_maven - add module to manage Maven repositories
- repository_pypi - add module to manage PyPI repositories

New Modules
-----------

- shaerpour.nexus.repository_composer - Manage Nexus Composer repositories.
- shaerpour.nexus.repository_maven - Manage Nexus Maven repositories.
- shaerpour.nexus.repository_pypi - Manage Nexus PyPI repositories.

v0.1.0
======

Major Changes
-------------

- repository_docker - new module to manage Docker repositories.
- repository_raw - new module to manage raw repositories.

New Modules
-----------

- shaerpour.nexus.repository_docker - Manage Nexus Docker repositories.
- shaerpour.nexus.repository_raw - Manage Nexus raw repositories.
