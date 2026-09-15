# AGENTS.md

This repo is currently just a Kubernetes CRD (`RuntimeConditionsProfile`,
`runtimeconditions.io/v1alpha1`). There is no controller, no webhook, and no
manager binary in this repo.

## Files that matter

| Path | What it is |
| --- | --- |
| `api/v1alpha1/runtimeconditionsprofile_types.go` | The actual CRD schema. Edit this. |
| `api/v1alpha1/zz_generated.deepcopy.go` | Generated from the file above. DO NOT EDIT by hand - run `make generate`. |
| `config/crd/bases/*.yaml` | Generated CRD manifest. DO NOT EDIT by hand - run `make manifests`. |
| `config/samples/*.yaml` | Example CR. Edit these if the schema changes. |
| `config/rbac/runtimeconditionsprofile_{admin,editor,viewer}_role.yaml` | Convenience ClusterRoles for people/service accounts using the CRD. Not tied to any controller. |
| `charts/runtime-conditions-crd/` | Helm chart wrapping the CRD (+ the same RBAC convenience roles, toggled by `rbac.create`). Published as an OCI artifact to GHCR on push to main. `crds/*.yaml` and `templates/rbac.yaml` are derived from `config/crd/bases/` and `config/rbac/` by `make helm-chart` - not committed, don't hand-edit them. Run `make helm-chart` before `helm lint`/`helm package` locally. |

After editing `api/v1alpha1/*_types.go`, always run:

```sh
make manifests generate
go build ./... && go vet ./...
```

