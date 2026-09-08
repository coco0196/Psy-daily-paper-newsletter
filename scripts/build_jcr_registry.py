"""从用户提供的 JCR Excel 生成运行时使用的紧凑期刊索引。"""

import argparse
import csv
import os
import re

import pandas as pd


QUARTILE_ORDER = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}


def normalize_issn(value):
    return re.sub(r"[^0-9X]", "", str(value or "").upper())


def normalize_name(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).strip()


def nonempty(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def main():
    parser = argparse.ArgumentParser(description="构建 JCR 期刊运行时索引")
    parser.add_argument("input_xlsx")
    parser.add_argument("output_csv")
    args = parser.parse_args()

    frame = pd.read_excel(args.input_xlsx, header=1)
    expected = {
        "期刊名", "ISSN号", "eISSN号", "Wos学科信息", "2025影响因子", "分区"
    }
    missing = expected.difference(frame.columns)
    if missing:
        raise ValueError(f"JCR Excel 缺少字段: {sorted(missing)}")

    groups = {}
    for row in frame.to_dict("records"):
        name = nonempty(row["期刊名"])
        pissn = nonempty(row["ISSN号"])
        eissn = nonempty(row["eISSN号"])
        identity = normalize_issn(pissn) or normalize_issn(eissn) or normalize_name(name)
        if not identity:
            continue
        item = groups.setdefault(
            identity,
            {
                "journal_name": name,
                "pissn": pissn,
                "eissn": eissn,
                "impact_factor": "",
                "quartiles": set(),
            },
        )
        if not item["pissn"] and pissn:
            item["pissn"] = pissn
        if not item["eissn"] and eissn:
            item["eissn"] = eissn
        impact_factor = nonempty(row["2025影响因子"])
        if impact_factor and not item["impact_factor"]:
            item["impact_factor"] = impact_factor
        quartile = nonempty(row["分区"]).upper()
        if quartile in QUARTILE_ORDER:
            item["quartiles"].add(quartile)

    rows = []
    for item in groups.values():
        quartiles = sorted(item["quartiles"], key=QUARTILE_ORDER.get)
        rows.append(
            {
                "journal_name": item["journal_name"],
                "pissn": item["pissn"],
                "eissn": item["eissn"],
                "impact_factor": item["impact_factor"],
                "best_quartile": quartiles[0] if quartiles else "",
                "all_quartiles": "|".join(quartiles),
            }
        )

    rows.sort(key=lambda item: normalize_name(item["journal_name"]))
    os.makedirs(os.path.dirname(os.path.abspath(args.output_csv)), exist_ok=True)
    with open(args.output_csv, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "journal_name", "pissn", "eissn", "impact_factor",
                "best_quartile", "all_quartiles",
            ),
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"generated {len(rows)} journal profiles: {args.output_csv}")


if __name__ == "__main__":
    main()
