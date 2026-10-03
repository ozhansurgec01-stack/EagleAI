from datetime import date, datetime
from calendar import monthrange
from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import get_db, init_db

app = Flask(__name__)
init_db()


def durum_hesapla(bitis):
    if not bitis:
        return "Aktif"

    try:
        bitis_tarihi = datetime.strptime(bitis, "%Y-%m-%d").date()
    except ValueError:
        return "Aktif"

    kalan = (bitis_tarihi - date.today()).days

    if kalan < 0:
        return "Süresi Doldu"
    if kalan == 0:
        return "Bugün Bitiyor"
    if kalan <= 7:
        return "Yaklaşıyor"
    return "Aktif"


def ay_ekle(tarih_metni, ay):
    tarih = datetime.strptime(tarih_metni, "%Y-%m-%d").date()

    toplam_ay = tarih.month - 1 + ay
    yil = tarih.year + toplam_ay // 12
    ay_no = toplam_ay % 12 + 1
    gun = min(tarih.day, monthrange(yil, ay_no)[1])

    return date(yil, ay_no, gun).isoformat()


@app.route("/")
def dashboard():
    db = get_db()

    arama = request.args.get("arama", "").strip()

    if arama:
        pattern = f"%{arama}%"
        uyeler = db.execute("""
            SELECT *
            FROM uyeler
            WHERE ad LIKE ?
               OR soyad LIKE ?
               OR telefon LIKE ?
            ORDER BY id DESC
        """, (pattern, pattern, pattern)).fetchall()
    else:
        uyeler = db.execute("""
            SELECT *
            FROM uyeler
            ORDER BY id DESC
        """).fetchall()

    uyeler = [
        dict(uye, durum=durum_hesapla(uye["bitis"]))
        for uye in uyeler
    ]

    toplam = len(uyeler)
    aktif = sum(u["durum"] == "Aktif" for u in uyeler)
    yaklasan = sum(u["durum"] == "Yaklaşıyor" for u in uyeler)
    dolan = sum(u["durum"] == "Süresi Doldu" for u in uyeler)
    bugun = sum(u["durum"] == "Bugün Bitiyor" for u in uyeler)

    db.close()

    return render_template(
        "dashboard.html",
        uyeler=uyeler,
        toplam=toplam,
        aktif=aktif,
        yaklasan=yaklasan,
        dolan=dolan,
        bugun=bugun,
        arama=arama
    )


@app.route("/uye/yeni", methods=["POST"])
def uye_yeni():
    db = get_db()

    db.execute("""
        INSERT INTO uyeler
        (ad, soyad, telefon, notlar, baslangic, bitis)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        request.form.get("ad", "").strip(),
        request.form.get("soyad", "").strip(),
        request.form.get("telefon", "").strip(),
        request.form.get("notlar", "").strip(),
        request.form.get("baslangic", "").strip(),
        request.form.get("bitis", "").strip()
    ))

    db.commit()
    db.close()

    return redirect(url_for("dashboard"))


@app.route("/uye/<int:uye_id>/duzenle", methods=["POST"])
def uye_duzenle(uye_id):
    db = get_db()

    db.execute("""
        UPDATE uyeler
        SET ad = ?, soyad = ?, telefon = ?, notlar = ?, baslangic = ?, bitis = ?
        WHERE id = ?
    """, (
        request.form.get("ad", "").strip(),
        request.form.get("soyad", "").strip(),
        request.form.get("telefon", "").strip(),
        request.form.get("notlar", "").strip(),
        request.form.get("baslangic", "").strip(),
        request.form.get("bitis", "").strip(),
        uye_id
    ))

    db.commit()
    db.close()

    return redirect(url_for("dashboard"))


@app.route("/uye/<int:uye_id>/yenile", methods=["POST"])
def uye_yenile(uye_id):
    try:
        ay = int(request.form.get("ay_sayisi", "0"))
    except ValueError:
        ay = 0

    if ay < 1:
        return redirect(url_for("dashboard"))

    db = get_db()

    uye = db.execute("""
        SELECT bitis
        FROM uyeler
        WHERE id = ?
    """, (uye_id,)).fetchone()

    son_odeme = db.execute("""
        SELECT tutar, ay_sayisi
        FROM odemeler
        WHERE uye_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (uye_id,)).fetchone()

    if not uye or not son_odeme:
        db.close()
        return redirect(url_for("dashboard"))

    try:
        son_ay = int(son_odeme["ay_sayisi"])
        son_tutar = float(son_odeme["tutar"])
        if son_ay < 1 or son_tutar <= 0:
            raise ValueError
        aylik = son_tutar / son_ay
    except (TypeError, ValueError, ZeroDivisionError):
        db.close()
        return redirect(url_for("dashboard"))

    temel_tarih = uye["bitis"] or date.today().isoformat()

    try:
        yeni_bitis = ay_ekle(temel_tarih, ay)
    except ValueError:
        db.close()
        return redirect(url_for("dashboard"))

    toplam_tutar = aylik * ay

    db.execute("""
        UPDATE uyeler
        SET bitis = ?
        WHERE id = ?
    """, (yeni_bitis, uye_id))

    db.execute("""
        INSERT INTO odemeler
        (uye_id, tutar, tarih, aciklama, ay_sayisi)
        VALUES (?, ?, ?, ?, ?)
    """, (
        uye_id,
        f"{toplam_tutar:.2f}",
        date.today().isoformat(),
        "Üyelik yenileme",
        ay
    ))

    db.commit()
    db.close()

    return redirect(url_for("dashboard"))


@app.route("/uye/<int:uye_id>/sil", methods=["POST"])
def uye_sil(uye_id):
    db = get_db()

    db.execute("DELETE FROM odemeler WHERE uye_id = ?", (uye_id,))
    db.execute("DELETE FROM uyeler WHERE id = ?", (uye_id,))

    db.commit()
    db.close()

    return redirect(url_for("dashboard"))


@app.route("/uye/<int:uye_id>/odeme", methods=["POST"])
def odeme_ekle(uye_id):
    tutar = request.form.get("tutar", "").strip()
    tarih = request.form.get("tarih", "").strip()
    aciklama = request.form.get("aciklama", "").strip()

    try:
        ay = int(request.form.get("ay_sayisi", "1"))
    except ValueError:
        ay = 1

    if ay < 1:
        ay = 1

    db = get_db()

    db.execute("""
        INSERT INTO odemeler
        (uye_id, tutar, tarih, aciklama, ay_sayisi)
        VALUES (?, ?, ?, ?, ?)
    """, (uye_id, tutar, tarih, aciklama, ay))

    uye = db.execute("""
        SELECT baslangic
        FROM uyeler
        WHERE id = ?
    """, (uye_id,)).fetchone()

    if ay > 1 and uye and uye["baslangic"]:
        try:
            yeni_bitis = ay_ekle(uye["baslangic"], ay)
            db.execute("""
                UPDATE uyeler
                SET bitis = ?
                WHERE id = ?
            """, (yeni_bitis, uye_id))
        except ValueError:
            pass

    db.commit()
    db.close()

    return redirect(url_for("dashboard"))


@app.route("/api/uye/<int:uye_id>/yenile-bilgisi")
def uye_yenile_bilgisi(uye_id):
    db = get_db()

    uye = db.execute("""
        SELECT bitis
        FROM uyeler
        WHERE id = ?
    """, (uye_id,)).fetchone()

    odeme = db.execute("""
        SELECT tutar, ay_sayisi
        FROM odemeler
        WHERE uye_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (uye_id,)).fetchone()

    db.close()

    if not uye:
        return jsonify({"ok": False, "mesaj": "Üye bulunamadı."}), 404

    if not odeme:
        return jsonify({"ok": False, "mesaj": "Ödeme kaydı bulunamadı."})

    try:
        son_tutar = float(odeme["tutar"])
        son_ay = int(odeme["ay_sayisi"])
        if son_ay < 1 or son_tutar <= 0:
            raise ValueError
        aylik = son_tutar / son_ay
    except (TypeError, ValueError, ZeroDivisionError):
        return jsonify({"ok": False, "mesaj": "Son ödeme bilgisi geçersiz."})

    return jsonify({
        "ok": True,
        "son_tutar": son_tutar,
        "son_ay": son_ay,
        "aylik": aylik,
        "bitis": uye["bitis"] or date.today().isoformat()
    })


@app.route("/api/uye/<int:uye_id>/odemeler")
def uye_odemeler(uye_id):
    db = get_db()

    odemeler = db.execute("""
        SELECT *
        FROM odemeler
        WHERE uye_id = ?
        ORDER BY id DESC
    """, (uye_id,)).fetchall()

    db.close()

    return jsonify([dict(o) for o in odemeler])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
