import re

class EagleGenelUygulamaUretici:
    """Genel uygulama üreticisi."""

    def uret(self, plan):
        if not plan:
            return None

        konu = str(plan.get("konu") or "genel uygulama").strip()
        paket = self._paket_adi(konu)
        bilesenler = set(plan.get("bilesenler") or ())

        dosyalar = {
            "app.py": self._app(paket, plan),
            f"src/{paket}/__init__.py": "",
        }

        if "model" in bilesenler:
            dosyalar[f"src/{paket}/model.py"] = self._model()

        if "service" in bilesenler:
            dosyalar[f"src/{paket}/service.py"] = self._service()

        if "database" in bilesenler:
            dosyalar[f"src/{paket}/database.py"] = self._database()

        if "tests" in bilesenler:
            dosyalar["tests/test_core.py"] = self._tests(paket)

        dosyalar["README.md"] = self._readme(konu)
        dosyalar["requirements.txt"] = self._requirements(plan)

        return {
            "ok": True,
            "dosyalar": dosyalar,
            "ana_dosya": "app.py",
            "proje_adi": konu,
            "cikti_turu": plan.get("cikti_turu", "proje"),
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
        return (
            "from flask import Flask, jsonify\n"
            f"from src.{paket}.database import Database\n"
            f"from src.{paket}.service import Service\n\n"
            "app = Flask(__name__)\n"
            "database = Database()\n"
            "service = Service(database)\n\n"
            "@app.get('/')\n"
            "def index():\n"
            "    return jsonify({'ok': True, 'uygulama': 'hazir'})\n\n"
            "@app.get('/api/durum')\n"
            "def durum():\n"
            "    return jsonify({'ok': True})\n\n"
            "if __name__ == '__main__':\n"
            "    app.run(host='0.0.0.0', port=5000)\n"
        )

    @staticmethod
    def _model():
        return (
            "class Kayit:\n"
            "    def __init__(self, veri):\n"
            "        self.veri = veri\n"
        )

    @staticmethod
    def _service():
        return (
            "class Service:\n"
            "    def __init__(self, database):\n"
            "        self.database = database\n\n"
            "    def ekle(self, veri):\n"
            "        return self.database.ekle(veri)\n\n"
            "    def listele(self):\n"
            "        return self.database.listele()\n\n"
            "    def getir(self, kayit_id):\n"
            "        return self.database.getir(kayit_id)\n"
        )

    @staticmethod
    def _database():
        return (
            "import sqlite3\n\n"
            "class Database:\n"
            "    def __init__(self, path='app.db'):\n"
            "        self.path = path\n"
            "        self.initialize()\n\n"
            "    def initialize(self):\n"
            "        with sqlite3.connect(self.path) as conn:\n"
            "            conn.execute(\n"
            "                'CREATE TABLE IF NOT EXISTS kayitlar ('\n"
            "                'id INTEGER PRIMARY KEY AUTOINCREMENT, '\n"
            "                'veri TEXT NOT NULL)'\n"
            "            )\n\n"
            "    def ekle(self, veri):\n"
            "        with sqlite3.connect(self.path) as conn:\n"
            "            cur = conn.execute(\n"
            "                'INSERT INTO kayitlar (veri) VALUES (?)',\n"
            "                (str(veri),)\n"
            "            )\n"
            "            return cur.lastrowid\n\n"
            "    def listele(self):\n"
            "        with sqlite3.connect(self.path) as conn:\n"
            "            rows = conn.execute(\n"
            "                'SELECT id, veri FROM kayitlar ORDER BY id'\n"
            "            ).fetchall()\n"
            "        return [{'id': row[0], 'veri': row[1]} for row in rows]\n\n"
            "    def getir(self, kayit_id):\n"
            "        with sqlite3.connect(self.path) as conn:\n"
            "            row = conn.execute(\n"
            "                'SELECT id, veri FROM kayitlar WHERE id = ?',\n"
            "                (kayit_id,)\n"
            "            ).fetchone()\n"
            "        if row is None:\n"
            "            return None\n"
            "        return {'id': row[0], 'veri': row[1]}\n"
        )

    @staticmethod
    def _tests(paket):
        return (
            "def test_temel():\n"
            "    assert True\n"
        )

    @staticmethod
    def _requirements(plan):
        return "Flask>=3.0,<4\n"

    @staticmethod
    def _readme(konu):
        return (
            f"# {konu}\n\n"
            "EagleAI tarafından oluşturulan Python uygulama projesi.\n"
        )
