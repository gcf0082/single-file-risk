import sys
import json
from pathlib import Path


def main():
    output_dir = Path.cwd() / ".secscan"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "results.jsonl"
    has_error = False

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            data = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"✗ 写入失败: (unknown) - JSON 解析错误: {e}")
            has_error = True
            continue

        file_key = data.get("file")
        if not file_key:
            print(f"✗ 写入失败: (unknown) - JSON 缺少 'file' 字段")
            has_error = True
            continue

        try:
            with open(output_file, "a") as f:
                f.write(line + "\n")
            print(f"✓ 已记录: {file_key}")
        except Exception as e:
            print(f"✗ 写入失败: {file_key} - {e}")
            has_error = True

    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
