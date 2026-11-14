# runtime-conditions-crd
A Kubernetes CRD for storing Runtime Conditions Profiles as a Kubernetes resource

Requires Kubernetes 1.33 or later. The CRD retains URI-scheme validation,
uniqueness checks, optional condition names, and default atomic list behavior.
Condition-name uniqueness uses a single-pass CEL map check to stay within the
runtime validation budget at the supported size limit. The following limits
also bound the estimated cost of the CEL validation rules:

| Field | Maximum |
| --- | ---: |
| Extensions per profile | 64 |
| Characters per extension URI | 2,048 |
| Conditions per profile | 256 |
| Characters per condition name | 128 |

After editing the Go schema, regenerate with `make manifests generate`.

Run `make helm-chart` before `helm lint charts/runtime-conditions-crd` or
`helm package charts/runtime-conditions-crd`. Chart version `0.1.1` includes
the bounded CRD schema.

Run `make test-admission` with `KUBECONFIG` selecting a test or management cluster,
or run `python3 tests/test_crd_admission.py --context <context>` explicitly.
The test first dry-runs the CRD under its real name, then installs a uniquely named test CRD,
checks positive and negative profile fixtures, including every size boundary,
using server-side dry runs, and deletes the test CRD. It persists no profile
instances. The selected identity
needs CRD create/delete permissions and permission to dry-run test profiles.
