import re
import os
import subprocess
import shutil
from pathlib import Path
import time

class EagleAutoFixEngine:
    def __init__(self, project_root=".", max_attempts=3):
        self.project_root = Path(project_root).resolve()
        self.max_attempts = max_attempts
        self.backup_dir = self.project_root / ".eagle_backups"
        self.backup_dir.mkdir(exist_ok=True)

        # AutoFix yalnızca proje içindeki Python dosyalarında çalışabilir.
        self.allowed_extensions = {".py"}
        self.blocked_parts = {".git", ".eagle_backups", "__pycache__"}

    def is_safe_target(self, file_path: Path) -> tuple[bool, str]:
        """AutoFix hedefinin güvenli ve proje içinde olduğunu doğrular."""
        try:
            target = Path(file_path).resolve()

            if target.suffix.lower() not in self.allowed_extensions:
                return False, "Yalnızca Python (.py) dosyaları değiştirilebilir."

            if any(part in self.blocked_parts for part in target.parts):
                return False, "Engellenmiş bir dizindeki dosya değiştirilemez."

            target.relative_to(self.project_root)

            if not target.is_file():
                return False, "Hedef dosya mevcut bir dosya değil."

            return True, "Güvenli hedef."
        except ValueError:
            return False, "Hedef dosya proje klasörü dışında."
        except Exception as e:
            return False, f"Güvenlik kontrolü başarısız: {e}"

    def discover_files(self, keyword: str) -> list:
        matched_files = []
        for path in self.project_root.rglob("*.py"):
            if ".eagle_backups" in path.parts or ".git" in path.parts:
                continue
            try:
                content = path.read_text(encoding="utf-8")
                if keyword.lower() in content.lower() or keyword.lower() in path.name.lower():
                    matched_files.append(path)
            except Exception:
                continue
        return matched_files

    def create_backup(self, file_path: Path) -> Path:
        timestamp = int(time.time())
        backup_path = self.backup_dir / f"{file_path.name}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def rollback(self, backup_path: Path, target_path: Path):
        if backup_path.exists():
            shutil.copy2(backup_path, target_path)
            print(f"[GÜVENLİK] Rollback yapıldı: {target_path} eski haline döndürüldü.")

    def check_syntax(self, file_path: Path) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["python3", "-m", "py_compile", str(file_path)],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return True, "Syntax geçerli."
            return False, result.stderr
        except Exception as e:
            return False, str(e)

    def run_tests(self) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                ["pytest"], capture_output=True, text=True, timeout=10
            )
            output = result.stdout + "\n" + result.stderr
            return result.returncode == 0, output
        except Exception as e:
            return False, str(e)

    def analyze_error(self, error_text: str) -> dict:
        """Traceback'i derinlemesine analiz eder; kodu değiştirmez."""
        text = str(error_text or "").strip()

        error_types = [
            "SyntaxError", "IndentationError", "NameError",
            "TypeError", "ValueError", "IndexError", "KeyError",
            "ImportError", "ModuleNotFoundError"
        ]
        detected = next(
            (name for name in error_types if name in text),
            "UnknownError"
        )

        # Python traceback'indeki son dosya/satır bilgisini yakala.
        traceback_matches = re.findall(
            r'File ["\']([^"\']+)["\'], line (\d+)(?:, in ([^\n]+))?',
            text
        )

        file_path = None
        line_number = None
        function_name = None
        code_line = None

        if traceback_matches:
            file_path, line_number, function_name = traceback_matches[-1]
            line_number = int(line_number)

            # Traceback'teki "File ..., line ..." satırından sonraki
            # kod satırını mümkün olduğunca yakala.
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if (
                    file_path in line
                    and f"line {line_number}" in line
                    and i + 1 < len(lines)
                ):
                    candidate = lines[i + 1].strip()
                    if candidate and not candidate.startswith("File "):
                        code_line = candidate
                    break

        undefined_name = self.extract_undefined_name(text)

        suggested_name = None
        if undefined_name:
            suggestion_match = re.search(
                r"Did you mean: [\'\"]([^\'\"]+)[\'\"]",
                text
            )
            if suggestion_match:
                suggested_name = suggestion_match.group(1)

        # Kanıt seviyesini belirle.
        evidence = []
        if file_path:
            evidence.append("dosya")
        if line_number is not None:
            evidence.append("satır")
        if function_name:
            evidence.append("fonksiyon")
        if code_line:
            evidence.append("kod_satırı")
        if undefined_name:
            evidence.append("tanımsız_isim")
        if suggested_name:
            evidence.append("python_onerisi")

        confidence = "düşük"
        if detected != "UnknownError" and len(evidence) >= 2:
            confidence = "orta"
        if (
            detected == "NameError"
            and undefined_name
            and suggested_name
            and file_path
            and line_number is not None
        ):
            confidence = "yüksek"

        return {
            "type": detected,
            "message": text,
            "has_error": bool(text),
            "file": file_path,
            "line": line_number,
            "function": function_name,
            "code_line": code_line,
            "undefined_name": undefined_name,
            "suggested_name": suggested_name,
            "evidence": evidence,
            "confidence": confidence
        }

    def extract_undefined_name(self, error_text: str) -> str | None:
        """NameError mesajından tanımsız ismi çıkarır."""
        import re
        match = re.search(r"NameError: name ['\"]([^'\"]+)['\"] is not defined", str(error_text or ""))
        return match.group(1) if match else None

    def suggest_fix(self, error_info: dict) -> dict:
        """Hata türüne göre güvenli düzeltme önerisi üretir; dosyayı değiştirmez."""
        error_type = str(error_info.get("type", "UnknownError"))
        rules = {
            "NameError": "Tanımsız değişken veya isim kontrol edilmeli; isim tanımlanmalı veya doğru isim kullanılmalı.",
            "SyntaxError": "Hata mesajındaki satır ve sözdizimi kontrol edilmeli.",
            "IndentationError": "Girinti seviyeleri ve blok yapısı kontrol edilmeli.",
            "TypeError": "İşleme giren veri tipleri ve dönüşümler kontrol edilmeli.",
            "ValueError": "Fonksiyona verilen değerin geçerli olup olmadığı kontrol edilmeli.",
            "IndexError": "Liste/koleksiyon indeks sınırları kontrol edilmeli.",
            "KeyError": "Sözlük anahtarının mevcut olup olmadığı kontrol edilmeli.",
            "ImportError": "Modül adı ve import yolu kontrol edilmeli.",
            "ModuleNotFoundError": "Gerekli modülün kurulu ve doğru adla çağrıldığı kontrol edilmeli."
        }
        suggestion = rules.get(error_type, "Hata mesajı ve ilgili kod bölümü ayrıntılı olarak incelenmeli.")
        if error_type == "NameError":
            undefined_name = self.extract_undefined_name(error_info.get("message", ""))
            if undefined_name:
                suggestion = f"Tanımsız isim: {undefined_name}. Önce bu ismin nerede tanımlanması gerektiği veya doğru değişken adının ne olduğu belirlenmeli."
        return {
            "type": error_type,
            "suggestion": suggestion
        }

    def run_file(self, file_path: Path) -> tuple[bool, str]:
        """Python dosyasını çalıştırır ve hata çıktısını yakalar; dosyayı değiştirmez."""
        try:
            result = subprocess.run(
                ["python3", str(file_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            output = (result.stdout or "") + "\n" + (result.stderr or "")
            return result.returncode == 0, output.strip()
        except Exception as e:
            return False, str(e)

    def repair_loop(self, target_file: Path) -> dict:
        """Hata -> analiz -> güvenli düzeltme -> doğrulama döngüsü."""
        target_file = Path(target_file)

        safe, safety_reason = self.is_safe_target(target_file)
        if not safe:
            return {
                "success": False,
                "reason": safety_reason,
                "attempts": 0
            }

        if not target_file.exists():
            return {
                "success": False,
                "reason": "Hedef dosya bulunamadı.",
                "attempts": 0
            }

        backup_path = self.create_backup(target_file)
        attempts = 0
        history = []

        try:
            while attempts < self.max_attempts:
                attempts += 1

                ok, output = self.run_file(target_file)

                if ok:
                    return {
                        "success": True,
                        "reason": "Dosya düzeltme sonrası başarıyla çalıştı.",
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

                error_info = self.analyze_error(output)
                history.append({
                    "attempt": attempts,
                    "error": error_info
                })

                if error_info.get("confidence") != "yüksek":
                    self.rollback(backup_path, target_file)
                    return {
                        "success": False,
                        "reason": "Hata için yeterli güvenli kanıt bulunamadı.",
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

                fix = self.apply_known_fix(target_file, error_info)

                if not fix.get("fixed"):
                    self.rollback(backup_path, target_file)
                    return {
                        "success": False,
                        "reason": fix.get("reason", "Güvenli düzeltme uygulanamadı."),
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

                history[-1]["fix"] = fix

                syntax_ok, syntax_msg = self.check_syntax(target_file)
                if not syntax_ok:
                    self.rollback(backup_path, target_file)
                    return {
                        "success": False,
                        "reason": "Düzeltme sonrası syntax kontrolü başarısız.",
                        "syntax_error": syntax_msg,
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

            self.rollback(backup_path, target_file)

            return {
                "success": False,
                "reason": "Maksimum otomatik düzeltme denemesine ulaşıldı.",
                "attempts": attempts,
                "history": history,
                "backup": str(backup_path)
            }

        except Exception as e:
            self.rollback(backup_path, target_file)
            return {
                "success": False,
                "reason": f"AutoFix döngüsünde beklenmeyen hata: {e}",
                "attempts": attempts,
                "history": history,
                "backup": str(backup_path)
            }

    def apply_known_fix(self, target_file: Path, error_info: dict) -> dict:
        """Python traceback'inden kanıtlanabilir NameError düzeltmesini uygular."""
        import re

        error_type = str(error_info.get("type", ""))
        if error_type != "NameError":
            return {"fixed": False, "reason": "Güvenli bilinen düzeltme kuralı yok."}

        message = str(error_info.get("message", ""))
        undefined_name = self.extract_undefined_name(message)
        if not undefined_name:
            return {"fixed": False, "reason": "Tanımsız isim çıkarılamadı."}

        match = re.search(r"Did you mean: [\'\"]([^\'\"]+)[\'\"]", message)
        if not match:
            return {"fixed": False, "reason": "Python tarafından güvenilir 'Did you mean' önerisi verilmedi."}

        replacement = match.group(1)
        if not replacement.isidentifier() or replacement == undefined_name:
            return {"fixed": False, "reason": "Önerilen isim güvenli değil."}

        content = target_file.read_text(encoding="utf-8")
        occurrences = len(re.findall(rf"\b{re.escape(undefined_name)}\b", content))
        if occurrences != 1:
            return {"fixed": False, "reason": f"Tanımsız isim dosyada tam 1 kez bulunmalı; bulunan: {occurrences}."}

        if not re.search(rf"\b{re.escape(replacement)}\s*=", content):
            return {"fixed": False, "reason": "Önerilen isim dosyada tanımlı görünmüyor."}

        backup_path = self.create_backup(target_file)
        new_content = re.sub(rf"\b{re.escape(undefined_name)}\b", replacement, content)
        target_file.write_text(new_content, encoding="utf-8")

        return {
            "fixed": True,
            "old_name": undefined_name,
            "replacement": replacement,
            "backup": str(backup_path)
        }

    def apply_fix_and_test(self, target_file: Path):
        """Güvenli yedekleme, syntax, test ve rollback döngüsü."""
        print(f"\n[OTONOM DÖNGÜ] Başlatıldı. Hedef: {target_file}")
        
        # 1. Backup al
        backup_path = self.create_backup(target_file)
        print(f"[YEDEK] Backup oluşturuldu: {backup_path}")

        attempt = 0
        while attempt < self.max_attempts:
            attempt += 1
            print(f"--- Deneme {attempt}/{self.max_attempts} ---")

            # 2. Syntax kontrolü
            syntax_ok, syntax_msg = self.check_syntax(target_file)
            if not syntax_ok:
                print(f"[HATA] Syntax hatası tespit edildi: {syntax_msg}")
                self.rollback(backup_path, target_file)
                return False

            # 3. Testleri çalıştır
            success, test_output = self.run_tests()

            if success:
                print(f"[BAŞARILI] Testler başarıyla geçti. Dosya değiştirilmeden bırakıldı.")
                return True
            else:
                print(f"[TEST BAŞARISIZ] Hata çıktısı:\n{test_output[:200]}...")

        # 6. Maksimum deneme aşılırsa rollback yap
        print(f"[BAŞARISIZ] Maksimum deneme sınırına ({self.max_attempts}) ulaşıldı. Rollback yapılıyor.")
        self.rollback(backup_path, target_file)
        return False
