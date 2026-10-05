#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Ensure the custom CIDRs injection step exists in .github/workflows/run.yml.
Used by sync-upstream workflow to guarantee zero merge conflict with upstream.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
WORKFLOW_FILE = os.path.join(REPO_ROOT, ".github", "workflows", "run.yml")

HOOK_STEP = """      - name: Inject custom China Anycast CIDRs
        run: |
          go install -v -trimpath -ldflags="-s -w -buildid=" github.com/sagernet/sing-box/cmd/sing-box@latest || true
          if [ -f "custom-rules/inject-cidrs.py" ]; then
            python3 custom-rules/inject-cidrs.py
          fi
"""

def main():
    if not os.path.exists(WORKFLOW_FILE):
        print(f"[ensure-workflow] {WORKFLOW_FILE} does not exist.")
        return 1

    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    if "Inject custom China Anycast CIDRs" in content:
        print("[ensure-workflow] Hook step already present in run.yml.")
        return 0

    # Insert before "- name: Convert asn" or before "- name: Build BundleMRS.7z"
    anchor = "- name: Convert asn"
    if anchor in content:
        content = content.replace(f"      {anchor}", f"{HOOK_STEP}\n      {anchor}")
    else:
        anchor_alt = "- name: Build BundleMRS.7z"
        if anchor_alt in content:
            content = content.replace(f"      {anchor_alt}", f"{HOOK_STEP}\n      {anchor_alt}")
        else:
            print("[ensure-workflow] Anchor not found, appending to jobs.")
            content += f"\n{HOOK_STEP}"

    with open(WORKFLOW_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print("[ensure-workflow] Successfully injected custom CIDR hook step into run.yml.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
