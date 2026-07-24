import sys
import json
from pathlib import Path


def main():
    output_dir = Path.cwd() / ".secscan"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "results.json"
    has_error = False

    results = []
    if output_file.exists():
        try:
            with open(output_file, "r") as f:
                results = json.load(f)
        except json.JSONDecodeError:
            results = []

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
            results.append(data)
            print(f"✓ 已记录: {file_key}")
        except Exception as e:
            print(f"✗ 写入失败: {file_key} - {e}")
            has_error = True

    try:
        with open(output_file, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"✗ 写入文件失败: {e}")
        sys.exit(1)

    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
