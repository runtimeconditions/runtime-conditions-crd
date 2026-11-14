"""Exercise Kubernetes schema cost estimation and bounded profile validation."""

import argparse
import copy
import json
from pathlib import Path
import subprocess
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", help="kubectl context; otherwise use KUBECONFIG/current context")
    parser.add_argument("--namespace", default="default", help="existing namespace for dry-run profiles")
    args = parser.parse_args()
    command = ["kubectl"] + (["--context", args.context] if args.context else [])

    def kubectl(*arguments, document=None, check=True):
        result = subprocess.run(
            command + list(arguments),
            input=json.dumps(document) if document is not None else None,
            capture_output=True,
            text=True,
        )
        if check and result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return result

    crd_path = Path(__file__).resolve().parents[1] / "config/crd/bases/runtimeconditions.io_runtimeconditionsprofiles.yaml"
    # Ignore existing ownership only for this non-persistent schema admission check.
    kubectl("apply", "--server-side", "--dry-run=server", "--force-conflicts", "-f", str(crd_path))
    print("PASS CRD admission and estimated validation cost")
    crd = json.loads(kubectl("create", "--dry-run=client", "--validate=false", "-f", str(crd_path), "-o", "json").stdout)
    group = "validation-" + uuid.uuid4().hex[:12] + ".runtimeconditions.io"
    test_crd = copy.deepcopy(crd)
    test_crd["metadata"] = {"name": crd["spec"]["names"]["plural"] + "." + group}
    test_crd["spec"]["group"] = group
    test_crd["spec"]["names"].pop("shortNames", None)
    version = next(v["name"] for v in crd["spec"]["versions"] if v["storage"])

    def condition(name=None):
        value = {"kind": "datastore", "interface": {"type": "relational", "engine": "postgres"}}
        if name is not None:
            value["name"] = name
        return value

    profile = {
        "apiVersion": group + "/" + version,
        "kind": crd["spec"]["names"]["kind"],
        "metadata": {"name": "schema-fixture", "namespace": args.namespace},
        "workload": {"uri": "https://example.test/repository"},
        "extensions": [],
        "conditions": [],
    }
    extension = "https://runtimeconditions.io/extensions/rc/common-integrations:v1alpha2"

    def fixture(name, conditions, extensions, accepted=True):
        value = copy.deepcopy(profile)
        value.update(conditions=conditions, extensions=extensions)
        result = kubectl("create", "--dry-run=server", "-f", "-", "-o", "json", document=value, check=False)
        if accepted and result.returncode:
            raise AssertionError(name + ": " + result.stderr)
        if not accepted and (result.returncode == 0 or "invalid" not in result.stderr.lower()):
            raise AssertionError(name + ": expected schema rejection, got " + result.stdout + result.stderr)
        print("PASS " + name)
        return json.loads(result.stdout) if accepted else None

    created = False
    name = test_crd["metadata"]["name"]
    try:
        kubectl("create", "-f", "-", document=test_crd)
        created = True
        kubectl("wait", "--for=condition=Established", "--timeout=30s", "crd/" + name)
        fixture("empty lists", [], [])
        fixture("distinct names and extension URIs", [condition("db"), condition("other")], [extension, "urn:example:other"])
        fixture("unnamed conditions", [condition(), condition(), condition("db")], [])
        fixture("duplicate condition names", [condition("db"), condition("db")], [], accepted=False)
        fixture("empty condition name", [condition("")], [], accepted=False)
        fixture("duplicate extensions", [], [extension, extension], accepted=False)
        fixture("missing extension scheme", [], ["missing-scheme"], accepted=False)
        conditions_at_limit = [condition("n" * 125 + f"{i:03d}") for i in range(256)]
        uri_prefix = "https://example.test/extensions/"
        uri_padding = "x" * (2048 - len(uri_prefix) - 2)
        extensions_at_limit = [uri_prefix + uri_padding + f"{i:02d}" for i in range(64)]
        fixture("extension size limits", [], extensions_at_limit)
        fixture("condition size limits", conditions_at_limit, [])
        fixture("all approved size limits", conditions_at_limit, extensions_at_limit)
        fixture(
            "extension count above 64", [],
            extensions_at_limit + ["urn:example:extra"], accepted=False,
        )
        fixture(
            "extension URI above 2048 characters", [],
            [extensions_at_limit[0] + "x"], accepted=False,
        )
        fixture(
            "condition count above 256", conditions_at_limit + [condition("extra")],
            [], accepted=False,
        )
        fixture("condition name above 128 characters", [condition("n" * 129)], [], accepted=False)
        extra = condition("db")
        extra["configuration"] = {"host": {"env": "DATABASE_HOST"}}
        extra["interface"]["operations"] = ["read", "write"]
        result = fixture("extension-defined fields", [extra], [extension])
        assert result["conditions"][0]["configuration"] == extra["configuration"]
        assert result["conditions"][0]["interface"]["operations"] == ["read", "write"]
    finally:
        if created:
            kubectl("delete", "crd", name, "--wait=true", "--timeout=30s", "--ignore-not-found=true")
            print("Deleted temporary validation CRD")


if __name__ == "__main__":
    main()
