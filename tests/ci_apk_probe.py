"""CI 构建产物探针：校验 APK 内含 Chaquopy Python 引擎与关键资源。

用法：python tests/ci_apk_probe.py <apk路径>
失败即 exit 1（CI 阻断）。

校验项：
  R1 APK 可被 zipfile 打开且条目数 > 500
  R2 assets/chaquopy/app.imy 存在，解包后含 runner.pyc / repl.pyc
  R3 runner.pyc 可被 marshal 解析，且引用 threading（看门狗路径）
  R4 assets 内课程与挑战 JSON 存在且可解析（lessons_*.json / challenges.json）
  R5 assets/syntaxes/javascript.tmLanguage.json 存在（多语言高亮）
  R6 AndroidManifest 声明的包名为 com.pyneon.academy（通过 aapt 或 strings 兜底）
"""
import io
import json
import marshal
import sys
import zipfile


def fail(msg):
    print(f"[FAIL] {msg}")
    sys.exit(1)


def code_names(code, acc):
    acc.update(code.co_names)
    for const in code.co_consts:
        if hasattr(const, "co_names"):
            code_names(const, acc)
    return acc


def main():
    if len(sys.argv) != 2:
        fail("用法：python tests/ci_apk_probe.py <apk路径>")
    apk = sys.argv[1]
    try:
        z = zipfile.ZipFile(apk)
    except Exception as exc:  # noqa: BLE001
        fail(f"APK 无法打开：{exc}")

    names = z.namelist()
    if len(names) < 500:
        fail(f"APK 条目数异常：{len(names)}")
    print(f"[PASS] APK 可打开，条目 {len(names)}")

    if "assets/chaquopy/app.imy" not in names:
        fail("缺少 assets/chaquopy/app.imy")
    inner = zipfile.ZipFile(io.BytesIO(z.read("assets/chaquopy/app.imy")))
    pycs = set(inner.namelist())
    for want in ("runner.pyc", "repl.pyc"):
        if want not in pycs:
            fail(f"app.imy 缺少 {want}")
    print(f"[PASS] app.imy 含 {sorted(pycs)}")

    raw = inner.read("runner.pyc")
    try:
        code = marshal.loads(raw[16:])
    except Exception as exc:  # noqa: BLE001
        fail(f"runner.pyc 无法解析：{exc}")
    if "threading" not in code_names(code, set()):
        fail("runner.pyc 未引用 threading（超时看门狗缺失）")
    print("[PASS] runner.pyc 可解析且含 threading 看门狗")

    assets = [n for n in names if n.startswith("app/src/main/assets/") or n.startswith("assets/lessons_")]
    if not assets:
        # Chaquopy/AGP 可能把 assets 放在 assets/ 根：直接按文件名核对
        assets = [n for n in names if n.endswith(("lessons_basic.json", "lessons_mid.json", "lessons_adv.json", "lessons_pro.json", "challenges.json"))]
    required_assets = ("lessons_basic.json", "lessons_mid.json", "lessons_adv.json", "lessons_pro.json", "challenges.json")
    for want in required_assets:
        hit = [n for n in names if n.endswith(want)]
        if not hit:
            fail(f"APK 缺少 assets/{want}")
        json.loads(z.read(hit[0]).decode("utf-8"))
    print(f"[PASS] 课程与挑战 JSON 完整且可解析（{len(required_assets)} 个）")

    syn = [n for n in names if n.endswith("syntaxes/javascript.tmLanguage.json")]
    if not syn:
        fail("APK 缺少 syntaxes/javascript.tmLanguage.json")
    print("[PASS] JavaScript 语法高亮资源存在")

    # AXML 是二进制格式，字符串资源以 UTF-16LE 存储
    manifest = z.read("AndroidManifest.xml").decode("utf-16-le", "ignore")
    if "com.pyneon.academy" not in manifest:
        fail("AndroidManifest 中未找到包名 com.pyneon.academy")
    print("[PASS] AndroidManifest 包名就位")
    print("ALL APK PROBES PASSED")


if __name__ == "__main__":
    main()
