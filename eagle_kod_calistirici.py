import os
import runpy
import sys
from pathlib import Path


def _guvenli_yol(path, workspace, read_only=False):
    if not isinstance(path, (str, bytes, Path)):
        return True

    try:
        p = Path(path).resolve()

        # Çalışma alanının içi her zaman izinli.
        try:
            p.relative_to(workspace)
            return True
        except ValueError:
            pass

        # Python'un kendi runtime/kütüphane dosyaları yalnızca okunabilir.
        if read_only:
            try:
                p.relative_to(Path(sys.prefix).resolve())
                return True
            except ValueError:
                pass

        return False
    except (ValueError, OSError):
        return False


def guvenlik_hook(workspace):
    dosya_olaylari = {
        "open",
        "os.remove",
        "os.rename",
        "os.mkdir",
        "os.rmdir",
        "os.chdir",
        "os.chmod",
        "os.chown",
        "os.link",
        "os.symlink",
        "os.truncate",
        "os.utime",
        "os.scandir",
        "os.listdir",
    }

    proses_olaylari = {
        "subprocess.Popen",
        "os.system",
        "os.exec",
        "os.execve",
        "os.execv",
        "os.execvp",
        "os.spawn",
        "os.spawnv",
        "os.spawnve",
        "os.posix_spawn",
        "os.fork",
        "os.forkpty",
        "pty.spawn",
    }

    def hook(event, args):
        if event in proses_olaylari or event.startswith("socket."):
            raise PermissionError(
                f"EAGLE_SECURITY_BLOCK: yasak işlem engellendi: {event}"
            )

        if event not in dosya_olaylari:
            return

        if event == "os.rename":
            yollar = args[:2]
        else:
            yollar = args[:1]

        for yol in yollar:
            if yol is None or isinstance(yol, int):
                continue

            # open olayı için runtime kütüphanelerine yalnızca okuma izni.
            if event == "open":
                mode = args[1] if len(args) > 1 else None
                yazma = isinstance(mode, str) and any(
                    bayrak in mode for bayrak in ("w", "a", "x", "+")
                )

                if not _guvenli_yol(
                    yol,
                    workspace,
                    read_only=not yazma,
                ):
                    raise PermissionError(
                        f"EAGLE_SECURITY_BLOCK: çalışma alanı dışı erişim engellendi: {yol}"
                    )
            elif not _guvenli_yol(yol, workspace):
                raise PermissionError(
                    f"EAGLE_SECURITY_BLOCK: çalışma alanı dışı erişim engellendi: {yol}"
                )

    return hook


def secure_run(file_path: Path, workspace: Path, timeout: int = 10):
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            str(Path(file_path).resolve()),
            str(Path(workspace).resolve()),
        ],
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    return result.returncode == 0, output.strip()


def main():
    if len(sys.argv) != 3:
        print(
            "Kullanim: eagle_kod_calistirici.py <kod_dosyasi> <calisma_klasoru>",
            file=sys.stderr,
        )
        return 2

    kod_dosyasi = Path(sys.argv[1]).resolve()
    workspace = Path(sys.argv[2]).resolve()

    if not kod_dosyasi.is_file():
        print("EAGLE_SECURITY_BLOCK: kod dosyası bulunamadı.", file=sys.stderr)
        return 2

    if not workspace.is_dir():
        print("EAGLE_SECURITY_BLOCK: çalışma klasörü bulunamadı.", file=sys.stderr)
        return 2

    try:
        kod_dosyasi.relative_to(workspace)
    except ValueError:
        print(
            "EAGLE_SECURITY_BLOCK: kod dosyası çalışma alanı dışında.",
            file=sys.stderr,
        )
        return 2

    os.chdir(workspace)
    sys.addaudithook(guvenlik_hook(workspace))

    try:
        runpy.run_path(str(kod_dosyasi), run_name="__main__")
        return 0
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 0
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        return 126
    except Exception:
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
