"""Validate render.yaml against the official Render Blueprint JSON Schema.

Schema: https://render.com/schema/render.yaml.json
Draft: JSON Schema Draft 2020-12
"""

import json
import sys
import jsonschema
import yaml


def validate_blueprint(blueprint_path: str = "render.yaml", schema_path: str = "render_schema.json") -> bool:
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)
    with open(blueprint_path, "r", encoding="utf-8") as f:
        blueprint = yaml.safe_load(f)

    print(f"Loaded blueprint '{blueprint_path}' and schema '{schema_path}'.")

    # 1. Validate the web service specifically against serverService definition
    service_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "definitions": schema.get("definitions", {}),
        "$ref": "#/definitions/serverService",
    }
    validator_svc = jsonschema.Draft202012Validator(service_schema)
    svc_errors = list(validator_svc.iter_errors(blueprint["services"][0]))
    if svc_errors:
        print(f"FAIL: Found {len(svc_errors)} service validation errors:")
        for err in svc_errors:
            print(f"  - {err.message} (path: {list(err.path)})")
        return False
    else:
        svc = blueprint["services"][0]
        print(f"PASS: Web service '{svc.get('name')}' is 100% valid under Render serverService schema!")
        print(f"      plan: '{svc.get('plan')}'")
        print(f"      runtime: '{svc.get('runtime')}'")
        print(f"      branch: '{svc.get('branch')}'")
        print(f"      autoDeployTrigger: '{svc.get('autoDeployTrigger')}'")

    # 2. Validate root structure against resources definition
    resources_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "definitions": schema.get("definitions", {}),
        "$ref": "#/definitions/resources",
    }
    validator_res = jsonschema.Draft202012Validator(resources_schema)
    res_errors = list(validator_res.iter_errors(blueprint))
    if res_errors:
        print(f"FAIL: Found {len(res_errors)} resources validation errors:")
        for err in res_errors:
            print(f"  - {err.message} (path: {list(err.path)})")
        return False
    else:
        print("PASS: Blueprint resources container is 100% valid under Render resources schema!")

    return True


if __name__ == "__main__":
    success = validate_blueprint()
    sys.exit(0 if success else 1)
