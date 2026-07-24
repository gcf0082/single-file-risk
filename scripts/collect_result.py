import sys
import json
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("Usage: collect_result.py <json_string>", file=sys.stderr)
        sys.exit(1)

    raw = sys.argv[1]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        file_key = "(unknown)"
        print(f"✗ 写入失败: {file_key} - JSON 解析错误: {e}")
        sys.exit(1)

    file_key = data.get("file")
    if not file_key:
        print(f"✗ 写入失败: {file_key} - JSON 缺少 'file' 字段")
        sys.exit(1)

    try:
        output_dir = Path.cwd() / ".secscan"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "results.json"

        if output_file.exists():
            with open(output_file, "r") as f:
                aggregate = json.load(f)
        else:
            aggregate = {"files": {}}

        aggregate["files"][file_key] = data
        aggregate["metadata"] = {
            "total_files": len(aggregate["files"]),
        }

        with open(output_file, "w") as f:
            json.dump(aggregate, f, ensure_ascii=False, indent=2)

        print(f"✓ 已记录: {file_key}")
    except Exception as e:
        print(f"✗ 写入失败: {file_key} - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
