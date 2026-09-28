package com.eagleai.generated.uyeleri_uyelik_durumunu_odeme;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ContentValues;
import android.content.Intent;
import android.net.Uri;
import android.content.pm.PackageManager;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.View;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {

    private Veritabani db;
    private LinearLayout liste;
    private TextView toplam;
    private TextView aktif;
    private TextView yaklasan;
    private TextView dolan;
    private TextView bugun;
    private EditText arama;
    private LinearLayout uyelerEkrani;
    private LinearLayout odemelerEkrani;

    private String bekleyenSmsMetni = null;
    private String bekleyenSmsTelefon = null;
    private String bekleyenSmsUyeMetni = null;
    private static final int SMS_IZIN_KODU = 2001;
    private static final int SMS_UYE_IZIN_KODU = 2002;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        db = new Veritabani();

        LinearLayout ana = new LinearLayout(this);
        ana.setOrientation(LinearLayout.VERTICAL);
        ana.setPadding(18, 18, 18, 18);
        ana.setBackgroundColor(Color.rgb(248, 249, 251));

        TextView baslik = new TextView(this);
        baslik.setText("🏋️ Üye Takip");
        baslik.setTextSize(25);
        baslik.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        baslik.setTextColor(Color.rgb(25, 55, 95));
        baslik.setPadding(0, 0, 0, 12);
        ana.addView(baslik);

        LinearLayout sekmeler = new LinearLayout(this);
        sekmeler.setOrientation(LinearLayout.HORIZONTAL);

        Button uyeSekme = new Button(this);
        uyeSekme.setText("👥 Üyeler");
        uyeSekme.setAllCaps(false);

        Button odemeSekme = new Button(this);
        odemeSekme.setText("💳 Ödemeler");
        odemeSekme.setAllCaps(false);

        renkliButon(uyeSekme, Color.rgb(25, 118, 210), Color.WHITE);
        renkliButon(odemeSekme, Color.rgb(96, 125, 139), Color.WHITE);

        sekmeler.addView(
            uyeSekme,
            new LinearLayout.LayoutParams(0, 52, 1f)
        );
        sekmeler.addView(
            odemeSekme,
            new LinearLayout.LayoutParams(0, 52, 1f)
        );
        ana.addView(sekmeler);

        uyelerEkrani = new LinearLayout(this);
        uyelerEkrani.setOrientation(LinearLayout.VERTICAL);

        LinearLayout ozet = new LinearLayout(this);
        ozet.setOrientation(LinearLayout.VERTICAL);

        toplam = kutu("Toplam Üye: 0");
        aktif = kutu("Aktif Üye: 0");
        yaklasan = kutu("Süresi Yaklaşan: 0");
        dolan = kutu("Süresi Dolan: 0");
        bugun = kutu("🟡 Bugün Bitiyor: 0");

        ozet.addView(toplam);
        ozet.addView(aktif);
        ozet.addView(yaklasan);
        ozet.addView(dolan);
        ozet.addView(bugun);
        uyelerEkrani.addView(ozet);

        arama = new EditText(this);
        arama.setHint("Üye ara...");
        arama.setSingleLine(true);
        uyelerEkrani.addView(arama);

        LinearLayout ustButonlar = new LinearLayout(this);
        ustButonlar.setOrientation(LinearLayout.HORIZONTAL);
        ustButonlar.setPadding(0, 4, 0, 8);

        Button yeni = new Button(this);
        yeni.setText("➕ Yeni Üye");
        yeni.setAllCaps(false);
        renkliButon(yeni, Color.rgb(27, 94, 32), Color.WHITE);

        Button duyuru = new Button(this);
        duyuru.setText("📩 SMS Duyuru");
        duyuru.setAllCaps(false);
        renkliButon(duyuru, Color.rgb(66, 66, 66), Color.WHITE);
        duyuru.setGravity(android.view.Gravity.CENTER);

        LinearLayout.LayoutParams yeniLp =
            new LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1f
            );
        yeniLp.setMargins(0, 0, 4, 0);

        LinearLayout.LayoutParams duyuruLp =
            new LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1f
            );
        duyuruLp.setMargins(4, 0, 0, 0);

        ustButonlar.addView(yeni, yeniLp);
        ustButonlar.addView(duyuru, duyuruLp);
        uyelerEkrani.addView(ustButonlar);

        yeni.setOnClickListener(v -> uyeFormu(-1));
        duyuru.setOnClickListener(v -> smsDuyuru());

        ScrollView kaydir = new ScrollView(this);
        liste = new LinearLayout(this);
        liste.setOrientation(LinearLayout.VERTICAL);
        liste.setPadding(0, 8, 0, 20);
        kaydir.addView(liste);

        uyelerEkrani.addView(
            kaydir,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
            )
        );

        ana.addView(
            uyelerEkrani,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
            )
        );

        odemelerEkrani = odemeSekmesiOlustur();
        odemelerEkrani.setVisibility(View.GONE);

        ana.addView(
            odemelerEkrani,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
            )
        );

        yeni.setOnClickListener(v -> uyeFormu(-1));

        arama.addTextChangedListener(new android.text.TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                listele(s.toString());
            }
            public void afterTextChanged(android.text.Editable s) {}
        });

        uyeSekme.setOnClickListener(v -> {
            uyelerEkrani.setVisibility(View.VISIBLE);
            odemelerEkrani.setVisibility(View.GONE);
            renkliButon(uyeSekme, Color.rgb(25, 118, 210), Color.WHITE);
            renkliButon(odemeSekme, Color.rgb(96, 125, 139), Color.WHITE);
        });

        odemeSekme.setOnClickListener(v -> {
            uyelerEkrani.setVisibility(View.GONE);
            odemelerEkrani.setVisibility(View.VISIBLE);
            renkliButon(uyeSekme, Color.rgb(96, 125, 139), Color.WHITE);
            renkliButon(odemeSekme, Color.rgb(25, 118, 210), Color.WHITE);
            odemeleriGuncelle();
        });


        yeni.setOnClickListener(v -> uyeFormu(-1));

        arama.addTextChangedListener(new android.text.TextWatcher() {
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            public void onTextChanged(CharSequence s, int start, int before, int count) {
                listele(s.toString());
            }
            public void afterTextChanged(android.text.Editable s) {}
        });

        setContentView(ana);
        listele("");

        if (!"🟡 Bugün Bitiyor: 0".equals(bugun.getText().toString())) {
            new AlertDialog.Builder(this)
                .setTitle("⚠️ Üyelik Uyarısı")
                .setMessage("Bugün süresi dolacak üyeler var.\n\nÜye listesinden kontrol edebilirsiniz.")
                .setPositiveButton("Tamam", null)
                .show();
        }
    }

    private void renkliButon(Button b, int arkaPlan, int yazi) {
        b.setTextColor(yazi);
        b.setAllCaps(false);

        GradientDrawable g = new GradientDrawable();
        g.setColor(arkaPlan);
        g.setCornerRadius(22);
        b.setBackground(g);
        b.setPadding(14, 8, 14, 8);
    }

    private String durumIkonu(String durum) {
        if ("Aktif".equals(durum)) return "🟢";
        if ("Bugün Bitiyor".equals(durum)) return "🟡";
        if ("Yaklaşıyor".equals(durum)) return "🟠";
        if ("Süresi Doldu".equals(durum)) return "🔴";
        return "⚪";
    }

    private GradientDrawable kartArkaPlan(String durum) {
        int renk = Color.rgb(230, 235, 242);

        if ("Aktif".equals(durum)) {
            renk = Color.rgb(190, 235, 200);
        }
        if ("Bugün Bitiyor".equals(durum)) {
            renk = Color.rgb(255, 235, 150);
        }
        if ("Yaklaşıyor".equals(durum)) {
            renk = Color.rgb(255, 220, 120);
        }
        if ("Süresi Doldu".equals(durum)) {
            renk = Color.rgb(255, 175, 175);
        }

        GradientDrawable g = new GradientDrawable();
        g.setColor(renk);
        g.setCornerRadius(24);
        g.setStroke(2, Color.rgb(220, 225, 232));
        return g;
    }

    private TextView kutu(String metin) {
        TextView t = new TextView(this);
        t.setText(metin);
        t.setTextSize(16);
        t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        t.setTextColor(Color.rgb(35, 35, 35));
        t.setPadding(14, 12, 14, 12);
        return t;
    }

    private void yanipSonuyor(View hedef) {
        AlphaAnimation anim = new AlphaAnimation(1.0f, 0.25f);
        anim.setDuration(550);
        anim.setRepeatMode(Animation.REVERSE);
        anim.setRepeatCount(Animation.INFINITE);
        hedef.startAnimation(anim);
    }

    private void listele(String sorgu) {
        liste.removeAllViews();

        int toplamSayi = 0;
        int aktifSayi = 0;
        int yaklasanSayi = 0;
        int dolanSayi = 0;
        int bugunSayi = 0;

        Cursor c = db.getReadableDatabase().rawQuery(
            "SELECT id, ad, soyad, telefon, notlar, baslangic, bitis " +
            "FROM uyeler " +
            "WHERE ad LIKE ? OR soyad LIKE ? OR telefon LIKE ? " +
            "ORDER BY id DESC",
            new String[] {
                "%" + sorgu + "%",
                "%" + sorgu + "%",
                "%" + sorgu + "%"
            }
        );

        while (c.moveToNext()) {
            toplamSayi++;

            int id = c.getInt(0);
            String ad = c.getString(1);
            String soyad = c.getString(2);
            String telefon = c.getString(3);
            String notlar = c.getString(4);
            String baslangic = c.getString(5);
            String bitis = c.getString(6);

            String durum = durumHesapla(bitis);

            if ("Aktif".equals(durum)) aktifSayi++;
            if ("Bugün Bitiyor".equals(durum)) bugunSayi++;
            if ("Yaklaşıyor".equals(durum)) yaklasanSayi++;
            if ("Süresi Doldu".equals(durum)) dolanSayi++;

            LinearLayout kart = new LinearLayout(this);
            kart.setOrientation(LinearLayout.VERTICAL);
            kart.setPadding(18, 16, 18, 16);
            kart.setBackground(kartArkaPlan(durum));

            TextView bilgi = new TextView(this);
            bilgi.setText(
                "👤 " + ad + " " + soyad +
                "\n📞 " + telefon +
                "\n📅 " + baslangic + " → " + bitis +
                "\n" + durumIkonu(durum) + " " + durum +
                (notlar.isEmpty() ? "" : "\n📝 " + notlar)
            );
            bilgi.setTextSize(16);
            bilgi.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            bilgi.setTextColor(Color.rgb(35, 35, 35));

            if ("Bugün Bitiyor".equals(durum)) {
                yanipSonuyor(bilgi);
            }

            kart.addView(bilgi);

            LinearLayout butonlar = new LinearLayout(this);
            butonlar.setOrientation(LinearLayout.HORIZONTAL);

            Button duzenle = new Button(this);
            duzenle.setText("✏️ Düzenle");
            duzenle.setAllCaps(false);
            duzenle.setOnClickListener(v -> uyeFormu(id));

            Button yenile = new Button(this);
            yenile.setText("🔄 Yenile");
            yenile.setAllCaps(false);
            yenile.setOnClickListener(v -> uyelikYenile(id));

            Button odeme = new Button(this);
            odeme.setText("💳 Ödeme");
            odeme.setAllCaps(false);
            odeme.setOnClickListener(v -> odemeEkle(id));

            Button gecmis = new Button(this);
            gecmis.setText("📜 Geçmiş");
            gecmis.setAllCaps(false);
            gecmis.setOnClickListener(v -> odemeGecmisi(id));

            Button sms = new Button(this);
            sms.setText("📩 SMS");
            sms.setAllCaps(false);
            sms.setOnClickListener(v -> smsUyeDuyuru(ad, soyad, telefon));

            Button sil = new Button(this);
            sil.setText("🗑️ Sil");
            sil.setAllCaps(false);

            renkliButon(duzenle, Color.rgb(84, 110, 122), Color.WHITE);
            renkliButon(yenile, Color.rgb(46, 125, 50), Color.WHITE);
            renkliButon(odeme, Color.rgb(25, 118, 210), Color.WHITE);
            renkliButon(gecmis, Color.rgb(123, 31, 162), Color.WHITE);
            renkliButon(sms, Color.rgb(66, 66, 66), Color.WHITE);
            renkliButon(sil, Color.rgb(198, 40, 40), Color.WHITE);

            sil.setOnClickListener(v -> uyeSil(id));

            Button[] butonDizisi = {
                duzenle, yenile, odeme, gecmis, sms, sil
            };

            for (Button buton : butonDizisi) {
                buton.setMinWidth(0);
                buton.setMinimumWidth(0);
                buton.setMinHeight(0);
                buton.setMinimumHeight(0);
                buton.setTextSize(10);
                buton.setGravity(android.view.Gravity.CENTER);
                buton.setPadding(0, 4, 0, 4);
                buton.setIncludeFontPadding(false);
            }

            for (Button buton : butonDizisi) {
                LinearLayout.LayoutParams butonLp =
                    new LinearLayout.LayoutParams(
                        0,
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        1f
                    );
                butonLp.setMargins(2, 3, 2, 3);
                butonLp.width = 0;
                butonLp.weight = 1f;
                butonlar.addView(buton, butonLp);
            }

            kart.addView(butonlar);

            LinearLayout.LayoutParams lp =
                new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                );
            lp.setMargins(0, 0, 0, 12);
            liste.addView(kart, lp);
        }

        c.close();

        toplam.setText("Toplam Üye: " + toplamSayi);
        aktif.setText("Aktif Üye: " + aktifSayi);
        bugun.setText("🟡 Bugün Bitiyor: " + bugunSayi);

        bugun.clearAnimation();
        if (bugunSayi > 0) {
            yanipSonuyor(bugun);
        }

        yaklasan.setText("Süresi Yaklaşan: " + yaklasanSayi);
        dolan.setText("Süresi Dolan: " + dolanSayi);
    }

    private String durumHesapla(String bitis) {
        try {
            String temiz = bitis == null ? "" : bitis.trim();

            String[] formatlar = {
                "yyyy-MM-dd",
                "dd.MM.yyyy",
                "dd/MM/yyyy",
                "dd-MM-yyyy"
            };

            java.util.Date hedef = null;

            for (String desen : formatlar) {
                try {
                    java.text.SimpleDateFormat f =
                        new java.text.SimpleDateFormat(desen);
                    f.setLenient(false);
                    hedef = f.parse(temiz);
                    if (hedef != null) break;
                } catch (Exception ignored) {
                }
            }

            if (hedef == null) return "Bilinmiyor";

            java.util.Calendar bugun =
                java.util.Calendar.getInstance();
            bugun.set(java.util.Calendar.HOUR_OF_DAY, 0);
            bugun.set(java.util.Calendar.MINUTE, 0);
            bugun.set(java.util.Calendar.SECOND, 0);
            bugun.set(java.util.Calendar.MILLISECOND, 0);

            java.util.Calendar hedefGun =
                java.util.Calendar.getInstance();
            hedefGun.setTime(hedef);
            hedefGun.set(java.util.Calendar.HOUR_OF_DAY, 0);
            hedefGun.set(java.util.Calendar.MINUTE, 0);
            hedefGun.set(java.util.Calendar.SECOND, 0);
            hedefGun.set(java.util.Calendar.MILLISECOND, 0);

            long fark =
                hedefGun.getTimeInMillis() -
                bugun.getTimeInMillis();

            long gun =
                fark / (1000L * 60L * 60L * 24L);

            if (gun < 0) return "Süresi Doldu";
            if (gun == 0) return "Bugün Bitiyor";
            if (gun <= 7) return "Yaklaşıyor";
            return "Aktif";
        } catch (Exception e) {
            return "Bilinmiyor";
        }
    }

    private void uyeFormu(int id) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(20, 10, 20, 0);

        EditText ad = alan("Ad");
        EditText soyad = alan("Soyad");
        EditText telefon = alan("Telefon");
        EditText notlar = alan("Not");
        EditText baslangic = alan("Başlangıç tarihi (YYYY-AA-GG)");
        EditText bitis = alan("Bitiş tarihi (YYYY-AA-GG)");

        form.addView(ad);
        form.addView(soyad);
        form.addView(telefon);
        form.addView(notlar);
        form.addView(baslangic);
        form.addView(bitis);

        if (id >= 0) {
            Cursor c = db.getReadableDatabase().rawQuery(
                "SELECT ad, soyad, telefon, notlar, baslangic, bitis " +
                "FROM uyeler WHERE id=?",
                new String[]{String.valueOf(id)}
            );
            if (c.moveToFirst()) {
                ad.setText(c.getString(0));
                soyad.setText(c.getString(1));
                telefon.setText(c.getString(2));
                notlar.setText(c.getString(3));
                baslangic.setText(c.getString(4));
                bitis.setText(c.getString(5));
            }
            c.close();
        }

        new AlertDialog.Builder(this)
            .setTitle(id < 0 ? "Yeni Üye" : "Üye Düzenle")
            .setView(form)
            .setPositiveButton("Kaydet", (dialog, which) -> {
                ContentValues v = new ContentValues();
                v.put("ad", ad.getText().toString().trim());
                v.put("soyad", soyad.getText().toString().trim());
                v.put("telefon", telefon.getText().toString().trim());
                v.put("notlar", notlar.getText().toString().trim());
                v.put("baslangic", baslangic.getText().toString().trim());
                v.put("bitis", bitis.getText().toString().trim());

                if (id < 0) {
                    db.getWritableDatabase().insert("uyeler", null, v);
                    Toast.makeText(this, "Üye eklendi", Toast.LENGTH_SHORT).show();
                } else {
                    db.getWritableDatabase().update(
                        "uyeler", v, "id=?", new String[]{String.valueOf(id)}
                    );
                    Toast.makeText(this, "Üye güncellendi", Toast.LENGTH_SHORT).show();
                }
                listele(arama.getText().toString());
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private EditText alan(String ipucu) {
        EditText e = new EditText(this);
        e.setHint(ipucu);
        e.setSingleLine(true);
        return e;
    }

    private void uyeSil(int id) {
        new AlertDialog.Builder(this)
            .setTitle("Üye silinsin mi?")
            .setMessage("Bu işlem üyeyi ve bağlı ödeme kayıtlarını kaldırır.")
            .setPositiveButton("Sil", (d, w) -> {
                SQLiteDatabase sql = db.getWritableDatabase();
                sql.delete("odemeler", "uye_id=?", new String[]{String.valueOf(id)});
                sql.delete("uyeler", "id=?", new String[]{String.valueOf(id)});
                listele(arama.getText().toString());
                Toast.makeText(this, "Üye silindi", Toast.LENGTH_SHORT).show();
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private void uyelikYenile(int id) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);

        EditText bitis = alan("Yeni bitiş tarihi (YYYY-AA-GG)");
        form.addView(bitis);

        new AlertDialog.Builder(this)
            .setTitle("Üyelik Yenile")
            .setView(form)
            .setPositiveButton("Yenile", (d, w) -> {
                ContentValues v = new ContentValues();
                v.put("bitis", bitis.getText().toString().trim());
                db.getWritableDatabase().update(
                    "uyeler", v, "id=?", new String[]{String.valueOf(id)}
                );
                listele(arama.getText().toString());
                Toast.makeText(this, "Üyelik yenilendi", Toast.LENGTH_SHORT).show();
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private LinearLayout odemeSekmesiOlustur() {
        LinearLayout ekran = new LinearLayout(this);
        ekran.setOrientation(LinearLayout.VERTICAL);
        ekran.setPadding(0, 12, 0, 20);

        TextView baslik = new TextView(this);
        baslik.setText("💳 Ödeme Takibi");
        baslik.setTextSize(22);
        baslik.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        baslik.setTextColor(Color.rgb(25, 55, 95));
        baslik.setPadding(0, 0, 0, 12);
        ekran.addView(baslik);

        TextView toplam = kutu("💰 Bu Ay Tahsilat: 0,00 TL");
        TextView adet = kutu("🧾 Bu Ay Ödeme Sayısı: 0");
        TextView toplamGenel = kutu("💵 Toplam Tahsilat: 0,00 TL");
        TextView adetGenel = kutu("📋 Toplam Ödeme Sayısı: 0");

        ekran.addView(toplam);
        ekran.addView(adet);
        ekran.addView(toplamGenel);
        ekran.addView(adetGenel);

        TextView sonBaslik = new TextView(this);
        sonBaslik.setText("📋 Son Ödemeler");
        sonBaslik.setTextSize(18);
        sonBaslik.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        sonBaslik.setTextColor(Color.rgb(35, 35, 35));
        sonBaslik.setPadding(4, 18, 4, 8);
        ekran.addView(sonBaslik);

        ScrollView kaydir = new ScrollView(this);
        LinearLayout liste = new LinearLayout(this);
        liste.setOrientation(LinearLayout.VERTICAL);
        liste.setPadding(0, 4, 0, 20);
        kaydir.addView(liste);

        ekran.addView(
            kaydir,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
            )
        );

        ekran.setTag(new Object[]{toplam, adet, toplamGenel, adetGenel, liste});
        return ekran;
    }

    private double tutarSayiyaCevir(String metin) {
        if (metin == null) return 0.0;

        String s = metin.trim()
            .replace("TL", "")
            .replace("₺", "")
            .replace(" ", "");

        if (s.isEmpty()) return 0.0;

        try {
            int virgul = s.lastIndexOf(',');
            int nokta = s.lastIndexOf('.');

            if (virgul >= 0 && nokta >= 0) {
                if (virgul > nokta) {
                    s = s.replace(".", "").replace(",", ".");
                } else {
                    s = s.replace(",", "");
                }
            } else if (virgul >= 0) {
                s = s.replace(",", ".");
            } else if (nokta >= 0) {
                int ondalik = s.length() - nokta - 1;
                if (ondalik == 3) {
                    s = s.replace(".", "");
                }
            }

            return Double.parseDouble(s);
        } catch (Exception e) {
            return 0.0;
        }
    }

    private void odemeleriGuncelle() {
        if (odemelerEkrani == null) return;

        Object[] parcalar = (Object[]) odemelerEkrani.getTag();
        TextView toplam = (TextView) parcalar[0];
        TextView adet = (TextView) parcalar[1];
        TextView toplamGenel = (TextView) parcalar[2];
        TextView adetGenel = (TextView) parcalar[3];
        LinearLayout liste = (LinearLayout) parcalar[4];

        liste.removeAllViews();

        double toplamTutar = 0.0;
        int odemeSayisi = 0;
        double genelToplamTutar = 0.0;
        int genelOdemeSayisi = 0;

        java.util.Calendar simdi = java.util.Calendar.getInstance();
        int buYil = simdi.get(java.util.Calendar.YEAR);
        int buAy = simdi.get(java.util.Calendar.MONTH) + 1;

        Cursor toplamCursor = db.getReadableDatabase().rawQuery(
            "SELECT tutar, tarih FROM odemeler",
            null
        );

        while (toplamCursor.moveToNext()) {
            String tutarMetni = toplamCursor.getString(0);
            String tarihMetni = toplamCursor.getString(1);

            genelToplamTutar += tutarSayiyaCevir(tutarMetni);
            genelOdemeSayisi++;

            if (tarihMetni == null) continue;

            java.util.Date odemeTarihi = null;
            String temizTarih = tarihMetni.trim();

            String[] formatlar = {
                "yyyy-MM-dd",
                "dd.MM.yyyy",
                "dd/MM/yyyy",
                "dd-MM-yyyy"
            };

            for (String desen : formatlar) {
                try {
                    java.text.SimpleDateFormat f =
                        new java.text.SimpleDateFormat(desen);
                    f.setLenient(false);
                    odemeTarihi = f.parse(temizTarih);
                    if (odemeTarihi != null) break;
                } catch (Exception ignored) {}
            }

            if (odemeTarihi != null) {
                java.util.Calendar odeme =
                    java.util.Calendar.getInstance();
                odeme.setTime(odemeTarihi);

                if (odeme.get(java.util.Calendar.YEAR) == buYil &&
                    odeme.get(java.util.Calendar.MONTH) + 1 == buAy) {
                    toplamTutar += tutarSayiyaCevir(tutarMetni);
                    odemeSayisi++;
                }
            }
        }

        toplamCursor.close();

        toplam.setText(
            "💰 Bu Ay Tahsilat: " +
            String.format(java.util.Locale.US, "%,.2f", toplamTutar)
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".") +
            " TL"
        );

        adet.setText("🧾 Bu Ay Ödeme Sayısı: " + odemeSayisi);

        toplamGenel.setText(
            "💵 Toplam Tahsilat: " +
            String.format(java.util.Locale.US, "%,.2f", genelToplamTutar)
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".") +
            " TL"
        );

        adetGenel.setText(
            "📋 Toplam Ödeme Sayısı: " + genelOdemeSayisi
        );

        Cursor c = db.getReadableDatabase().rawQuery(
            "SELECT o.id, o.tutar, o.tarih, o.aciklama, " +
            "o.ay_sayisi, o.uye_id, u.ad, u.soyad " +
            "FROM odemeler o " +
            "LEFT JOIN uyeler u ON u.id=o.uye_id " +
            "ORDER BY o.id DESC LIMIT 20",
            null
        );

        while (c.moveToNext()) {
            int odemeId = c.getInt(0);
            String tutar = c.getString(1);
            String tarih = c.getString(2);
            String aciklama = c.getString(3);
            int aySayisi = c.getInt(4);
            int uyeId = c.getInt(5);
            String ad = c.getString(6);
            String soyad = c.getString(7);

            if (ad == null || ad.trim().isEmpty()) ad = "Bilinmeyen Üye";
            if (soyad == null) soyad = "";

            LinearLayout kart = new LinearLayout(this);
            kart.setOrientation(LinearLayout.VERTICAL);
            kart.setPadding(16, 14, 16, 14);
            kart.setBackground(kartArkaPlan("Aktif"));

            TextView bilgi = new TextView(this);
            bilgi.setText(
                "👤 " + ad + " " + soyad.trim() +
                "\n💰 " + (tutar == null ? "" : tutar) + " TL" +
                "\n📆 " + aySayisi + " Ay" +
                "\n📅 " + (tarih == null ? "" : tarih) +
                ((aciklama == null || aciklama.trim().isEmpty())
                    ? ""
                    : "\n📝 " + aciklama)
            );
            bilgi.setTextSize(15);
            bilgi.setTextColor(Color.rgb(35, 35, 35));

            kart.addView(bilgi);

            Button duzenle = new Button(this);
            duzenle.setText("✏️ Düzenle");
            duzenle.setAllCaps(false);
            duzenle.setTextSize(12);
            duzenle.setOnClickListener(
                v -> odemeDuzenle(odemeId, uyeId)
            );
            kart.addView(duzenle);

            LinearLayout.LayoutParams lp =
                new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                );
            lp.setMargins(0, 0, 0, 10);

            liste.addView(kart, lp);
        }

        c.close();

        if (liste.getChildCount() == 0) {
            TextView bos = new TextView(this);
            bos.setText("Henüz ödeme kaydı bulunmuyor.");
            bos.setTextSize(16);
            bos.setTextColor(Color.rgb(90, 90, 90));
            bos.setPadding(12, 20, 12, 20);
            liste.addView(bos);
        }
    }

    private void smsUyeDuyuru(String ad, String soyad, String telefon) {
        if (telefon == null || telefon.trim().isEmpty()) {
            Toast.makeText(
                this,
                "Bu üyeye ait telefon numarası bulunamadı.",
                Toast.LENGTH_LONG
            ).show();
            return;
        }

        final EditText mesaj = new EditText(this);
        mesaj.setHint("SMS mesajı");
        mesaj.setGravity(android.view.Gravity.TOP);
        mesaj.setMinLines(4);
        mesaj.setSingleLine(false);

        String adSoyad = (ad + " " + (soyad == null ? "" : soyad)).trim();

        new AlertDialog.Builder(this)
            .setTitle("📩 " + adSoyad + " — SMS")
            .setView(mesaj)
            .setPositiveButton("Gönder", (d, w) -> {
                String metin = mesaj.getText().toString().trim();

                if (metin.isEmpty()) {
                    Toast.makeText(
                        this,
                        "SMS mesajı boş olamaz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }

                bekleyenSmsTelefon = telefon.trim();
                bekleyenSmsUyeMetni = metin;

                if (android.os.Build.VERSION.SDK_INT >= 23 &&
                    checkSelfPermission(android.Manifest.permission.SEND_SMS)
                        != PackageManager.PERMISSION_GRANTED) {

                    requestPermissions(
                        new String[]{android.Manifest.permission.SEND_SMS},
                        SMS_UYE_IZIN_KODU
                    );
                    return;
                }

                smsTekUyeGonder(bekleyenSmsTelefon, bekleyenSmsUyeMetni);
                bekleyenSmsTelefon = null;
                bekleyenSmsUyeMetni = null;
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private void smsTekUyeGonder(String telefon, String metin) {
        if (telefon == null || metin == null ||
            telefon.trim().isEmpty() || metin.trim().isEmpty()) {
            return;
        }

        String numara = telefon.trim().replaceAll("[^0-9+]", "");

        if (numara.startsWith("+")) {
            numara = numara.substring(1);
        } else if (numara.startsWith("0") && numara.length() == 11) {
            numara = "90" + numara.substring(1);
        } else if (numara.length() == 10 && numara.startsWith("5")) {
            numara = "90" + numara;
        }

        if (numara.length() != 12 || !numara.startsWith("90")) {
            Toast.makeText(
                this,
                "Geçerli bir telefon numarası bulunamadı.",
                Toast.LENGTH_LONG
            ).show();
            return;
        }

        try {
            android.telephony.SmsManager smsManager =
                android.telephony.SmsManager.getDefault();

            java.util.ArrayList<String> parcalar =
                smsManager.divideMessage(metin);

            smsManager.sendMultipartTextMessage(
                numara,
                null,
                parcalar,
                null,
                null
            );

            Toast.makeText(
                this,
                "SMS gönderimi başlatıldı.",
                Toast.LENGTH_LONG
            ).show();

        } catch (SecurityException e) {
            Toast.makeText(
                this,
                "SMS gönderme izni verilmedi.",
                Toast.LENGTH_LONG
            ).show();
        } catch (Exception e) {
            Toast.makeText(
                this,
                "SMS gönderimi başlatılamadı.",
                Toast.LENGTH_LONG
            ).show();
        }
    }

    private void smsDuyuru() {
        final EditText mesaj = new EditText(this);
        mesaj.setHint("Duyuru mesajı");
        mesaj.setGravity(android.view.Gravity.TOP);
        mesaj.setMinLines(4);
        mesaj.setSingleLine(false);

        new AlertDialog.Builder(this)
            .setTitle("📩 SMS Duyuru")
            .setView(mesaj)
            .setPositiveButton("Devam", (d, w) -> {
                String metin = mesaj.getText().toString().trim();

                if (metin.isEmpty()) {
                    Toast.makeText(
                        this,
                        "Duyuru mesajı boş olamaz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }

                bekleyenSmsMetni = metin;
                smsDuyuruHazirla();
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private void smsDuyuruHazirla() {
        if (android.os.Build.VERSION.SDK_INT >= 23 &&
            checkSelfPermission(android.Manifest.permission.SEND_SMS)
                != PackageManager.PERMISSION_GRANTED) {

            requestPermissions(
                new String[]{android.Manifest.permission.SEND_SMS},
                SMS_IZIN_KODU
            );
            return;
        }

        smsDuyuruOnayla();
    }

    private void smsDuyuruOnayla() {
        if (bekleyenSmsMetni == null || bekleyenSmsMetni.trim().isEmpty()) {
            return;
        }

        java.util.LinkedHashSet<String> numaralar =
            new java.util.LinkedHashSet<>();

        Cursor c = db.getReadableDatabase().query(
            "uyeler",
            new String[]{"telefon"},
            "telefon IS NOT NULL AND TRIM(telefon) <> ''",
            null,
            null,
            null,
            "id ASC"
        );

        while (c.moveToNext()) {
            String telefon = c.getString(0);

            if (telefon == null) {
                continue;
            }

            String numara = telefon.trim();
            numara = numara.replaceAll("[^0-9+]", "");

            if (numara.startsWith("+")) {
                numara = numara.substring(1);
            } else if (numara.startsWith("0") && numara.length() == 11) {
                numara = "90" + numara.substring(1);
            } else if (numara.length() == 10 && numara.startsWith("5")) {
                numara = "90" + numara;
            }

            if (numara.length() == 12 && numara.startsWith("90")) {
                numaralar.add(numara);
            }
        }

        c.close();

        if (numaralar.isEmpty()) {
            Toast.makeText(
                this,
                "SMS gönderilecek geçerli üye telefonu bulunamadı.",
                Toast.LENGTH_LONG
            ).show();
            bekleyenSmsMetni = null;
            return;
        }

        final int adet = numaralar.size();

        new AlertDialog.Builder(this)
            .setTitle("📩 SMS Gönder")
            .setMessage(
                adet + " üyeye SMS gönderilecek.\n\n" +
                "Mesaj:\n" + bekleyenSmsMetni
            )
            .setPositiveButton("Gönder", (d, w) -> {
                smsleriGonder(numaralar, bekleyenSmsMetni);
                bekleyenSmsMetni = null;
            })
            .setNegativeButton("İptal", (d, w) -> {
                bekleyenSmsMetni = null;
            })
            .show();
    }

    private void smsleriGonder(
        java.util.LinkedHashSet<String> numaralar,
        String metin
    ) {
        if (metin == null || metin.trim().isEmpty()) {
            return;
        }

        try {
            android.telephony.SmsManager smsManager =
                android.telephony.SmsManager.getDefault();

            java.util.ArrayList<String> parcalar =
                smsManager.divideMessage(metin);

            int basarili = 0;

            for (String numara : numaralar) {
                try {
                    smsManager.sendMultipartTextMessage(
                        numara,
                        null,
                        parcalar,
                        null,
                        null
                    );
                    basarili++;
                } catch (Exception ignored) {
                }
            }

            Toast.makeText(
                this,
                basarili + " üyeye SMS gönderimi başlatıldı.",
                Toast.LENGTH_LONG
            ).show();

        } catch (SecurityException e) {
            Toast.makeText(
                this,
                "SMS gönderme izni verilmedi.",
                Toast.LENGTH_LONG
            ).show();
        } catch (Exception e) {
            Toast.makeText(
                this,
                "SMS gönderimi başlatılamadı.",
                Toast.LENGTH_LONG
            ).show();
        }
    }

    @Override
    public void onRequestPermissionsResult(
        int requestCode,
        String[] permissions,
        int[] grantResults
    ) {
        super.onRequestPermissionsResult(
            requestCode,
            permissions,
            grantResults
        );

        if (requestCode == SMS_IZIN_KODU) {
            if (grantResults.length > 0 &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED) {

                smsDuyuruOnayla();

            } else {
                bekleyenSmsMetni = null;

                Toast.makeText(
                    this,
                    "SMS gönderme izni verilmedi.",
                    Toast.LENGTH_LONG
                ).show();
            }

            return;
        }

        if (requestCode == SMS_UYE_IZIN_KODU) {
            if (grantResults.length > 0 &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED) {

                smsTekUyeGonder(
                    bekleyenSmsTelefon,
                    bekleyenSmsUyeMetni
                );

            } else {
                Toast.makeText(
                    this,
                    "SMS gönderme izni verilmedi.",
                    Toast.LENGTH_LONG
                ).show();
            }

            bekleyenSmsTelefon = null;
            bekleyenSmsUyeMetni = null;
        }
    }

    private void whatsappUyeDuyuru(String ad, String soyad, String telefon) {
        final EditText mesaj = new EditText(this);
        mesaj.setHint("Mesajı yazın");
        mesaj.setGravity(android.view.Gravity.TOP);
        mesaj.setMinLines(4);
        mesaj.setSingleLine(false);

        new AlertDialog.Builder(this)
            .setTitle("💬 " + ad + " " + soyad)
            .setView(mesaj)
            .setPositiveButton("WhatsApp'ı Aç", (d, w) -> {
                String metin = mesaj.getText().toString().trim();

                if (metin.isEmpty()) {
                    Toast.makeText(
                        this,
                        "Mesaj boş olamaz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }

                String numara = telefon == null ? "" : telefon.trim();
                numara = numara.replaceAll("[^0-9+]", "");

                if (numara.startsWith("+")) {
                    numara = numara.substring(1);
                } else if (numara.startsWith("0") && numara.length() == 11) {
                    numara = "90" + numara.substring(1);
                } else if (numara.length() == 10 && numara.startsWith("5")) {
                    numara = "90" + numara;
                }

                if (numara.length() < 12 || !numara.startsWith("90")) {
                    Toast.makeText(
                        this,
                        "Üyenin telefon numarası geçersiz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }

                try {
                    String kodluMesaj = java.net.URLEncoder.encode(
                        metin,
                        "UTF-8"
                    );

                    Intent intent = new Intent(
                        Intent.ACTION_VIEW,
                        Uri.parse(
                            "https://wa.me/" + numara +
                            "?text=" + kodluMesaj
                        )
                    );
                    intent.setPackage("com.whatsapp");
                    startActivity(intent);
                } catch (Exception e) {
                    Toast.makeText(
                        this,
                        "WhatsApp açılamadı.",
                        Toast.LENGTH_SHORT
                    ).show();
                }
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private void odemeEkle(int uyeId) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);

        EditText tutar = alan("Tutar");
        form.addView(tutar);

        EditText aySayisi = alan("Üyelik Süresi (Ay)");
        aySayisi.setInputType(
            android.text.InputType.TYPE_CLASS_NUMBER
        );
        form.addView(aySayisi);

        EditText tarih = alan("Tarih (YYYY-AA-GG)");
        EditText aciklama = alan("Açıklama");

        form.addView(tarih);
        form.addView(aciklama);

        new AlertDialog.Builder(this)
            .setTitle("Ödeme Ekle")
            .setView(form)
            .setPositiveButton("Kaydet", (d, w) -> {
                ContentValues v = new ContentValues();
                v.put("uye_id", uyeId);
                v.put("tutar", tutar.getText().toString().trim());
                v.put("tarih", tarih.getText().toString().trim());
                v.put("aciklama", aciklama.getText().toString().trim());
                String ayMetni = aySayisi.getText().toString().trim();
                int ay = 1;

                try {
                    ay = Integer.parseInt(ayMetni);
                } catch (Exception ignored) {}

                if (ay < 1) {
                    ay = 1;
                }

                v.put("ay_sayisi", ay);

                db.getWritableDatabase().insert("odemeler", null, v);

                // Ödenen toplam süreyi başlangıç tarihinden hesapla.
                if (ay > 1) {
                    Cursor uyeCursor = db.getReadableDatabase().rawQuery(
                        "SELECT baslangic FROM uyeler WHERE id=?",
                        new String[]{String.valueOf(uyeId)}
                    );

                    if (uyeCursor.moveToFirst()) {
                        String baslangicMetni = uyeCursor.getString(0);

                        try {
                            java.text.SimpleDateFormat giris =
                                new java.text.SimpleDateFormat("yyyy-MM-dd");
                            giris.setLenient(false);

                            java.util.Date baslangicTarihi =
                                giris.parse(baslangicMetni.trim());

                            java.util.Calendar yeniBitis =
                                java.util.Calendar.getInstance();
                            yeniBitis.setTime(baslangicTarihi);
                            yeniBitis.add(java.util.Calendar.MONTH, ay);

                            String yeniBitisMetni =
                                giris.format(yeniBitis.getTime());

                            ContentValues bitisValues =
                                new ContentValues();
                            bitisValues.put("bitis", yeniBitisMetni);

                            db.getWritableDatabase().update(
                                "uyeler",
                                bitisValues,
                                "id=?",
                                new String[]{String.valueOf(uyeId)}
                            );
                        } catch (Exception ignored) {
                        }
                    }

                    uyeCursor.close();
                }

                Toast.makeText(
                    this,
                    "Ödeme kaydedildi",
                    Toast.LENGTH_SHORT
                ).show();
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private void odemeDuzenle(int odemeId, int uyeId) {
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);

        EditText tutar = alan("Tutar");
        EditText aySayisi = alan("Üyelik Süresi (Ay)");
        aySayisi.setInputType(
            android.text.InputType.TYPE_CLASS_NUMBER
        );
        EditText tarih = alan("Tarih (YYYY-AA-GG)");
        EditText aciklama = alan("Açıklama");

        form.addView(tutar);
        form.addView(aySayisi);
        form.addView(tarih);
        form.addView(aciklama);

        Cursor c = db.getReadableDatabase().rawQuery(
            "SELECT tutar, tarih, aciklama, ay_sayisi " +
            "FROM odemeler WHERE id=?",
            new String[]{String.valueOf(odemeId)}
        );

        if (c.moveToFirst()) {
            tutar.setText(c.getString(0));
            tarih.setText(c.getString(1));
            aciklama.setText(c.getString(2));
            aySayisi.setText(String.valueOf(c.getInt(3)));
        }
        c.close();

        new AlertDialog.Builder(this)
            .setTitle("Ödeme Düzenle")
            .setView(form)
            .setPositiveButton("Kaydet", (d, w) -> {
                String ayMetni = aySayisi.getText().toString().trim();
                int ay = 1;

                try {
                    ay = Integer.parseInt(ayMetni);
                } catch (Exception ignored) {}

                if (ay < 1) {
                    ay = 1;
                }

                ContentValues v = new ContentValues();
                v.put("tutar", tutar.getText().toString().trim());
                v.put("tarih", tarih.getText().toString().trim());
                v.put("aciklama", aciklama.getText().toString().trim());
                v.put("ay_sayisi", ay);

                db.getWritableDatabase().update(
                    "odemeler",
                    v,
                    "id=?",
                    new String[]{String.valueOf(odemeId)}
                );

                Cursor uyeCursor = db.getReadableDatabase().rawQuery(
                    "SELECT baslangic FROM uyeler WHERE id=?",
                    new String[]{String.valueOf(uyeId)}
                );

                if (uyeCursor.moveToFirst()) {
                    String baslangicMetni = uyeCursor.getString(0);

                    try {
                        java.text.SimpleDateFormat giris =
                            new java.text.SimpleDateFormat("yyyy-MM-dd");
                        giris.setLenient(false);

                        java.util.Date baslangicTarihi =
                            giris.parse(baslangicMetni.trim());

                        java.util.Calendar yeniBitis =
                            java.util.Calendar.getInstance();
                        yeniBitis.setTime(baslangicTarihi);
                        yeniBitis.add(java.util.Calendar.MONTH, ay);

                        ContentValues bitisValues =
                            new ContentValues();
                        bitisValues.put(
                            "bitis",
                            giris.format(yeniBitis.getTime())
                        );

                        db.getWritableDatabase().update(
                            "uyeler",
                            bitisValues,
                            "id=?",
                            new String[]{String.valueOf(uyeId)}
                        );
                    } catch (Exception ignored) {
                    }
                }

                uyeCursor.close();

                odemeleriGuncelle();

                Toast.makeText(
                    this,
                    "Ödeme güncellendi",
                    Toast.LENGTH_SHORT
                ).show();
            })
            .setNegativeButton("İptal", null)
            .show();
    }

    private void odemeGecmisi(int uyeId) {
        Cursor c = db.getReadableDatabase().rawQuery(
            "SELECT tutar, tarih, aciklama FROM odemeler " +
            "WHERE uye_id=? ORDER BY id DESC",
            new String[]{String.valueOf(uyeId)}
        );

        StringBuilder metin = new StringBuilder();

        while (c.moveToNext()) {
            metin.append("Tutar: ")
                .append(c.getString(0))
                .append("\nTarih: ")
                .append(c.getString(1))
                .append("\n")
                .append(c.getString(2))
                .append("\n\n");
        }
        c.close();

        if (metin.length() == 0) {
            metin.append("Bu üyeye ait ödeme kaydı yok.");
        }

        new AlertDialog.Builder(this)
            .setTitle("Ödeme Geçmişi")
            .setMessage(metin.toString())
            .setPositiveButton("Kapat", null)
            .show();
    }

    private class Veritabani extends SQLiteOpenHelper {
        Veritabani() {
            super(MainActivity.this, "uye_takip.db", null, 2);
        }

        @Override
        public void onCreate(SQLiteDatabase sql) {
            sql.execSQL(
                "CREATE TABLE uyeler (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "ad TEXT NOT NULL," +
                "soyad TEXT," +
                "telefon TEXT," +
                "notlar TEXT," +
                "baslangic TEXT," +
                "bitis TEXT)"
            );

            sql.execSQL(
                "CREATE TABLE odemeler (" +
                "id INTEGER PRIMARY KEY AUTOINCREMENT," +
                "uye_id INTEGER NOT NULL," +
                "tutar TEXT," +
                "tarih TEXT," +
                "aciklama TEXT," +
                "ay_sayisi INTEGER DEFAULT 1)"
            );
        }

        @Override
        public void onUpgrade(
            SQLiteDatabase sql,
            int oldVersion,
            int newVersion
        ) {
            if (oldVersion < 2) {
                sql.execSQL(
                    "ALTER TABLE odemeler ADD COLUMN ay_sayisi INTEGER DEFAULT 1"
                );
            }
        }
    }
}
