#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Inject custom China Anycast CIDRs into Sing-Box and Meta/Clash geoip rulesets.
"""

import os
import sys
import json
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
CIDR_FILE = os.path.join(SCRIPT_DIR, "china-anycast-cidrs.txt")

def load_custom_cidrs():
    if not os.path.exists(CIDR_FILE):
        print(f"[inject-cidrs] Warning: {CIDR_FILE} not found.")
        return []
    cidrs = []
    with open(CIDR_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                cidrs.append(line)
    return cidrs

def load_custom_domains():
    domain_file = os.path.join(SCRIPT_DIR, "china-custom-domains.txt")
    if not os.path.exists(domain_file):
        return []
    domains = []
    with open(domain_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                domains.append(line)
    return domains

def inject_sing_box(cidrs):
    targets = [
        os.path.join(REPO_ROOT, "sing-rule", "geo", "geoip", "cn.json"),
        os.path.join(REPO_ROOT, "sing-rule", "geo-lite", "geoip", "cn.json")
    ]
    for target in targets:
        if not os.path.exists(target):
            continue
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            rules = data.get("rules", [{}])[0].get("ip_cidr", [])
            added = 0
            for c in cidrs:
                if c not in rules:
                    rules.insert(0, c)
                    added += 1
            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[inject-cidrs] Injected {added} CIDRs into {target}")
            
            srs_path = target[:-4] + "srs"
            try:
                subprocess.run(["sing-box", "rule-set", "compile", target, "-o", srs_path], check=True)
                print(f"[inject-cidrs] Successfully compiled {srs_path}")
            except Exception as e:
                print(f"[inject-cidrs] Failed to compile {srs_path}: {e}")
        except Exception as e:
            print(f"[inject-cidrs] Error processing {target}: {e}")

def inject_sing_box_domains(domains):
    targets = [
        os.path.join(REPO_ROOT, "sing-rule", "geo", "geosite", "cn.json"),
        os.path.join(REPO_ROOT, "sing-rule", "geo-lite", "geosite", "cn.json")
    ]
    for target in targets:
        if not os.path.exists(target):
            continue
        try:
            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)
            rules = data.get("rules", [{}])[0].get("domain_suffix", [])
            added = 0
            for d in domains:
                if d not in rules:
                    rules.insert(0, d)
                    added += 1
            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"[inject-cidrs] Injected {added} domains into {target}")
            
            srs_path = target[:-4] + "srs"
            try:
                subprocess.run(["sing-box", "rule-set", "compile", target, "-o", srs_path], check=True)
                print(f"[inject-cidrs] Successfully compiled {srs_path}")
            except Exception as e:
                print(f"[inject-cidrs] Failed to compile {srs_path}: {e}")
        except Exception as e:
            print(f"[inject-cidrs] Error processing {target}: {e}")

def inject_meta_clash(cidrs):
    targets = [
        (os.path.join(REPO_ROOT, "meta-rule", "geo", "geoip", "cn.yaml"), "yaml"),
        (os.path.join(REPO_ROOT, "meta-rule", "geo-lite", "geoip", "cn.yaml"), "yaml"),
        (os.path.join(REPO_ROOT, "meta-rule", "geo", "geoip", "cn.list"), "list"),
        (os.path.join(REPO_ROOT, "meta-rule", "geo-lite", "geoip", "cn.list"), "list")
    ]
    for target, fmt in targets:
        if not os.path.exists(target):
            continue
        try:
            with open(target, "r", encoding="utf-8") as f:
                lines = f.readlines()
            added = 0
            with open(target, "a", encoding="utf-8") as f:
                for c in cidrs:
                    if not any(c in l for l in lines):
                        if fmt == "yaml":
                            f.write(f"    - {c}\n")
                        else:
                            f.write(f"{c}\n")
                        added += 1
            print(f"[inject-cidrs] Injected {added} CIDRs into {target}")
        except Exception as e:
            print(f"[inject-cidrs] Error processing {target}: {e}")

def inject_meta_clash_domains(domains):
    targets = [
        (os.path.join(REPO_ROOT, "meta-rule", "geo", "geosite", "cn.yaml"), "yaml"),
        (os.path.join(REPO_ROOT, "meta-rule", "geo-lite", "geosite", "cn.yaml"), "yaml"),
        (os.path.join(REPO_ROOT, "meta-rule", "geo", "geosite", "cn.list"), "list"),
        (os.path.join(REPO_ROOT, "meta-rule", "geo-lite", "geosite", "cn.list"), "list")
    ]
    for target, fmt in targets:
        if not os.path.exists(target):
            continue
        try:
            with open(target, "r", encoding="utf-8") as f:
                lines = f.readlines()
            added = 0
            with open(target, "a", encoding="utf-8") as f:
                for d in domains:
                    entry = f"+.{d}" if fmt == "yaml" else f"+.{d}"
                    if not any(d in l for l in lines):
                        if fmt == "yaml":
                            f.write(f"    - '{entry}'\n")
                        else:
                            f.write(f"{entry}\n")
                        added += 1
            print(f"[inject-cidrs] Injected {added} domains into {target}")
        except Exception as e:
            print(f"[inject-cidrs] Error processing {target}: {e}")

def main():
    cidrs = load_custom_cidrs()
    if cidrs:
        print(f"[inject-cidrs] Found {len(cidrs)} custom CIDRs to inject.")
        inject_sing_box(cidrs)
        inject_meta_clash(cidrs)
    else:
        print("[inject-cidrs] No custom CIDRs to inject.")

    domains = load_custom_domains()
    if domains:
        print(f"[inject-cidrs] Found {len(domains)} custom domains to inject.")
        inject_sing_box_domains(domains)
        inject_meta_clash_domains(domains)
    else:
        print("[inject-cidrs] No custom domains to inject.")

if __name__ == "__main__":
    main()
