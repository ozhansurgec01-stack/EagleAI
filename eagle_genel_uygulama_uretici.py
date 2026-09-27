import ast
import os
import subprocess
import sys
import tempfile
import re

class EagleGenelUygulamaUretici:
    """Genel uygulama üreticisi."""

    def uret(self, plan):
        if not plan:
            return None

        konu = str(plan.get("konu") or "genel uygulama").strip()
        paket = self._paket_adi(konu)
        bilesenler = set(plan.get("bilesenler") or ())

        # Planner tarafından çıkarılan gereksinimleri üretim katmanına aktar.
        # Alanlar bilinmiyorsa mevcut güvenli Kayit/veri fallback'i korunur.
        gereksinimler = plan.get("gereksinimler") or {}
        varliklar = plan.get("varliklar") or gereksinimler.get("varliklar") or ["kayit"]
        alanlar = plan.get("alanlar") or gereksinimler.get("alanlar") or {
            "kayit": ["id", "veri"]
        }
        islemler = plan.get("islemler") or gereksinimler.get("islemler") or [
            "ekle", "listele", "detay", "guncelle", "sil"
        ]

        plan = dict(plan)
        plan["varliklar"] = list(varliklar)
        plan["alanlar"] = dict(alanlar)
        plan["islemler"] = list(islemler)

        dosyalar = {
            "app.py": self._app(paket, plan),
            f"src/{paket}/__init__.py": "",
        }

        if "model" in bilesenler:
            dosyalar[f"src/{paket}/model.py"] = self._model(plan)

        if "service" in bilesenler:
            dosyalar[f"src/{paket}/service.py"] = self._service(plan)

        if "database" in bilesenler:
            dosyalar[f"src/{paket}/database.py"] = self._database(plan)

        if "api" in bilesenler:
            dosyalar[f"src/{paket}/api.py"] = self._api(paket, plan)

        if "source" in bilesenler:
            dosyalar[f"src/{paket}/source.py"] = self._source()

        if "ui" in bilesenler:
            dosyalar["templates/index.html"] = self._index_html(konu, plan)

        if "detail" in bilesenler:
            dosyalar["templates/detail.html"] = self._detail_html(konu)

        if "tests" in bilesenler:
            dosyalar["tests/test_core.py"] = self._tests(paket, plan)

        dosyalar["README.md"] = self._readme(konu)
        dosyalar["requirements.txt"] = self._requirements(plan)

        sonuc = {
            "ok": True,
            "dosyalar": dosyalar,
            "ana_dosya": "app.py",
            "proje_adi": konu,
            "cikti_turu": plan.get("cikti_turu", "proje"),
        }

        dogrulama = self._dogrula(dosyalar, plan)
        sonuc.update(dogrulama)
        sonuc["ok"] = bool(dogrulama["validation_ok"])

        return sonuc

    @staticmethod
    def _dogrula(dosyalar, plan=None):
        """
        Üretilen projeyi geçici bir dizinde gerçek dosyalarla doğrular.

        Ağ bağlantısı kurmaz. Harici kaynak dosyaları yalnızca syntax/import
        seviyesinde doğrulanır.
        """
        syntax_hatalari = []
        import_hatalari = []
        fonksiyon_hatalari = []

        with tempfile.TemporaryDirectory(prefix="eagle_gen_") as tmp:
            root = os.path.abspath(tmp)

            for yol, icerik in dosyalar.items():
                hedef = os.path.join(root, yol)
                os.makedirs(os.path.dirname(hedef), exist_ok=True)

                with open(hedef, "w", encoding="utf-8") as f:
                    f.write(str(icerik))

            python_dosyalar = [
                os.path.join(root, yol)
                for yol in dosyalar
                if yol.endswith(".py")
            ]

            for dosya in python_dosyalar:
                try:
                    with open(dosya, "r", encoding="utf-8") as f:
                        ast.parse(f.read(), filename=dosya)
                except (OSError, SyntaxError) as exc:
                    syntax_hatalari.append(f"{os.path.relpath(dosya, root)}: {exc}")

            syntax_ok = not syntax_hatalari

            if syntax_ok:
                env = os.environ.copy()
                env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")

                import_kod = (
                    "import importlib; "
                    "m=importlib.import_module('app'); "
                    "assert hasattr(m, 'app')"
                )

                proc = subprocess.run(
                    [sys.executable, "-c", import_kod],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )

                if proc.returncode != 0:
                    import_hatalari.append(
                        (proc.stderr or proc.stdout or "app import başarısız").strip()
                    )

            import_ok = not import_hatalari

            functional_ok = False

            if syntax_ok and import_ok:
                varliklar = (plan or {}).get("varliklar") or ["kayit"]
                alanlar = (plan or {}).get("alanlar") or {
                    "kayit": ["id", "veri"]
                }
                ilk_varlik = str(varliklar[0])
                test_alanlari = [
                    str(x)
                    for x in alanlar.get(ilk_varlik, ["id", "veri"])
                    if str(x) != "id"
                ] or ["veri"]

                test_payload = {
                    alan: f"EagleAI test {alan}"
                    for alan in test_alanlari
                }
                guncel_payload = {
                    alan: f"EagleAI guncel {alan}"
                    for alan in test_alanlari
                }

                test_kod = f"""
from app import app

client = app.test_client()

r = client.get("/")
assert r.status_code == 200, f"/ -> {{r.status_code}}"

r = client.get("/api/durum")
assert r.status_code == 200, f"/api/durum -> {{r.status_code}}"
data = r.get_json()
assert data and data.get("ok") is True

r = client.get("/api/kayitlar")
assert r.status_code == 200, f"GET /api/kayitlar -> {{r.status_code}}"

payload = {test_payload!r}
guncel_payload = {guncel_payload!r}

r = client.post("/api/kayitlar", json=payload)
assert r.status_code == 201, f"POST /api/kayitlar -> {{r.status_code}}"
created = r.get_json()
assert created and created.get("ok") is True
kayit_id = created["id"]

r = client.get(f"/api/kayitlar/{{kayit_id}}")
assert r.status_code == 200, f"GET detay -> {{r.status_code}}"
data = r.get_json()
kayit = data.get("kayit") if isinstance(data, dict) else None
assert isinstance(kayit, dict), "GET detay kayit nesnesi yok"
assert all(kayit.get(alan) == deger for alan, deger in payload.items()), (
    f"GET detay payload uyuşmuyor: {{kayit}}"
)

r = client.put(f"/api/kayitlar/{{kayit_id}}", json=guncel_payload)
assert r.status_code == 200, f"PUT -> {{r.status_code}}"

r = client.get(f"/api/kayitlar/{{kayit_id}}")
assert r.status_code == 200, f"GET güncel -> {{r.status_code}}"
data = r.get_json()
kayit = data.get("kayit") if isinstance(data, dict) else None
assert isinstance(kayit, dict), "GET güncel kayit nesnesi yok"
assert all(kayit.get(alan) == deger for alan, deger in guncel_payload.items()), (
    f"GET güncel payload uyuşmuyor: {{kayit}}"
)

r = client.delete(f"/api/kayitlar/{{kayit_id}}")
assert r.status_code == 200, f"DELETE -> {{r.status_code}}"

r = client.get(f"/api/kayitlar/{{kayit_id}}")
assert r.status_code == 404, f"silinen kayıt 404 -> {{r.status_code}}"

r = client.get("/api/kayitlar/999999999")
assert r.status_code == 404, f"404 testi -> {{r.status_code}}"

r = client.get(f"/detail/{{kayit_id}}")
assert r.status_code in (200, 404), f"/detail -> {{r.status_code}}"

import json
import os
from threading import Thread
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from werkzeug.serving import make_server

server = make_server("127.0.0.1", 0, app)
port = server.server_port
thread = Thread(target=server.serve_forever, daemon=True)
thread.start()
base = f"http://127.0.0.1:{{port}}"

def http_request(path, method="GET", payload=None):
    data = None
    headers = {{}}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = Request(base + path, data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=5) as response:
            return response.status
    except HTTPError as exc:
        return exc.code

http_passed = False
try:
    assert http_request("/") == 200
    assert http_request("/api/durum") == 200
    assert http_request("/api/kayitlar") == 200
    assert http_request("/api/kayitlar/999999999") == 404
    http_passed = True
finally:
    server.shutdown()
    thread.join(timeout=5)

if http_passed:
    print("__EAGLE_HTTP_OK__")

import importlib.util

test_path = os.path.join("tests", "test_core.py")
spec = importlib.util.spec_from_file_location("generated_test_core", test_path)
generated_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generated_tests)

for test_name in dir(generated_tests):
    if test_name.startswith("test_"):
        test_func = getattr(generated_tests, test_name)
        if callable(test_func):
            test_func()

print("__EAGLE_GENERATED_TESTS_OK__")

"""

                proc = subprocess.run(
                    [sys.executable, "-c", test_kod],
                    cwd=root,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )

                stdout = proc.stdout or ""
                stderr = proc.stderr or ""

                functional_ok = (
                    proc.returncode == 0
                    and "__EAGLE_GENERATED_TESTS_OK__" in stdout
                )
                if not functional_ok:
                    fonksiyon_hatalari.append(
                        (stderr or stdout or "fonksiyon testi başarısız").strip()
                    )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""

        http_ok = (
            proc.returncode == 0
            and "__EAGLE_HTTP_OK__" in stdout
        )
        http_hatalari = [] if http_ok else [
            (stderr or stdout or "HTTP testi başarısız").strip()
        ]

        validation_ok = (
            syntax_ok
            and import_ok
            and functional_ok
            and http_ok
        )

        return {
            "validation_ok": validation_ok,
            "syntax_ok": syntax_ok,
            "syntax_hatalari": syntax_hatalari,
            "import_ok": import_ok,
            "import_hatalari": import_hatalari,
            "functional_ok": functional_ok,
            "fonksiyon_hatalari": fonksiyon_hatalari,
            "http_ok": http_ok,
            "http_hatalari": http_hatalari,
        }

    @staticmethod
    def _paket_adi(konu):
        cevir = str.maketrans({
            "ç": "c", "ğ": "g", "ı": "i", "ö": "o",
            "ş": "s", "ü": "u",
            "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O",
            "Ş": "S", "Ü": "U",
        })
        konu = str(konu).translate(cevir)
        konu = re.sub(r"[^a-zA-Z0-9_]+", "_", konu.lower()).strip("_")
        konu = re.sub(r"_+", "_", konu)
        return konu or "genel_uygulama"

    @staticmethod
    def _app(paket, plan):
        lines = [
            "from flask import Flask, render_template",
            f"from src.{paket}.api import api",
            "",
            "app = Flask(__name__)",
            "app.register_blueprint(api)",
            "",
            "@app.get('/')",
            "def index():",
            "    return render_template('index.html')",
            "",
            "@app.get('/detail/<int:kayit_id>')",
            "def detail(kayit_id):",
            "    return render_template('detail.html', kayit_id=kayit_id)",
            "",
            "if __name__ == '__main__':",
            "    app.run(host='0.0.0.0', port=5000)",
        ]
        return "\n".join(lines)

    @staticmethod
    def _api(paket, plan):
        varliklar = plan.get("varliklar") or ["kayit"]
        alanlar = plan.get("alanlar") or {"kayit": ["id", "veri"]}
        ilk_varlik = str(varliklar[0])

        lines = [
            "from flask import Blueprint, jsonify, request",
            f"from src.{paket}.service import Service",
            f"from src.{paket}.database import Database",
            "",
            "api = Blueprint('api', __name__, url_prefix='/api')",
            "database = Database()",
            "service = Service(database)",
            f"VARLIKLAR = {list(varliklar)!r}",
            f"ALANLAR = {dict(alanlar)!r}",
            f"ILK_VARLIK = {ilk_varlik!r}",
            "",
            "@api.get('/durum')",
            "def durum():",
            "    return jsonify({'ok': True, 'varliklar': VARLIKLAR})",
            "",
            "@api.get('/kayitlar')",
            "def kayitlar():",
            "    return jsonify({'ok': True, 'kayitlar': service.listele(ILK_VARLIK)})",
            "",
            "@api.post('/kayitlar')",
            "def kayit_ekle():",
            "    veri = request.get_json(silent=True) or {}",
            "    if not isinstance(veri, dict):",
            "        return jsonify({'ok': False, 'error': 'JSON nesnesi gerekli'}), 400",
            "    kayit_id = service.ekle(ILK_VARLIK, veri)",
            "    return jsonify({'ok': True, 'id': kayit_id, 'varlik': ILK_VARLIK}), 201",
            "",
            "@api.get('/kayitlar/<int:kayit_id>')",
            "def kayit_getir(kayit_id):",
            "    kayit = service.getir(ILK_VARLIK, kayit_id)",
            "    if kayit is None:",
            "        return jsonify({'ok': False, 'error': 'Kayıt bulunamadı'}), 404",
            "    return jsonify({'ok': True, 'kayit': kayit})",
            "",
            "@api.put('/kayitlar/<int:kayit_id>')",
            "def kayit_guncelle(kayit_id):",
            "    veri = request.get_json(silent=True) or {}",
            "    if not isinstance(veri, dict):",
            "        return jsonify({'ok': False, 'error': 'JSON nesnesi gerekli'}), 400",
            "    if not service.guncelle(ILK_VARLIK, kayit_id, veri):",
            "        return jsonify({'ok': False, 'error': 'Kayıt bulunamadı'}), 404",
            "    return jsonify({'ok': True, 'id': kayit_id})",
            "",
            "@api.delete('/kayitlar/<int:kayit_id>')",
            "def kayit_sil(kayit_id):",
            "    if not service.sil(ILK_VARLIK, kayit_id):",
            "        return jsonify({'ok': False, 'error': 'Kayıt bulunamadı'}), 404",
            "    return jsonify({'ok': True, 'id': kayit_id})",
            "",
            "@api.get('/<varlik>')",
            "def varlik_listele(varlik):",
            "    if varlik not in VARLIKLAR:",
            "        return jsonify({'ok': False, 'error': 'Varlık bulunamadı'}), 404",
            "    return jsonify({'ok': True, 'varlik': varlik, 'kayitlar': service.listele(varlik)})",
            "",
            "@api.post('/<varlik>')",
            "def varlik_ekle(varlik):",
            "    if varlik not in VARLIKLAR:",
            "        return jsonify({'ok': False, 'error': 'Varlık bulunamadı'}), 404",
            "    veri = request.get_json(silent=True) or {}",
            "    if not isinstance(veri, dict):",
            "        return jsonify({'ok': False, 'error': 'JSON nesnesi gerekli'}), 400",
            "    kayit_id = service.ekle(varlik, veri)",
            "    return jsonify({'ok': True, 'id': kayit_id, 'varlik': varlik}), 201",
            "",
            "@api.get('/<varlik>/<int:kayit_id>')",
            "def varlik_getir(varlik, kayit_id):",
            "    if varlik not in VARLIKLAR:",
            "        return jsonify({'ok': False, 'error': 'Varlık bulunamadı'}), 404",
            "    kayit = service.getir(varlik, kayit_id)",
            "    if kayit is None:",
            "        return jsonify({'ok': False, 'error': 'Kayıt bulunamadı'}), 404",
            "    return jsonify({'ok': True, 'kayit': kayit})",
        ]
        return "\n".join(lines)

    @staticmethod
    def _model(plan):
        varliklar = plan.get("varliklar") or ["kayit"]
        alanlar = plan.get("alanlar") or {"kayit": ["id", "veri"]}

        lines = [
            "from dataclasses import dataclass",
            "from typing import Any, Dict",
            "",
            "@dataclass",
            "class Kayit:",
            "    id: int",
            "    varlik: str",
            "    veri: Dict[str, Any]",
            "",
            f"VARLIKLAR = {varliklar!r}",
            f"ALANLAR = {alanlar!r}",
            "",
        ]
        return "\n".join(lines)

    @staticmethod
    def _service(plan):
        return "\n".join([
            "class Service:",
            "    def __init__(self, database):",
            "        self.database = database",
            "",
            "    def ekle(self, varlik, veri):",
            "        return self.database.ekle(varlik, veri)",
            "",
            "    def listele(self, varlik=None):",
            "        return self.database.listele(varlik)",
            "",
            "    def getir(self, varlik, kayit_id):",
            "        return self.database.getir(varlik, kayit_id)",
            "",
            "    def guncelle(self, varlik, kayit_id, veri):",
            "        return self.database.guncelle(varlik, kayit_id, veri)",
            "",
            "    def sil(self, varlik, kayit_id):",
            "        return self.database.sil(varlik, kayit_id)",
        ])

    @staticmethod
    def _database(plan):
        lines = [
            "import json",
            "import sqlite3",
            "",
            "class Database:",
            "    def __init__(self, path='app.db'):",
            "        self.path = path",
            "        self.initialize()",
            "",
            "    def _connect(self):",
            "        conn = sqlite3.connect(self.path)",
            "        conn.row_factory = sqlite3.Row",
            "        return conn",
            "",
            "    def initialize(self):",
            "        with self._connect() as conn:",
            "            conn.execute(",
            "                'CREATE TABLE IF NOT EXISTS kayitlar ('",
            "                'id INTEGER PRIMARY KEY AUTOINCREMENT, '",
            "                'varlik TEXT NOT NULL, '",
            "                'veri TEXT NOT NULL)'",
            "            )",
            "            conn.execute(",
            "                'CREATE INDEX IF NOT EXISTS idx_kayitlar_varlik '",
            "                'ON kayitlar(varlik)'",
            "            )",
            "",
            "    def ekle(self, varlik, veri):",
            "        payload = dict(veri or {})",
            "        with self._connect() as conn:",
            "            cur = conn.execute(",
            "                'INSERT INTO kayitlar (varlik, veri) VALUES (?, ?)',",
            "                (str(varlik), json.dumps(payload, ensure_ascii=False))",
            "            )",
            "            return cur.lastrowid",
            "",
            "    def listele(self, varlik=None):",
            "        with self._connect() as conn:",
            "            if varlik:",
            "                rows = conn.execute(",
            "                    'SELECT id, varlik, veri FROM kayitlar '",
            "                    'WHERE varlik = ? ORDER BY id',",
            "                    (str(varlik),)",
            "                ).fetchall()",
            "            else:",
            "                rows = conn.execute(",
            "                    'SELECT id, varlik, veri FROM kayitlar ORDER BY id'",
            "                ).fetchall()",
            "        return [self._row(row) for row in rows]",
            "",
            "    def getir(self, varlik, kayit_id):",
            "        with self._connect() as conn:",
            "            row = conn.execute(",
            "                'SELECT id, varlik, veri FROM kayitlar '",
            "                'WHERE varlik = ? AND id = ?',",
            "                (str(varlik), kayit_id)",
            "            ).fetchone()",
            "        return self._row(row) if row else None",
            "",
            "    def guncelle(self, varlik, kayit_id, veri):",
            "        payload = dict(veri or {})",
            "        with self._connect() as conn:",
            "            cur = conn.execute(",
            "                'UPDATE kayitlar SET veri = ? '",
            "                'WHERE varlik = ? AND id = ?',",
            "                (json.dumps(payload, ensure_ascii=False), str(varlik), kayit_id)",
            "            )",
            "        return cur.rowcount > 0",
            "",
            "    def sil(self, varlik, kayit_id):",
            "        with self._connect() as conn:",
            "            cur = conn.execute(",
            "                'DELETE FROM kayitlar WHERE varlik = ? AND id = ?',",
            "                (str(varlik), kayit_id)",
            "            )",
            "        return cur.rowcount > 0",
            "",
            "    @staticmethod",
            "    def _row(row):",
            "        if row is None:",
            "            return None",
            "        try:",
            "            veri = json.loads(row['veri'])",
            "        except (TypeError, ValueError):",
            "            veri = {'veri': row['veri']}",
            "        if not isinstance(veri, dict):",
            "            veri = {'veri': veri}",
            "        return {",
            "            'id': row['id'],",
            "            'varlik': row['varlik'],",
            "            **veri,",
            "        }",
        ]
        return "\n".join(lines)

    @staticmethod
    def _source():
        lines = [
            "import requests",
            "",
            "def getir(url, params=None, timeout=10):",
            "    try:",
            "        response = requests.get(url, params=params, timeout=timeout)",
            "        response.raise_for_status()",
            "        return response.json()",
            "    except requests.RequestException as exc:",
            "        return {'ok': False, 'error': str(exc)}",
        ]
        return "\n".join(lines)

    @staticmethod
    def _index_html(konu, plan=None):
        baslik = str(konu or "Genel Uygulama")
        plan = plan or {}
        varliklar = plan.get("varliklar") or ["kayit"]
        alanlar = plan.get("alanlar") or {"kayit": ["id", "veri"]}
        ilk_varlik = str(varliklar[0])
        alan_listesi = [
            str(x) for x in alanlar.get(ilk_varlik, ["id", "veri"])
            if str(x) != "id"
        ] or ["veri"]

        lines = [
            "<!doctype html>",
            "<html lang='tr'>",
            "<head>",
            "  <meta charset='utf-8'>",
            "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
            f"  <title>{baslik}</title>",
            "  <style>",
            "    * { box-sizing: border-box; }",
            "    body {",
            "      margin: 0;",
            "      padding: 24px 16px 40px;",
            "      font-family: Arial, sans-serif;",
            "      background: #f6f8fb;",
            "      color: #20242a;",
            "    }",
            "    .container {",
            "      width: min(100%, 760px);",
            "      margin: 0 auto;",
            "    }",
            "    h1 {",
            "      margin: 0 0 20px;",
            "      font-size: 28px;",
            "      line-height: 1.2;",
            "      font-weight: 700;",
            "      text-align: center;",
            "    }",
            "    .form-card {",
            "      background: #ffffff;",
            "      border-radius: 18px;",
            "      padding: 18px;",
            "      margin-bottom: 22px;",
            "      box-shadow: 0 4px 16px rgba(0,0,0,0.07);",
            "    }",
            "    #alanlar {",
            "      display: grid;",
            "      gap: 10px;",
            "    }",
            "    input {",
            "      width: 100%;",
            "      padding: 14px 15px;",
            "      border: 1px solid #d9dee7;",
            "      border-radius: 12px;",
            "      background: #fafbfc;",
            "      color: #20242a;",
            "      font-size: 16px;",
            "      outline: none;",
            "    }",
            "    input:focus {",
            "      border-color: #5b7cfa;",
            "      background: #ffffff;",
            "    }",
            "    button {",
            "      width: 100%;",
            "      margin-top: 12px;",
            "      padding: 14px 18px;",
            "      border: 0;",
            "      border-radius: 12px;",
            "      background: #5b5bea;",
            "      color: #ffffff;",
            "      font-size: 16px;",
            "      font-weight: 700;",
            "      cursor: pointer;",
            "    }",
            "    button:active {",
            "      transform: scale(0.99);",
            "    }",
            "    #liste {",
            "      display: grid;",
            "      gap: 10px;",
            "      padding: 0;",
            "      margin: 0;",
            "      list-style: none;",
            "    }",
            "    #liste li {",
            "      padding: 16px;",
            "      border-radius: 15px;",
            "      font-size: 16px;",
            "      line-height: 1.5;",
            "      overflow-wrap: anywhere;",
            "      box-shadow: 0 3px 12px rgba(0,0,0,0.05);",
            "    }",
            "    #liste li:nth-child(5n+1) { background: #eef6ff; }",
            "    #liste li:nth-child(5n+2) { background: #f5f0ff; }",
            "    #liste li:nth-child(5n+3) { background: #eefaf4; }",
            "    #liste li:nth-child(5n+4) { background: #fff7eb; }",
            "    #liste li:nth-child(5n+5) { background: #fff0f3; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <div class='container'>",
            f"    <h1>{baslik}</h1>",
            "    <div class='form-card'>",
            "      <form id='form'>",
            "        <div id='alanlar'></div>",
            "        <button type='submit'>Ekle</button>",
            "      </form>",
            "    </div>",
            "    <ul id='liste'></ul>",
            "  </div>",
            "  <script>",
            f"    const alanlar = {alan_listesi!r};",
            "    const form = document.getElementById('form');",
            "    const alanKutusu = document.getElementById('alanlar');",
            "    const liste = document.getElementById('liste');",
            "",
            "    for (const alan of alanlar) {",
            "      const input = document.createElement('input');",
            "      input.id = alan;",
            "      input.name = alan;",
            "      input.placeholder = alan;",
            "      input.required = true;",
            "      alanKutusu.appendChild(input);",
            "    }",
            "",
            "    async function yukle() {",
            "      const r = await fetch('/api/kayitlar');",
            "      const data = await r.json();",
            "      liste.innerHTML = '';",
            "      for (const x of (data.kayitlar || [])) {",
            "        const li = document.createElement('li');",
            "        const parcalar = alanlar.map(a => `${a}: ${x[a] ?? ''}`);",
            "        li.textContent = `${x.id}: ${parcalar.join(' | ')}`;",
            "        liste.appendChild(li);",
            "      }",
            "    }",
            "",
            "    form.addEventListener('submit', async (e) => {",
            "      e.preventDefault();",
            "      const veri = {};",
            "      for (const alan of alanlar) {",
            "        veri[alan] = document.getElementById(alan).value;",
            "      }",
            "      const r = await fetch('/api/kayitlar', {",
            "        method: 'POST',",
            "        headers: {'Content-Type': 'application/json'},",
            "        body: JSON.stringify(veri)",
            "      });",
            "      if (r.ok) { form.reset(); await yukle(); }",
            "    });",
            "",
            "    yukle();",
            "  </script>",
            "</body>",
            "</html>",
        ]
        return "\n".join(lines)

    @staticmethod
    def _detail_html(konu):
        baslik = str(konu or "Kayıt Detayı")
        lines = [
            "<!doctype html>",
            "<html lang='tr'>",
            "<head>",
            "  <meta charset='utf-8'>",
            "  <meta name='viewport' content='width=device-width, initial-scale=1'>",
            f"  <title>{baslik} - Detay</title>",
            "</head>",
            "<body>",
            f"  <h1>{baslik} - Detay</h1>",
            "  <pre id='detay'>Yükleniyor...</pre>",
            "  <script>",
            "    const id = location.pathname.split('/').pop();",
            "    fetch('/api/kayitlar/' + id)",
            "      .then(r => r.json())",
            "      .then(data => {",
            "        document.getElementById('detay').textContent =",
            "          JSON.stringify(data.kayit || data, null, 2);",
            "      })",
            "      .catch(() => {",
            "        document.getElementById('detay').textContent = 'Kayıt yüklenemedi.';",
            "      });",
            "  </script>",
            "</body>",
            "</html>",
        ]
        return "\n".join(lines)

    @staticmethod
    def _tests(paket, plan):
        varliklar = plan.get("varliklar") or ["kayit"]
        alanlar = plan.get("alanlar") or {"kayit": ["id", "veri"]}
        ilk_varlik = str(varliklar[0])

        test_alanlari = [
            str(x)
            for x in alanlar.get(ilk_varlik, ["id", "veri"])
            if str(x) != "id"
        ] or ["veri"]

        payload = {
            alan: f"EagleAI test {alan}"
            for alan in test_alanlari
        }
        guncel_payload = {
            alan: f"EagleAI guncel {alan}"
            for alan in test_alanlari
        }

        payload_repr = repr(payload)
        guncel_payload_repr = repr(guncel_payload)

        lines = [
            "from app import app",
            "",
            "def test_temel_uygulama():",
            "    client = app.test_client()",
            "    r = client.get('/')",
            "    assert r.status_code == 200",
            "    r = client.get('/api/durum')",
            "    assert r.status_code == 200",
            "    assert r.get_json()['ok'] is True",
            "",
            "def test_crud():",
            "    client = app.test_client()",
            f"    payload = {payload_repr}",
            f"    guncel_payload = {guncel_payload_repr}",
            "    r = client.post('/api/kayitlar', json=payload)",
            "    assert r.status_code == 201",
            "    kayit_id = r.get_json()['id']",
            "",
            "    r = client.get(f'/api/kayitlar/{kayit_id}')",
            "    assert r.status_code == 200",
            "    kayit = r.get_json()['kayit']",
            "    assert all(kayit.get(k) == v for k, v in payload.items())",
            "",
            "    r = client.put(f'/api/kayitlar/{kayit_id}', json=guncel_payload)",
            "    assert r.status_code == 200",
            "",
            "    r = client.get(f'/api/kayitlar/{kayit_id}')",
            "    assert r.status_code == 200",
            "    kayit = r.get_json()['kayit']",
            "    assert all(kayit.get(k) == v for k, v in guncel_payload.items())",
            "",
            "    r = client.delete(f'/api/kayitlar/{kayit_id}')",
            "    assert r.status_code == 200",
            "",
            "    r = client.get(f'/api/kayitlar/{kayit_id}')",
            "    assert r.status_code == 404",
        ]

        return "\n".join(lines)

    @staticmethod
    def _requirements(plan):
        satirlar = ["Flask>=3.0,<4"]
        if plan.get("dis_kaynak") or plan.get("harici_kaynak_gerekli"):
            satirlar.append("requests>=2.31,<3")
        return "\n".join(satirlar) + "\n"

    @staticmethod
    def _readme(konu):
        return (
            f"# {konu}\n\n"
            "EagleAI tarafından oluşturulan Python uygulama projesi.\n"
        )
