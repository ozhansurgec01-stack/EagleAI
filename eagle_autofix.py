import re
import os
import subprocess
import shutil
from pathlib import Path
import time

from eagle_kod_analiz_motoru import EagleKodAnalizMotoru

class EagleAutoFixEngine:
    def __init__(self, project_root=".", max_attempts=3):
        self.project_root = Path(project_root).resolve()
        self.max_attempts = max_attempts
        self.backup_dir = self.project_root / ".eagle_backups"
        self.backup_dir.mkdir(exist_ok=True)

        # AutoFix yalnızca proje içindeki Python dosyalarında çalışabilir.
        self.allowed_extensions = {".py"}
        self.blocked_parts = {".git", ".eagle_backups", "__pycache__"}
        self.analiz_motoru = EagleKodAnalizMotoru()

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

    def analyze_code(self, target_file: Path) -> dict:
        """Kodun statik analizini yapar; dosyayı değiştirmez."""
        target_file = Path(target_file)

        safe, reason = self.is_safe_target(target_file)
        if not safe:
            return {
                "ok": False,
                "reason": reason,
                "findings": []
            }

        try:
            source = target_file.read_text(encoding="utf-8")
            findings = self.analiz_motoru.analiz_et(source)

            return {
                "ok": True,
                "reason": "Statik kod analizi tamamlandı.",
                "findings": findings,
                "count": len(findings)
            }
        except Exception as exc:
            return {
                "ok": False,
                "reason": f"Statik analiz hatası: {exc}",
                "findings": []
            }

    def repair_loop(self, target_file: Path) -> dict:
        """Statik analiz + mantık + güvenli düzeltme + doğrulama döngüsü."""
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

        # İşlem başlangıcında tek güvenlik yedeği.
        backup_path = self.create_backup(target_file)
        attempts = 0
        history = []

        try:
            while attempts < self.max_attempts:
                attempts += 1

                # -------------------------------------------------
                # 1 — STATİK ANALİZ
                # -------------------------------------------------
                analiz = self.analyze_code(target_file)

                if not analiz.get("ok"):
                    self.rollback(backup_path, target_file)
                    return {
                        "success": False,
                        "reason": analiz.get(
                            "reason",
                            "Statik analiz başarısız."
                        ),
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

                findings = analiz.get("findings", [])

                # -------------------------------------------------
                # 2 — MANTIK ANALİZİ
                # -------------------------------------------------
                source = target_file.read_text(
                    encoding="utf-8"
                )

                mantik = self.analiz_motoru.mantik_analizi(
                    source,
                    findings
                )

                history.append({
                    "attempt": attempts,
                    "static_findings": findings,
                    "logic_analysis": mantik
                })

                # -------------------------------------------------
                # 3 — YÜKSEK GÜVENLİ DÜZELTME ADAYI
                # -------------------------------------------------
                aday = None

                # Güvenli düzeltmeler için öncelik sırası.
                # Önce doğrudan uygulanabilen güvenli mantık düzeltmeleri.
                oncelik = {
                    "OffByOneRangeFix": 1,
                    "ZeroDivisionGuard": 2,
                }

                adaylar = [
                    karar for karar in mantik
                    if (
                        karar.get("guven") == "yüksek"
                        and karar.get("karar") == "DUZELTME_ADAYI"
                        and karar.get("duzeltme_adayi")
                    )
                ]

                adaylar.sort(
                    key=lambda karar: oncelik.get(
                        karar.get("duzeltme_adayi", {}).get("tur")
                        if isinstance(karar.get("duzeltme_adayi"), dict)
                        else "",
                        99
                    )
                )

                # Daha önce uygulanmış güvenli düzeltmeleri tekrar seçme.
                uygulanmis_turler = set()
                for gecmis in history:
                    fix_gecmis = gecmis.get("logic_fix")
                    if isinstance(fix_gecmis, dict):
                        tur_gecmis = fix_gecmis.get("tur") or fix_gecmis.get("rule")
                        if tur_gecmis:
                            uygulanmis_turler.add(tur_gecmis)

                adaylar = [
                    karar for karar in adaylar
                    if (
                        not isinstance(karar.get("duzeltme_adayi"), dict)
                        or (
                            karar["duzeltme_adayi"].get("tur")
                            not in uygulanmis_turler
                        )
                    )
                ]

                if adaylar:
                    aday = adaylar[0]

                if aday:
                    duzeltme = aday["duzeltme_adayi"]

                    # ZeroDivisionGuard → mevcut güvenli AutoFix motoru
                    if isinstance(duzeltme, dict) and duzeltme.get("tur") == "ZeroDivisionGuard":
                        fix = self.apply_known_fix(
                            target_file,
                            {"type": "ZeroDivision"}
                        )

                        if fix.get("fixed"):
                            history[-1]["logic_fix"] = fix

                            syntax_ok, syntax_msg = self.check_syntax(target_file)

                            if syntax_ok:
                                run_ok, run_output = self.run_file(target_file)

                                history[-1]["verification"] = {
                                    "syntax_ok": syntax_ok,
                                    "run_ok": run_ok,
                                    "output": run_output
                                }

                                if run_ok:
                                    return {
                                        "success": True,
                                        "reason": "ZeroDivision düzeltmesi uygulandı ve test başarılı.",
                                        "attempts": attempts,
                                        "history": history,
                                        "backup": str(backup_path),
                                        "fixed_code": target_file.read_text(encoding="utf-8").strip(),
                                    }

                                # Runtime başka bir hata veriyorsa mevcut düzeltmeyi koru.
                                # Döngünün başına dönüp kodu yeniden analiz et.
                                continue

                    # OffByOneRangeFix: bilinen güvenli düzeltmeyi uygula.
                    if duzeltme.get("tur") == "OffByOneRangeFix":
                        fix = self.apply_known_fix(
                            target_file,
                            {"type": "OffByOneRange"}
                        )

                        if fix.get("fixed"):
                            syntax_ok, syntax_msg = self.check_syntax(target_file)
                            if not syntax_ok:
                                self.rollback(backup_path, target_file)
                                return {
                                    "success": False,
                                    "reason": "OffByOne düzeltmesi sonrası syntax kontrolü başarısız.",
                                    "syntax_error": syntax_msg,
                                    "attempts": attempts,
                                    "history": history,
                                    "backup": str(backup_path),
                                }

                            run_ok, run_output = self.run_file(target_file)
                            history[-1]["logic_fix"] = fix
                            history[-1]["verification"] = {
                                "syntax_ok": syntax_ok,
                                "run_ok": run_ok,
                                "output": run_output,
                            }

                            if run_ok:
                                return {
                                    "success": True,
                                    "reason": "OffByOne düzeltmesi uygulandı ve syntax + çalışma testi başarıyla geçti.",
                                    "attempts": attempts,
                                    "history": history,
                                    "backup": str(backup_path),
                                    "fixed_code": target_file.read_text(encoding="utf-8").strip(),
                                }

                        # OffByOne düzeltmesi çalışma testinde başarısız oldu.
                        # Döngünün başına dönüp kodu yeniden analiz et.
                        continue


                    if isinstance(duzeltme, dict) and duzeltme.get("tur") in (
                        "MissingColonFix", "ReservedKeywordFix", "UnclosedParenFix"
                    ):
                        tur_map = {
                            "MissingColonFix": "MissingColon",
                            "ReservedKeywordFix": "ReservedKeywordName",
                            "UnclosedParenFix": "UnclosedParen",
                        }
                        fix_info = {
                            "type": tur_map[duzeltme["tur"]],
                            "satir": aday.get("satir"),
                        }
                        if duzeltme["tur"] == "ReservedKeywordFix":
                            fix_info["eski_isim"] = duzeltme.get("eski_isim")

                        fix = self.apply_known_fix(target_file, fix_info)

                        if fix.get("fixed"):
                            history[-1]["logic_fix"] = fix
                            syntax_ok, syntax_msg = self.check_syntax(target_file)

                            if not syntax_ok:
                                # Dosyada başka bir syntax hatası kalmış olabilir;
                                # elde edilen kısmi düzeltmeyi geri almadan
                                # döngünün başına dön ve bir sonraki hatayı ara.
                                history[-1]["verification"] = {
                                    "syntax_ok": False,
                                    "syntax_error": syntax_msg,
                                }
                                continue

                            run_ok, run_output = self.run_file(target_file)
                            history[-1]["verification"] = {
                                "syntax_ok": syntax_ok,
                                "run_ok": run_ok,
                                "output": run_output,
                            }

                            if run_ok:
                                return {
                                    "success": True,
                                    "reason": (
                                        f"{duzeltme['tur']} uygulandı ve "
                                        "syntax + çalışma testi başarıyla geçti."
                                    ),
                                    "attempts": attempts,
                                    "history": history,
                                    "backup": str(backup_path),
                                    "fixed_code": target_file.read_text(
                                        encoding="utf-8"
                                    ).strip(),
                                }

                        continue

                    eski = duzeltme.get("eski")
                    yeni_ad = duzeltme.get("yeni")

                    if eski and yeni_ad:
                        import re

                        content = target_file.read_text(
                            encoding="utf-8"
                        )

                        # Sadece güvenli identifier değişikliklerine izin ver.
                        if (
                            isinstance(eski, str)
                            and isinstance(yeni_ad, str)
                            and eski.isidentifier()
                            and yeni_ad.isidentifier()
                            and eski != yeni_ad
                        ):
                            pattern = rf"\b{re.escape(eski)}\b"
                            occurrences = len(
                                re.findall(pattern, content)
                            )

                            # Yazım hatası düzeltmesinde tek kullanım şartı.
                            if occurrences == 1:
                                new_content = re.sub(
                                    pattern,
                                    yeni_ad,
                                    content
                                )

                                if new_content != content:
                                    target_file.write_text(
                                        new_content,
                                        encoding="utf-8"
                                    )

                                    history[-1]["logic_fix"] = {
                                        "fixed": True,
                                        "old": eski,
                                        "new": yeni_ad,
                                        "reason": aday.get(
                                            "neden",
                                            ""
                                        )
                                    }

                                    # Syntax doğrulaması.
                                    syntax_ok, syntax_msg = (
                                        self.check_syntax(target_file)
                                    )

                                    if not syntax_ok:
                                        self.rollback(
                                            backup_path,
                                            target_file
                                        )
                                        return {
                                            "success": False,
                                            "reason": (
                                                "Mantıksal düzeltme sonrası "
                                                "syntax kontrolü başarısız."
                                            ),
                                            "syntax_error": syntax_msg,
                                            "attempts": attempts,
                                            "history": history,
                                            "backup": str(backup_path)
                                        }

                                    # Gerçek dosya testi.
                                    run_ok, run_output = (
                                        self.run_file(target_file)
                                    )

                                    history[-1]["verification"] = {
                                        "syntax_ok": syntax_ok,
                                        "run_ok": run_ok,
                                        "output": run_output
                                    }

                                    if run_ok:
                                        return {
                                            "success": True,
                                            "reason": (
                                                "Mantıksal düzeltme uygulandı "
                                                "ve syntax + çalışma testi "
                                                "başarıyla geçti."
                                            ),
                                            "attempts": attempts,
                                            "history": history,
                                            "backup": str(backup_path)
                                        }

                                    # Çalışmadıysa mevcut traceback
                                    # analiz zincirine devam et.
                                    output = run_output
                                else:
                                    output = ""
                            else:
                                output = ""
                        else:
                            output = ""
                    else:
                        output = ""
                else:
                    # Mantıksal otomatik düzeltme yoksa mevcut
                    # runtime analizine geç.
                    output_ok, output = self.run_file(target_file)

                    if output_ok:
                        return {
                            "success": True,
                            "reason": (
                                "Kod statik analiz ve çalışma "
                                "kontrolünden geçti."
                            ),
                            "attempts": attempts,
                            "history": history,
                            "backup": str(backup_path)
                        }

                # -------------------------------------------------
                # 4 — RUNTIME HATASI
                # -------------------------------------------------
                if not output:
                    self.rollback(
                        backup_path,
                        target_file
                    )
                    return {
                        "success": False,
                        "reason": (
                            "Mantıksal düzeltme adayı doğrulanamadı "
                            "ve devam edilecek runtime hatası yok."
                        ),
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

                error_info = self.analyze_error(output)

                history[-1]["runtime_error"] = error_info

                if error_info.get("confidence") != "yüksek":
                    self.rollback(
                        backup_path,
                        target_file
                    )
                    return {
                        "success": False,
                        "reason": (
                            "Hata için yeterli güvenli kanıt bulunamadı."
                        ),
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

                # -------------------------------------------------
                # 5 — MEVCUT GÜVENLİ RUNTIME DÜZELTMELERİ
                # -------------------------------------------------
                fix = self.apply_known_fix(
                    target_file,
                    error_info
                )

                if not fix.get("fixed"):
                    self.rollback(
                        backup_path,
                        target_file
                    )
                    return {
                        "success": False,
                        "reason": fix.get(
                            "reason",
                            "Güvenli düzeltme uygulanamadı."
                        ),
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

                history[-1]["fix"] = fix

                syntax_ok, syntax_msg = self.check_syntax(
                    target_file
                )

                if not syntax_ok:
                    self.rollback(
                        backup_path,
                        target_file
                    )
                    return {
                        "success": False,
                        "reason": (
                            "Düzeltme sonrası syntax kontrolü başarısız."
                        ),
                        "syntax_error": syntax_msg,
                        "attempts": attempts,
                        "history": history,
                        "backup": str(backup_path)
                    }

            self.rollback(
                backup_path,
                target_file
            )

            return {
                "success": False,
                "reason": (
                    "Maksimum otomatik düzeltme denemesine ulaşıldı."
                ),
                "attempts": attempts,
                "history": history,
                "backup": str(backup_path)
            }

        except Exception as e:
            self.rollback(
                backup_path,
                target_file
            )

            return {
                "success": False,
                "reason": (
                    f"AutoFix döngüsünde beklenmeyen hata: {e}"
                ),
                "attempts": attempts,
                "history": history,
                "backup": str(backup_path)
            }


    def apply_known_fix(self, target_file: Path, error_info: dict) -> dict:
        """Kanıtlanabilir güvenli düzeltmeleri uygular."""

        import re

        error_type = str(error_info.get("type", ""))

        if error_type == "MissingColon":
            content = target_file.read_text(encoding="utf-8")
            satirlar = content.splitlines()
            satir_no = error_info.get("satir")
            if not satir_no or not (1 <= satir_no <= len(satirlar)):
                return {
                    "fixed": False,
                    "reason": "MissingColon: satır numarası geçersiz."
                }
            idx = satir_no - 1
            satir = satirlar[idx]
            if satir.rstrip().endswith(":"):
                return {
                    "fixed": False,
                    "reason": "MissingColon: satır zaten ':' ile bitiyor."
                }
            satirlar[idx] = satir.rstrip() + ":"
            target_file.write_text(
                "\n".join(satirlar) + "\n", encoding="utf-8"
            )
            return {
                "fixed": True,
                "tur": "MissingColonFix",
                "aciklama": f"{satir_no}. satır sonuna ':' eklendi.",
            }

        if error_type == "ReservedKeywordName":
            import re
            import keyword as _kw

            eski_isim = error_info.get("eski_isim")
            satir_no = error_info.get("satir")

            if not eski_isim or not _kw.iskeyword(eski_isim):
                return {
                    "fixed": False,
                    "reason": "ReservedKeywordName: geçersiz isim."
                }
            if not satir_no:
                return {
                    "fixed": False,
                    "reason": "ReservedKeywordName: satır numarası eksik."
                }

            content = target_file.read_text(encoding="utf-8")
            satirlar = content.splitlines()
            idx = satir_no - 1

            if not (0 <= idx < len(satirlar)):
                return {
                    "fixed": False,
                    "reason": "ReservedKeywordName: satır numarası geçersiz."
                }

            for_satiri = satirlar[idx]
            girinti = len(for_satiri) - len(for_satiri.lstrip())

            blok_son = idx
            for j in range(idx + 1, len(satirlar)):
                satir_j = satirlar[j]
                if satir_j.strip() == "":
                    blok_son = j
                    continue
                girinti_j = len(satir_j) - len(satir_j.lstrip())
                if girinti_j > girinti:
                    blok_son = j
                else:
                    break

            tum_metin = "\n".join(satirlar)
            yeni_isim = f"{eski_isim}_deger"
            while re.search(rf"\b{re.escape(yeni_isim)}\b", tum_metin):
                yeni_isim += "_"

            for k in range(idx, blok_son + 1):
                satirlar[k] = re.sub(
                    rf"\b{re.escape(eski_isim)}\b", yeni_isim, satirlar[k]
                )

            target_file.write_text(
                "\n".join(satirlar) + "\n", encoding="utf-8"
            )
            return {
                "fixed": True,
                "tur": "ReservedKeywordFix",
                "aciklama": (
                    f"{satir_no}. satırdaki döngü kapsamında "
                    f"'{eski_isim}' -> '{yeni_isim}' olarak değiştirildi."
                ),
            }

        if error_type == "UnclosedParen":
            content = target_file.read_text(encoding="utf-8")
            satirlar = content.splitlines()
            satir_no = error_info.get("satir")
            if not satir_no or not (1 <= satir_no <= len(satirlar)):
                return {
                    "fixed": False,
                    "reason": "UnclosedParen: satır numarası geçersiz."
                }
            idx = satir_no - 1
            satir = satirlar[idx]
            acik = satir.count("(") - satir.count(")")
            if acik <= 0:
                return {
                    "fixed": False,
                    "reason": "UnclosedParen: satırda eksik parantez bulunamadı."
                }
            satirlar[idx] = satir + (")" * acik)
            target_file.write_text(
                "\n".join(satirlar) + "\n", encoding="utf-8"
            )
            return {
                "fixed": True,
                "tur": "UnclosedParenFix",
                "aciklama": f"{satir_no}. satıra {acik} eksik ')' eklendi.",
            }

        # Statik analiz: ZeroDivision için güvenli koşullu ifade.
        if error_type == "ZeroDivision":
            import ast
            import re

            content = target_file.read_text(encoding="utf-8")

            try:
                tree = ast.parse(content)
            except SyntaxError:
                return {
                    "fixed": False,
                    "reason": "ZeroDivision düzeltmesi öncesi syntax geçersiz."
                }

            for node in ast.walk(tree):
                if not isinstance(node, ast.BinOp):
                    continue

                if not isinstance(
                    node.op,
                    (ast.Div, ast.FloorDiv, ast.Mod)
                ):
                    continue

                if not isinstance(node.right, ast.Name):
                    continue

                payda = node.right.id

                # Paydanın gerçekten 0'a atandığını doğrula.
                sifir_atama = re.search(
                    rf"(?m)^\s*{re.escape(payda)}\s*=\s*0\s*$",
                    content
                )

                if not sifir_atama:
                    continue

                satirlar = content.splitlines()
                satir_no = node.lineno - 1

                if not (0 <= satir_no < len(satirlar)):
                    continue

                satir = satirlar[satir_no]

                # Basit atama veya return ifadesini güvenli biçimde değiştir.
                match = re.match(
                    r"^(\s*)([A-Za-z_]\w*\s*=\s*)(.+?)\s*$",
                    satir
                )

                if match:
                    girinti = match.group(1)
                    atama = match.group(2)
                    ifade = match.group(3)

                    if f"{payda} != 0" in ifade:
                        return {
                            "fixed": False,
                            "reason": "ZeroDivision koruması zaten mevcut."
                        }

                    yeni_ifade = (
                        f"({ifade}) if {payda} != 0 else 0"
                    )

                    satirlar[satir_no] = (
                        girinti + atama + yeni_ifade
                    )

                else:
                    return_match = re.match(
                        r"^(\s*)return\s+(.+?)\s*$",
                        satir
                    )

                    if not return_match:
                        continue

                    girinti = return_match.group(1)
                    ifade = return_match.group(2)

                    if f"{payda} != 0" in ifade:
                        return {
                            "fixed": False,
                            "reason": "ZeroDivision koruması zaten mevcut."
                        }

                    yeni_ifade = (
                        f"({ifade}) if {payda} != 0 else 0"
                    )

                    satirlar[satir_no] = (
                        f"{girinti}return {yeni_ifade}"
                    )


                new_content = "\n".join(satirlar)

                if content.endswith("\n"):
                    new_content += "\n"

                target_file.write_text(
                    new_content,
                    encoding="utf-8"
                )

                return {
                    "fixed": True,
                    "rule": "ZeroDivisionGuard",
                    "variable": payda,
                    "replacement": yeni_ifade
                }

            return {
                "fixed": False,
                "reason": "Güvenli ZeroDivision düzeltme noktası bulunamadı."
            }

        # Statik analiz: OffByOneRange için güvenli düzeltme.
        if error_type == "OffByOneRange":
            content = target_file.read_text(encoding="utf-8")

            import re

            pattern = re.compile(
                r"range\(\s*len\(\s*([A-Za-z_]\w*)\s*\)\s*-\s*1\s*\)"
            )
            matches = list(pattern.finditer(content))

            if len(matches) != 1:
                return {
                    "fixed": False,
                    "reason": "Güvenli OffByOne düzeltmesi için tam olarak bir eşleşme bulunmalı."
                }

            match = matches[0]
            liste = match.group(1)
            eski = match.group(0)
            yeni = f"range(len({liste}))"

            new_content = (
                content[:match.start()]
                + yeni
                + content[match.end():]
            )

            target_file.write_text(new_content, encoding="utf-8")

            return {
                "fixed": True,
                "rule": "OffByOneRangeFix",
                "replacement": f"{eski} -> {yeni}"
            }

        # Runtime NameError: yalnızca Python'un güvenilir önerisi varsa.
        if error_type == "NameError":
            message = str(error_info.get("message", ""))
            undefined_name = self.extract_undefined_name(message)

            if not undefined_name:
                return {
                    "fixed": False,
                    "reason": "Tanımsız isim çıkarılamadı."
                }

            match = re.search(
                r"Did you mean: ['\"]([^'\"]+)['\"]",
                message
            )

            if not match:
                return {
                    "fixed": False,
                    "reason": "Python tarafından güvenilir 'Did you mean' önerisi verilmedi."
                }

            replacement = match.group(1)

            if (
                not replacement.isidentifier()
                or replacement == undefined_name
            ):
                return {
                    "fixed": False,
                    "reason": "Önerilen isim güvenli değil."
                }

            content = target_file.read_text(encoding="utf-8")

            occurrences = len(
                re.findall(
                    rf"\b{re.escape(undefined_name)}\b",
                    content
                )
            )

            if occurrences != 1:
                return {
                    "fixed": False,
                    "reason": (
                        "Tanımsız isim dosyada tam 1 kez bulunmalı; "
                        f"bulunan: {occurrences}."
                    )
                }

            if not re.search(
                rf"\b{re.escape(replacement)}\s*=",
                content
            ):
                return {
                    "fixed": False,
                    "reason": "Önerilen isim dosyada tanımlı görünmüyor."
                }

            backup_path = self.create_backup(target_file)

            new_content = re.sub(
                rf"\b{re.escape(undefined_name)}\b",
                replacement,
                content
            )

            target_file.write_text(
                new_content,
                encoding="utf-8"
            )

            return {
                "fixed": True,
                "old_name": undefined_name,
                "replacement": replacement,
                "backup": str(backup_path)
            }

        # Statik analiz: BareExcept güvenli dönüşüm.
        if error_type == "BareExcept":
            content = target_file.read_text(encoding="utf-8")

            if not re.search(r"(?m)^\s*except\s*:\s*$", content):
                return {
                    "fixed": False,
                    "reason": "Güvenli bare except bulunamadı."
                }

            backup_path = self.create_backup(target_file)

            new_content = re.sub(
                r"(?m)^(\s*)except\s*:\s*$",
                r"\1except Exception:",
                content
            )

            if new_content == content:
                return {
                    "fixed": False,
                    "reason": "Düzeltme uygulanamadı."
                }

            target_file.write_text(
                new_content,
                encoding="utf-8"
            )

            return {
                "fixed": True,
                "rule": "BareExcept",
                "replacement": "except Exception:",
                "backup": str(backup_path)
            }

        return {
            "fixed": False,
            "reason": "Güvenli bilinen düzeltme kuralı yok."
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
