import ast
from pathlib import Path


class EagleKodAnalizMotoru:
    """
    İzole Eagle kod analiz laboratuvarı.

    Bu motor:
    - AST ile statik analiz yapar.
    - Kodun davranışını değiştirmez.
    - Gerçek proje dosyalarını değiştirmez.
    - eagle_api.py ve eagle_autofix.py'ye dokunmaz.
    """

    BUILTIN_SHADOWS = {
        "list", "dict", "set", "str", "int", "float",
        "bool", "id", "input", "open", "type", "sum",
        "min", "max", "len", "range", "format"
    }

    def __init__(self):
        self.bulgular = []

    def analiz_et(self, kaynak_kodu: str):
        self.bulgular = []

        try:
            tree = ast.parse(kaynak_kodu)
        except SyntaxError as e:
            self._ekle(
                "SyntaxError",
                "🔴 KESİN",
                e.lineno,
                f"Syntax hatası: {e.msg}",
                False
            )
            return self.bulgular

        self.tree = tree

        # Dosya seviyesindeki tanımlar
        tanimli_isimler = self._tanimli_isimler(tree)

        self._gez(tree, tanimli_isimler)

        return self.bulgular

    def _ekle(
        self,
        tur,
        seviye,
        satir,
        mesaj,
        otomatik=False,
        duzeltme=None
    ):
        self.bulgular.append({
            "tur": tur,
            "seviye": seviye,
            "satir": satir,
            "mesaj": mesaj,
            "otomatik_duzeltilebilir": otomatik,
            "duzeltme": duzeltme,
        })

    def _tanimli_isimler(self, tree):
        isimler = set()

        # Built-in isimler ve yerleşik Python hata sınıfları
        isimler.update(dir(__builtins__))
        isimler.update({
            "Exception", "BaseException",
            "ArithmeticError", "ZeroDivisionError",
            "AssertionError", "AttributeError",
            "EOFError", "FloatingPointError",
            "ImportError", "ModuleNotFoundError",
            "IndexError", "KeyError", "NameError",
            "TypeError", "ValueError", "RuntimeError",
            "FileNotFoundError", "OSError"
        })

        for node in ast.walk(tree):
            # Fonksiyon / sınıf isimleri
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                isimler.add(node.name)

                # Fonksiyon parametreleri
                for arg in node.args.args:
                    isimler.add(arg.arg)
                for arg in node.args.kwonlyargs:
                    isimler.add(arg.arg)
                if node.args.vararg:
                    isimler.add(node.args.vararg.arg)
                if node.args.kwarg:
                    isimler.add(node.args.kwarg.arg)

            # Importlar
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    isimler.add(alias.asname or alias.name.split(".")[0])

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*":
                        isimler.add(alias.asname or alias.name)

            # Atamalar
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                isimler.add(node.id)

            # with ... as
            elif isinstance(node, ast.withitem):
                if isinstance(node.optional_vars, ast.Name):
                    isimler.add(node.optional_vars.id)

            # except ... as
            elif isinstance(node, ast.ExceptHandler):
                if node.name:
                    isimler.add(node.name)

        return isimler

    def _gez(self, node, tanimli_isimler):
        for child in ast.iter_child_nodes(node):
            self._kontrol(child, tanimli_isimler)
            self._gez(child, tanimli_isimler)

    def _kontrol(self, node, tanimli_isimler):

        # ---------------------------------------------------------
        # 1 — Bare except
        # ---------------------------------------------------------
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                self._ekle(
                    "BareExcept",
                    "🟠 RİSK",
                    node.lineno,
                    "except: çok geniş bir hata yakalama alanı oluşturuyor.",
                    True,
                    "except Exception:"
                )

        # ---------------------------------------------------------
        # 2 — == True / == False
        # ---------------------------------------------------------
        if isinstance(node, ast.Compare):
            for op, comparator in zip(
                node.ops,
                node.comparators
            ):
                if (
                    isinstance(op, ast.Eq)
                    and isinstance(comparator, ast.Constant)
                    and isinstance(comparator.value, bool)
                ):
                    self._ekle(
                        "BooleanComparison",
                        "🟡 ÖNERİ",
                        node.lineno,
                        "Boolean değer doğrudan kontrol edilebilir.",
                        True,
                        "Boolean karşılaştırması sadeleştirilebilir."
                    )

        # ---------------------------------------------------------
        # 3 — is ile sayı/string karşılaştırması
        # ---------------------------------------------------------
        if isinstance(node, ast.Compare):
            for op, comparator in zip(
                node.ops,
                node.comparators
            ):
                if (
                    isinstance(op, ast.Is)
                    and isinstance(comparator, ast.Constant)
                    and isinstance(
                        comparator.value,
                        (int, float, str)
                    )
                ):
                    self._ekle(
                        "IsComparison",
                        "🔴 KESİN",
                        node.lineno,
                        "is operatörü değer karşılaştırmak için kullanılmamalı.",
                        True,
                        "== kullanılmalı."
                    )

        # ---------------------------------------------------------
        # 4 — Mutable default argument
        # ---------------------------------------------------------
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            defaults = list(node.args.defaults)

            for default in defaults:
                if isinstance(
                    default,
                    (ast.List, ast.Dict, ast.Set)
                ):
                    self._ekle(
                        "MutableDefaultArgument",
                        "🔴 KESİN",
                        node.lineno,
                        "Fonksiyon mutable default değer kullanıyor.",
                        True,
                        "Default değer None yapılıp fonksiyon içinde oluşturulmalı."
                    )

        # ---------------------------------------------------------
        # 5 — eval / exec
        # ---------------------------------------------------------
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in {"eval", "exec"}:
                    self._ekle(
                        "DangerousBuiltin",
                        "🟠 RİSK",
                        node.lineno,
                        f"{node.func.id}() kullanımı güvenlik açısından incelenmeli.",
                        False
                    )

        # ---------------------------------------------------------
        # 6 — Built-in isim gölgeleme
        # ---------------------------------------------------------
        if isinstance(node, ast.Assign):
            for hedef in node.targets:
                if isinstance(hedef, ast.Name):
                    if hedef.id in self.BUILTIN_SHADOWS:
                        self._ekle(
                            "BuiltinShadowing",
                            "🟠 RİSK",
                            node.lineno,
                            f"'{hedef.id}' Python built-in ismini gölgeliyor.",
                            False
                        )

        # ---------------------------------------------------------
        # 7 — Fonksiyon parametresi built-in gölgeliyor
        # ---------------------------------------------------------
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            for arg in node.args.args:
                if arg.arg in self.BUILTIN_SHADOWS:
                    self._ekle(
                        "BuiltinParameterShadowing",
                        "🟠 RİSK",
                        arg.lineno,
                        f"'{arg.arg}' built-in isimle aynı.",
                        False
                    )

        # ---------------------------------------------------------
        # 8 — while True + break yok
        # ---------------------------------------------------------
        if isinstance(node, ast.While):
            if (
                isinstance(node.test, ast.Constant)
                and node.test.value is True
                and not self._icinde_break_var(node.body)
            ):
                self._ekle(
                    "InfiniteLoop",
                    "🔴 KESİN",
                    node.lineno,
                    "while True içinde break bulunamadı.",
                    False
                )

        # ---------------------------------------------------------
        # 9 — Fonksiyon içindeki ulaşılmaz kod
        # ---------------------------------------------------------
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            self._kontrol_ulasılmaz(node.body)

        # ---------------------------------------------------------
        # 10 — Sıfıra bölme
        # ---------------------------------------------------------
        if isinstance(node, ast.BinOp):
            if isinstance(
                node.op,
                (ast.Div, ast.FloorDiv, ast.Mod)
            ):
                if (
                    isinstance(node.right, ast.Constant)
                    and node.right.value == 0
                ):
                    self._ekle(
                        "ZeroDivision",
                        "🔴 KESİN",
                        node.lineno,
                        "Sıfıra bölme tespit edildi.",
                        True,
                        "Bölen sıfırdan farklı olacak şekilde kontrol edilmeli."
                    )

        # ---------------------------------------------------------
        # 11/12 — Liste / sözlük erişimini bağlama göre ayır
        # ---------------------------------------------------------
        if isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                isim = node.value.id
                indeks = node.slice

                # İsimden açıkça liste olduğu anlaşılan değişkenler
                liste_adlari = {
                    "liste", "listeler", "elemanlar",
                    "items", "numbers", "sayilar"
                }

                # İsimden açıkça sözlük olduğu anlaşılan değişkenler
                sozluk_adlari = {
                    "veri", "sozluk", "dict",
                    "dictionary", "config", "ayarlar"
                }

                if (
                    isim.lower() in liste_adlari
                    and isinstance(indeks, ast.Constant)
                    and isinstance(indeks.value, int)
                    and indeks.value >= 0
                ):
                    self._ekle(
                        "PossibleIndexError",
                        "🟡 ÖNERİ",
                        node.lineno,
                        f"'{isim}' liste erişiminde sabit indeks kullanılıyor; indeks sınırı garanti değil.",
                        False
                    )

                elif (
                    isim.lower() in sozluk_adlari
                    and isinstance(indeks, ast.Constant)
                    and isinstance(indeks.value, str)
                ):
                    self._ekle(
                        "PossibleKeyError",
                        "🟡 ÖNERİ",
                        node.lineno,
                        f"'{isim}' sözlüğünde doğrudan anahtar erişimi var; anahtar bulunmayabilir.",
                        False
                    )

        # ---------------------------------------------------------
        # 12 — Basit tanımsız isim kontrolü
        # ---------------------------------------------------------
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Load):
                bilinen = set(dir(__builtins__))

                # Yaygın Python özel isimleri
                bilinen.update({
                    "True", "False", "None",
                    "print", "len", "range",
                    "str", "int", "float",
                    "list", "dict", "set", "tuple",
                    "open", "enumerate", "zip",
                    "sum", "min", "max", "abs"
                })

                if node.id not in tanimli_isimler and node.id not in bilinen:
                    self._ekle(
                        "UndefinedName",
                        "🔴 KESİN",
                        node.lineno,
                        f"'{node.id}' adı kullanıldığı noktada tanımlı görünmüyor.",
                        False
                    )

        # ---------------------------------------------------------
        # 13 — None ile açıkça riskli işlem
        # ---------------------------------------------------------
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Constant):
                if node.value.value is None:
                    self._ekle(
                        "NoneAttribute",
                        "🔴 KESİN",
                        node.lineno,
                        "None üzerinde attribute erişimi yapılıyor.",
                        False
                    )

        # ---------------------------------------------------------
        # 14 — Gereksiz else sonrası return
        # ---------------------------------------------------------
        if isinstance(node, ast.If):
            if node.body:
                son = node.body[-1]

                if isinstance(
                    son,
                    (ast.Return, ast.Raise)
                ):
                    if node.orelse:
                        self._ekle(
                            "UnnecessaryElse",
                            "🟡 ÖNERİ",
                            node.lineno,
                            "if bloğu return/raise ile bitiyor; else gereksiz olabilir.",
                            False
                        )

        # ---------------------------------------------------------
        # 15 — Derin iç içe if
        # ---------------------------------------------------------
        if isinstance(node, ast.If):
            derinlik = self._if_derinligi(node)

            if derinlik >= 4:
                self._ekle(
                    "DeepNesting",
                    "🟡 ÖNERİ",
                    node.lineno,
                    f"Koşul yapısı {derinlik} seviye iç içe.",
                    False
                )

    def _kontrol_ulasılmaz(self, body):
        terminal = False

        for stmt in body:
            if terminal:
                self._ekle(
                    "UnreachableCode",
                    "🟠 RİSK",
                    getattr(stmt, "lineno", None),
                    "Bu kod bloğuna normal akışta ulaşılamıyor.",
                    False
                )

            if isinstance(
                stmt,
                (ast.Return, ast.Raise)
            ):
                terminal = True

    def _icinde_break_var(self, body):
        for node in ast.walk(
            ast.Module(
                body=body,
                type_ignores=[]
            )
        ):
            if isinstance(node, ast.Break):
                return True

        return False

    def _if_derinligi(self, node):
        maksimum = 1

        for child in node.body:
            if isinstance(child, ast.If):
                maksimum = max(
                    maksimum,
                    1 + self._if_derinligi(child)
                )

        return maksimum


def dosya_analiz_et(dosya):
    dosya = Path(dosya)

    kaynak = dosya.read_text(
        encoding="utf-8"
    )

    motor = EagleKodAnalizMotoru()

    bulgular = motor.analiz_et(
        kaynak
    )

    print("\n🦅 EAGLE KOD ANALİZ")
    print("=" * 50)
    print(f"Dosya: {dosya}")
    print(f"Bulgu sayısı: {len(bulgular)}")
    print()

    if not bulgular:
        print("🟢 Kod temiz görünüyor.")
        return

    for i, bulgu in enumerate(
        bulgular,
        1
    ):
        print(
            f"{i}. "
            f"{bulgu['seviye']} "
            f"{bulgu['tur']}"
        )

        print(
            f"   Satır: "
            f"{bulgu['satir']}"
        )

        print(
            f"   {bulgu['mesaj']}"
        )

        if bulgu.get(
            "otomatik_duzeltilebilir"
        ):
            print(
                "   🛠️ Otomatik düzeltme adayı: EVET"
            )

        if bulgu.get("duzeltme"):
            print(
                f"   → {bulgu['duzeltme']}"
            )

        print()


if __name__ == "__main__":
    dosya_analiz_et(
        "eagle_kod_analiz_deneme.py"
    )
