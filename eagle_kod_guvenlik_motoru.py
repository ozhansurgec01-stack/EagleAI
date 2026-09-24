import ast


class EagleKodGuvenlikMotoru:
    """Kod çalıştırılmadan önce temel riskleri kontrol eder."""

    YASAK_IMPORTLAR = {
        "os",
        "subprocess",
        "socket",
        "shutil",
        "ctypes",
        "multiprocessing",
        "signal",
    }

    YASAK_CAGRI = {
        "eval",
        "exec",
        "system",
        "popen",
        "remove",
        "unlink",
        "rmdir",
        "__import__",
        "import_module",
    }

    def kontrol_et(self, kod: str) -> dict:
        try:
            agac = ast.parse(kod)
        except SyntaxError as exc:
            return {
                "guvenli": False,
                "neden": f"Syntax hatası: {exc.msg}",
                "bulgular": [],
            }

        bulgular = []

        for node in ast.walk(agac):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    kok = alias.name.split(".")[0]
                    if kok in self.YASAK_IMPORTLAR:
                        bulgular.append(
                            f"Yasak import: {alias.name}"
                        )

            elif isinstance(node, ast.ImportFrom):
                kok = (node.module or "").split(".")[0]
                if kok in self.YASAK_IMPORTLAR:
                    bulgular.append(
                        f"Yasak import: {node.module}"
                    )

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.YASAK_CAGRI:
                        bulgular.append(
                            f"Yasak çağrı: {node.func.id}()"
                        )

                elif isinstance(node.func, ast.Attribute):
                    if node.func.attr in self.YASAK_CAGRI:
                        bulgular.append(
                            f"Yasak çağrı: {node.func.attr}()"
                        )

        return {
            "guvenli": not bulgular,
            "neden": (
                "Kod güvenlik kontrolünden geçti."
                if not bulgular
                else "Kod çalıştırma güvenlik kontrolünde engellendi."
            ),
            "bulgular": bulgular,
        }
