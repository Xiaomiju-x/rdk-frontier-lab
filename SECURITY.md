# Security policy

## Reporting

Do not post credentials, private endpoints, confidential logs or exploitable
details in public issues. Use [GitHub private vulnerability reporting](https://github.com/Xiaomiju-x/rdk-frontier-lab/security/advisories/new).
If reporting is unavailable, contact the maintainer through GitHub without
including sensitive details and request a private channel.

Include the affected version, a minimal synthetic reproducer, expected and actual
behaviour, and impact. Do not test against somebody else's board or network.

## Supported versions

The latest tagged 0.1.x release receives security fixes on a best-effort basis.
Development snapshots and third-party runtimes are not covered by a support SLA.

## Threat model

The toolkit validates local data supplied by a user. It rejects duplicate JSON
keys, non-finite metrics, unsafe manifest paths, hash mismatches and contradictory
execution claims. These checks are **not a sandbox, signature system or remote
attestation**. Do not execute a submitted runner because its JSON passed validation.

The filesystem must not be actively modified by an adversary while a manifest is
being verified. Path validation reduces accidental and static traversal risks;
it does not provide race-free filesystem isolation. Use an isolated, read-only
input directory for untrusted submissions.

No core command downloads a model, opens a device, runs a subprocess or performs
network I/O. Optional algorithms and developer tools have separate dependencies.
Review vendor tools and model formats before enabling them in your own environment.

Hosted CI has no board credentials and must never run untrusted PR code on a
self-hosted hardware runner. Do not use `pull_request_target` to execute PR code.
