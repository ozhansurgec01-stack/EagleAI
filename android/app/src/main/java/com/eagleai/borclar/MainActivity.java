package com.eagleai.borclar;

import android.text.Spannable;
import android.text.SpannableStringBuilder;
import android.text.style.ForegroundColorSpan;
import android.text.style.StyleSpan;
import android.text.style.BackgroundColorSpan;
import android.text.style.TypefaceSpan;
import android.text.Spanned;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import android.app.Activity;
import android.Manifest;
import android.content.pm.PackageManager;
import android.speech.RecognizerIntent;
import android.speech.tts.TextToSpeech;
import android.speech.tts.Voice;
import java.util.Locale;
import java.util.Set;
import android.content.Intent;
import android.app.AlertDialog;
import android.os.Bundle;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.widget.PopupMenu;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ImageView;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;
import android.net.Uri;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import android.util.Base64;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.io.File;
import java.io.FileOutputStream;
import androidx.core.content.FileProvider;

public class MainActivity extends Activity {

    private static final String API_URL =
            "https://eagleai-8p9b4.faable.link/api/sohbet";

    private static final String MEMORY_URL =
            "https://eagleai-8p9b4.faable.link/api/hafiza";

    private LinearLayout mesajAlani;
    private EditText mesajKutusu;
    private Uri secilenDosyaUri;
    private LinearLayout onizlemeAlani;
    private ImageView onizlemeResmi;
    private ScrollView kaydirma;

    private final List<JSONObject> gecmis = new ArrayList<>();

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

    private final ExecutorService gorselExecutor =
            Executors.newSingleThreadExecutor();

    private long sonMesajZamani = 0;

    private TextToSpeech konusmaMotoru;
    private boolean sesAcik = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        // EagleAI koyu tema sistem çubukları
        getWindow().setStatusBarColor(Color.rgb(8, 16, 29));
        getWindow().setNavigationBarColor(Color.rgb(8, 16, 29));
        getWindow().getDecorView().setSystemUiVisibility(
                getWindow().getDecorView().getSystemUiVisibility()
                        & ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                        & ~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        );

        arayuzOlustur();
        sesMotoruBaslat();
    }

    private void arayuzOlustur() {

        LinearLayout ana = new LinearLayout(this);
        ana.setOrientation(LinearLayout.VERTICAL);
        ana.setBackgroundColor(Color.rgb(8, 16, 29));

          // ===== MODERN EAGLE-AI ÜST BAŞLIK =====
        LinearLayout ustBar = new LinearLayout(this);
        ustBar.setOrientation(LinearLayout.HORIZONTAL);
        ustBar.setGravity(Gravity.CENTER_VERTICAL);
        ustBar.setPadding(10, 10, 12, 10);
        ustBar.setBackground(yuvarlakArkaPlan(
                Color.rgb(3, 25, 40),
                Color.rgb(0, 115, 135),
                0
        ));

        Button menuBtn = new Button(this);
        menuBtn.setText("☰");
        menuBtn.setTextSize(25);
        menuBtn.setTextColor(Color.WHITE);
        menuBtn.setAllCaps(false);
        menuBtn.setGravity(Gravity.CENTER);
        menuBtn.setPadding(0, 0, 0, 0);
        menuBtn.setBackground(yuvarlakArkaPlan(
                Color.rgb(10, 47, 65),
                Color.rgb(0, 160, 180),
                24
        ));

        ustBar.addView(menuBtn, new LinearLayout.LayoutParams(48, 48));

        TextView kartalLogo = new TextView(this);
        kartalLogo.setText("🦅");
        kartalLogo.setTextSize(40);
        kartalLogo.setGravity(Gravity.CENTER);
        kartalLogo.setShadowLayer(
                8f, 0f, 0f, Color.rgb(0, 190, 210)
        );

        LinearLayout.LayoutParams logoLp =
                new LinearLayout.LayoutParams(52, 56);
        logoLp.setMargins(8, 0, 4, 0);
        ustBar.addView(kartalLogo, logoLp);

        LinearLayout baslikAlani = new LinearLayout(this);
        baslikAlani.setOrientation(LinearLayout.VERTICAL);
        baslikAlani.setGravity(Gravity.CENTER_VERTICAL);

        TextView baslik = new TextView(this);
        baslik.setText("EAGLE-AI");
        baslik.setTextSize(23);
        baslik.setTypeface(
                Typeface.create("sans-serif", Typeface.BOLD)
        );
        baslik.setTextColor(Color.WHITE);

        TextView altBaslik = new TextView(this);
        altBaslik.setText("Her zaman yanınızda...");
        altBaslik.setTextSize(11);
        altBaslik.setTextColor(Color.rgb(130, 205, 215));

        baslikAlani.addView(baslik);
        baslikAlani.addView(altBaslik);

        ustBar.addView(
                baslikAlani,
                new LinearLayout.LayoutParams(
                        0,
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        1
                )
        );

        Button sesBtn = new Button(this);
        sesBtn.setText(sesAcik ? "🔊" : "🔇");
        sesBtn.setTextSize(19);
        sesBtn.setTextColor(Color.WHITE);
        sesBtn.setAllCaps(false);
        sesBtn.setPadding(0, 0, 0, 0);
        sesBtn.setBackground(yuvarlakArkaPlan(
                Color.rgb(10, 47, 65),
                Color.rgb(0, 160, 180),
                24
        ));

        ustBar.addView(sesBtn, new LinearLayout.LayoutParams(46, 46));

        sesBtn.setOnClickListener(v -> {
            sesAcik = !sesAcik;

            if (!sesAcik && konusmaMotoru != null) {
                konusmaMotoru.stop();
            }

            sesBtn.setText(sesAcik ? "🔊" : "🔇");

            Toast.makeText(
                    this,
                    sesAcik ? "🔊 Sesli cevap açık" : "🔇 Sesli cevap kapalı",
                    Toast.LENGTH_SHORT
            ).show();
        });

        ana.addView(ustBar);

        kaydirma = new ScrollView(this);

        mesajAlani = new LinearLayout(this);
        mesajAlani.setOrientation(LinearLayout.VERTICAL);
        mesajAlani.setPadding(16, 16, 16, 16);

        mesajAlani.addView(mesajOlustur(
                "🦅 Özhan, hoş geldin!\n" +
                "Nasıl yardımcı olabilirim?"
        ));

        gecmisiYukle();

        kaydirma.addView(mesajAlani);

        ana.addView(
                kaydirma,
                new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        0,
                        1
                )
        );

        // ===== MODERN EAGLE-AI MESAJ KUTUSU =====

        LinearLayout alt = new LinearLayout(this);
        alt.setOrientation(LinearLayout.HORIZONTAL);
        alt.setGravity(Gravity.CENTER_VERTICAL);
        alt.setPadding(8, 7, 8, 7);
        alt.setBackground(yuvarlakArkaPlan(
                Color.rgb(8, 25, 40),
                Color.rgb(0, 125, 145),
                24
        ));
        alt.setElevation(8f);

        // 📎 Dosya butonu
          // 📎 DOSYA BUTONU
          Button dosya = new Button(this);
          dosya.setText("+");
          dosya.setTextSize(24);
          dosya.setTextColor(Color.WHITE);
          dosya.setAllCaps(false);
          dosya.setGravity(Gravity.CENTER);
          dosya.setBackground(yuvarlakArkaPlan(Color.rgb(30, 57, 70), Color.rgb(65, 111, 124), 18));
          dosya.setPadding(0, 0, 0, 0);

          LinearLayout.LayoutParams dosyaLp =
                  new LinearLayout.LayoutParams(46, 46);
          dosyaLp.setMargins(0, 0, 6, 0);

          alt.addView(dosya, dosyaLp);

        // ✍️ Mesaj yazma alanı
        mesajKutusu = new EditText(this);
        mesajKutusu.setHint("Mesajını yaz...");
        mesajKutusu.setTextSize(16);
        mesajKutusu.setSingleLine(false);
        mesajKutusu.setMinLines(1);
        mesajKutusu.setMaxLines(30);
        mesajKutusu.setGravity(Gravity.TOP | Gravity.START);
        mesajKutusu.setPadding(14, 10, 14, 10);
        mesajKutusu.setTextColor(Color.WHITE);
        mesajKutusu.setHintTextColor(Color.rgb(166, 190, 198));
        mesajKutusu.setBackground(yuvarlakArkaPlan(
                Color.rgb(18, 39, 55),
                Color.rgb(43, 83, 99),
                20
        ));
        mesajKutusu.setVerticalScrollBarEnabled(false);
        mesajKutusu.setHorizontallyScrolling(false);
        mesajKutusu.setScrollBarStyle(View.SCROLLBARS_INSIDE_INSET);
        mesajKutusu.setInputType(
                android.text.InputType.TYPE_CLASS_TEXT |
                android.text.InputType.TYPE_TEXT_FLAG_MULTI_LINE |
                android.text.InputType.TYPE_TEXT_FLAG_CAP_SENTENCES
        );

        LinearLayout.LayoutParams mesajLp =
                new LinearLayout.LayoutParams(
                        0,
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        1
                );

        mesajLp.setMargins(4, 0, 6, 0);



        alt.addView(mesajKutusu, mesajLp);

        // 🎤 Mikrofon butonu
        Button mikrofon = new Button(this);
        mikrofon.setText("🎤");
        mikrofon.setTextSize(22);
        mikrofon.setTextColor(Color.WHITE);
        mikrofon.setAllCaps(false);
        mikrofon.setGravity(Gravity.CENTER);
        mikrofon.setBackground(yuvarlakArkaPlan(Color.rgb(30, 57, 70), Color.rgb(65, 111, 124), 18));
        mikrofon.setPadding(0, 0, 0, 0);

        LinearLayout.LayoutParams mikrofonLp =
                new LinearLayout.LayoutParams(46, 46);
        mikrofonLp.setMargins(0, 0, 6, 0);

        alt.addView(mikrofon, mikrofonLp);

        // ➤ Gönder butonu
        Button gonder = new Button(this);
        gonder.setText("▲");
        gonder.setTextSize(22);
        gonder.setTextColor(Color.WHITE);
        gonder.setAllCaps(false);
        gonder.setGravity(Gravity.CENTER);
        gonder.setPadding(0, 0, 0, 0);
        gonder.setBackground(yuvarlakArkaPlan(Color.rgb(0, 184, 190), Color.rgb(100, 224, 220), 18));

        LinearLayout.LayoutParams gonderLp =
                new LinearLayout.LayoutParams(48, 48);

        alt.addView(gonder, gonderLp);


        // 🖼️ RESİM ÖNİZLEME ÇUBUĞU (gönderilmeden önce)
        onizlemeAlani = new LinearLayout(this);
        onizlemeAlani.setOrientation(LinearLayout.HORIZONTAL);
        onizlemeAlani.setGravity(Gravity.CENTER_VERTICAL);
        onizlemeAlani.setPadding(12, 8, 12, 8);
        onizlemeAlani.setBackground(yuvarlakArkaPlan(Color.rgb(24, 43, 61), Color.rgb(55, 91, 105), 16));
        onizlemeAlani.setVisibility(View.GONE);

        onizlemeResmi = new ImageView(this);
        onizlemeResmi.setScaleType(ImageView.ScaleType.CENTER_CROP);
        LinearLayout.LayoutParams onizlemeResimLp =
                new LinearLayout.LayoutParams(70, 70);
        onizlemeResimLp.setMargins(0, 0, 12, 0);
        onizlemeAlani.addView(onizlemeResmi, onizlemeResimLp);

        TextView onizlemeYazi = new TextView(this);
        onizlemeYazi.setText("📷 Fotoğraf eklendi");
        onizlemeYazi.setTextColor(Color.rgb(232, 244, 246));
        LinearLayout.LayoutParams onizlemeYaziLp =
                new LinearLayout.LayoutParams(
                        0,
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        1
                );
        onizlemeAlani.addView(onizlemeYazi, onizlemeYaziLp);

        Button onizlemeKaldir = new Button(this);
        onizlemeKaldir.setText("✕");
        onizlemeKaldir.setTextColor(Color.WHITE);
        onizlemeKaldir.setBackground(yuvarlakArkaPlan(Color.rgb(145, 61, 69), Color.rgb(190, 105, 110), 14));
        onizlemeKaldir.setAllCaps(false);
        LinearLayout.LayoutParams onizlemeKaldirLp =
                new LinearLayout.LayoutParams(48, 48);
        onizlemeKaldir.setOnClickListener(v -> {
            secilenDosyaUri = null;
            onizlemeAlani.setVisibility(View.GONE);
        });
        onizlemeAlani.addView(onizlemeKaldir, onizlemeKaldirLp);

        ana.addView(onizlemeAlani);

        ana.addView(alt);

        dosya.setOnClickListener(v -> dosyaSec());

        mikrofon.setOnClickListener(v -> sesiMetneCevir());

        gonder.setOnClickListener(v -> mesajGonder());

        menuBtn.setOnClickListener(v -> {
            PopupMenu popup = new PopupMenu(this, menuBtn);
            popup.getMenu().add("🧠 Hafıza");
            popup.getMenu().add("➕ Hafızaya Ekle");
            popup.getMenu().add("🗑️ Hafızadan Çıkar");
            popup.getMenu().add("❓ Yardım");
            popup.getMenu().add("🆕 Yeni");
              popup.getMenu().add("🕘 Son Sohbetler");
            popup.getMenu().add("🗑️ Temizle");
            popup.getMenu().add("🔊 Ses Seç");
            popup.getMenu().add(sesAcik ? "🔇 Sesi Kapat" : "🔊 Sesi Aç");

            popup.setOnMenuItemClickListener(item -> {
                String secim = item.getTitle().toString();

                if (secim.equals("🧠 Hafıza")) {
                    yerelMesajEkle("🧠 Eagle-AI hafızası yükleniyor...");

                    executor.execute(() -> {
                        String sonuc = hafizaIstek();
                        final String cevapFinal = sonuc;

                        runOnUiThread(() -> {
                            mesajAlani.addView(
                                    mesajOlustur(
                                            "🧠 EAGLE-AI HAFIZA\n\n" +
                                            cevapFinal
                                    )
                            );

                            kaydirma.post(() ->
                                    kaydirma.fullScroll(View.FOCUS_DOWN)
                            );
                        });
                    });
                } else if (secim.equals("➕ Hafızaya Ekle")) {
                    hafizayaEkleDialogGoster();
                } else if (secim.equals("🗑️ Hafızadan Çıkar")) {
                    hafizadanCikarDialogGoster();
                } else if (secim.contains("Yardım")) {
                    yerelMesajEkle(
                            "❓ YARDIM\n\n" +
                            "• Normal soru sor\n" +
                            "• Kod iste\n" +
                            "• Hata çıktısı gönder\n" +
                            "• Termux komutu iste\n\n" +
                            "Eagle-AI mümkün olduğunca doğrudan çalışabilir çözüm üretir."
                    );
                } else if (secim.contains("Son Sohbetler")) {
                      startActivity(new Intent(this, SohbetlerActivity.class));
                  } else if (secim.contains("Yeni")) {
                      yeniSohbet();
                  } else if (secim.contains("Temizle")) {
                      gecmisiTemizle();
                } else if (secim.contains("Ses Seç")) {
                    sesSecimMenusuGoster();
                } else if (secim.contains("Sesi Kapat") || secim.contains("Sesi Aç")) {
                    sesAcik = !sesAcik;
                    if (!sesAcik && konusmaMotoru != null) {
                        konusmaMotoru.stop();
                    }
                    Toast.makeText(
                            this,
                            sesAcik ? "🔊 Sesli cevap açık" : "🔇 Sesli cevap kapalı",
                            Toast.LENGTH_SHORT
                    ).show();
                }

                return true;
            });

            popup.show();
        });

        setContentView(ana);
    }

    private void mesajGonder() {
        android.util.Log.d("EAGLE_MIC", "mesajGonder() çağrıldı");

        final String mesaj =
                mesajKutusu.getText().toString().trim();

        if (mesaj.isEmpty() && secilenDosyaUri == null) {
            return;
        }

        sonMesajZamani = System.currentTimeMillis();

        LinearLayout kullaniciMesaji = mesajOlustur("Sen: " + mesaj);

        if (secilenDosyaUri != null) {
            try {
                ImageView gonderilenResim = new ImageView(this);
                gonderilenResim.setImageURI(secilenDosyaUri);
                gonderilenResim.setAdjustViewBounds(true);
                gonderilenResim.setScaleType(ImageView.ScaleType.FIT_CENTER);

                int resimYukseklik = (int) (
                        240 * getResources().getDisplayMetrics().density
                );

                LinearLayout.LayoutParams resimLp =
                        new LinearLayout.LayoutParams(
                                LinearLayout.LayoutParams.MATCH_PARENT,
                                resimYukseklik
                        );

                resimLp.setMargins(0, 0, 0, 12);
                kullaniciMesaji.addView(gonderilenResim, 0, resimLp);

            } catch (Exception exc) {
                android.util.Log.e(
                        "EAGLE_IMAGE",
                        "Mesaj resmi gösterilemedi: " + exc.getMessage()
                );
            }
        }

        mesajAlani.addView(kullaniciMesaji);
        final Uri gonderilecekResim = secilenDosyaUri;
        secilenDosyaUri = null;
        onizlemeAlani.setVisibility(View.GONE);
        gecmiseKaydet("Sen: " + mesaj);
          sohbeteMesajEkle("Sen: " + mesaj);
        mesajKutusu.setText("");

        final LinearLayout durum = mesajOlustur(
                "🤖 Eagle-AI düşünüyor..."
        );

        mesajAlani.addView(durum);

        kaydirma.post(() ->
                kaydirma.fullScroll(View.FOCUS_DOWN)
        );

        executor.execute(() -> {
            String sonucCevap = geminiIstek(mesaj, gonderilecekResim);

            if (sonucCevap == null) {
                sonucCevap =
                        "❌ Eagle-AI API bağlantısı kurulamadı.\n\n" +
                        "Telefonun aynı Wi-Fi ağında olduğundan " +
                        "ve Termux'taki eagle_api.py sunucusunun çalıştığından emin ol.";
            }

            final String cevapFinal = sonucCevap;

            runOnUiThread(() -> {
                mesajAlani.removeView(durum);

                LinearLayout cevapKarti =
                        mesajOlustur("🦅\n\n" + cevapFinal);
                mesajAlani.addView(cevapKarti);

                if (gonderilecekResim == null
                        && gorselAramasiUygunMu(mesaj, cevapFinal)) {
                    commonsGorselleriEkle(cevapKarti, mesaj);
                }
                gecmiseKaydet("🦅\n\n" + cevapFinal);
                  sohbeteMesajEkle("🦅\n\n" + cevapFinal);
                metniSesliOku(cevapFinal);

                kaydirma.post(() ->
                        kaydirma.fullScroll(View.FOCUS_DOWN)
                );
            });
        });
    }

    private void hafizayaEkleDialogGoster() {
        EditText giris = new EditText(this);
        giris.setHint("Hafızaya eklenecek bilgi");
        giris.setSingleLine(false);

        new AlertDialog.Builder(this)
                .setTitle("➕ Hafızaya Ekle")
                .setView(giris)
                .setNegativeButton("İptal", null)
                .setPositiveButton("Ekle", (dialog, which) -> {
                    String bilgi = giris.getText().toString().trim();

                    if (bilgi.isEmpty()) {
                        Toast.makeText(this, "Hafıza bilgisi boş olamaz.", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    executor.execute(() -> {
                        String sonuc = hafizaDegistirIstek(MEMORY_URL, bilgi);

                        runOnUiThread(() -> {
                            yerelMesajEkle(sonuc);
                            kaydirma.post(() ->
                                    kaydirma.fullScroll(View.FOCUS_DOWN)
                            );
                        });
                    });
                })
                .show();
    }

    private void hafizadanCikarDialogGoster() {
        EditText giris = new EditText(this);
        giris.setHint("Silinecek hafıza kaydını aynen yaz");
        giris.setSingleLine(false);

        new AlertDialog.Builder(this)
                .setTitle("🗑️ Hafızadan Çıkar")
                .setView(giris)
                .setNegativeButton("İptal", null)
                .setPositiveButton("Çıkar", (dialog, which) -> {
                    String bilgi = giris.getText().toString().trim();

                    if (bilgi.isEmpty()) {
                        Toast.makeText(this, "Silinecek bilgi boş olamaz.", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    executor.execute(() -> {
                        String sonuc = hafizaDegistirIstek(
                                MEMORY_URL + "/sil",
                                bilgi
                        );

                        runOnUiThread(() -> {
                            yerelMesajEkle(sonuc);
                            kaydirma.post(() ->
                                    kaydirma.fullScroll(View.FOCUS_DOWN)
                            );
                        });
                    });
                })
                .show();
    }

    private String hafizaDegistirIstek(String adres, String bilgi) {
        HttpURLConnection baglanti = null;

        try {
            URL url = new URL(adres);
            baglanti = (HttpURLConnection) url.openConnection();
            baglanti.setRequestMethod("POST");
            baglanti.setConnectTimeout(10000);
            baglanti.setReadTimeout(15000);
            baglanti.setDoOutput(true);
            baglanti.setRequestProperty("Content-Type", "application/json; charset=UTF-8");

            JSONObject veri = new JSONObject();
            veri.put("memory", bilgi);

            byte[] veriBytes =
                    veri.toString().getBytes(StandardCharsets.UTF_8);

            OutputStream cikti = baglanti.getOutputStream();
            cikti.write(veriBytes);
            cikti.flush();
            cikti.close();

            int kod = baglanti.getResponseCode();

            InputStream akis =
                    kod >= 200 && kod < 300
                            ? baglanti.getInputStream()
                            : baglanti.getErrorStream();

            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(akis, StandardCharsets.UTF_8)
            );

            StringBuilder sonuc = new StringBuilder();
            String satir;

            while ((satir = reader.readLine()) != null) {
                sonuc.append(satir);
            }

            reader.close();

            JSONObject json = new JSONObject(sonuc.toString());

            if (kod >= 200 && kod < 300 && json.optBoolean("ok", false)) {
                if (json.optBoolean("added", false)) {
                    return "🧠 Hafızaya eklendi.";
                }

                if (json.optBoolean("removed", false)) {
                    return "🗑️ Hafızadan çıkarıldı.";
                }

                return json.optString(
                        "message",
                        "🧠 İşlem tamamlandı."
                );
            }

            return "❌ Hafıza işlemi başarısız: " +
                    json.optString("error", "Bilinmeyen hata.");

        } catch (Exception e) {
            return "Bağlantı hatası: " + e.getMessage();
        } finally {
            if (baglanti != null) {
                baglanti.disconnect();
            }
        }
    }

    private String hafizaIstek() {
        HttpURLConnection baglanti = null;

        try {
            URL url = new URL(MEMORY_URL);

            baglanti = (HttpURLConnection) url.openConnection();
            baglanti.setRequestMethod("GET");
            baglanti.setConnectTimeout(10000);
            baglanti.setReadTimeout(15000);

            int kod = baglanti.getResponseCode();

            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(
                            kod >= 200 && kod < 300
                                    ? baglanti.getInputStream()
                                    : baglanti.getErrorStream(),
                            StandardCharsets.UTF_8
                    )
            );

            StringBuilder sonuc = new StringBuilder();
            String satir;

            while ((satir = reader.readLine()) != null) {
                sonuc.append(satir);
            }

            reader.close();

            JSONObject json = new JSONObject(sonuc.toString());

            if (kod >= 200 &&
                    kod < 300 &&
                    json.optBoolean("ok", false)) {

                JSONObject memory =
                        json.optJSONObject("memory");

                if (memory == null) {
                    return "Hafıza şu anda boş.";
                }

                JSONArray kullanici =
                        memory.optJSONArray("kullanici");

                if (kullanici == null || kullanici.length() == 0) {
                    return "Kullanıcı hafızası şu anda boş.";
                }

                StringBuilder metin =
                        new StringBuilder();

                for (int i = 0; i < kullanici.length(); i++) {
                    metin.append("• ")
                         .append(kullanici.optString(i))
                         .append("\n");
                }

                return metin.toString().trim();
            }

            return "❌ Hafıza API hatası: " +
                    json.optString(
                            "error",
                            "Bilinmeyen hata."
                    );

        } catch (Exception e) {

              return "Bağlantı hatası: " +
                      e.getClass().getSimpleName();


        } finally {

            if (baglanti != null) {
                baglanti.disconnect();
            }
        }
    }

    private String dosyaBase64(Uri uri) {
        if (uri == null) {
            return null;
        }

        try {
            InputStream inputStream =
                    getContentResolver().openInputStream(uri);

            if (inputStream == null) {
                return null;
            }

            java.io.ByteArrayOutputStream buffer =
                    new java.io.ByteArrayOutputStream();

            byte[] parca = new byte[8192];
            int okunan;

            while ((okunan = inputStream.read(parca)) != -1) {
                buffer.write(parca, 0, okunan);
            }

            inputStream.close();

            return Base64.encodeToString(
                    buffer.toByteArray(),
                    Base64.NO_WRAP
            );

        } catch (Exception e) {
            return null;
        }
    }


    private double paraDegeriniOku(String metin) {
        String s = metin.trim().replace(" ", "");

        if (s.contains(",") && s.contains(".")) {
            if (s.lastIndexOf(',') > s.lastIndexOf('.')) {
                s = s.replace(".", "").replace(",", ".");
            } else {
                s = s.replace(",", "");
            }
        } else if (s.contains(",")) {
            s = s.replace(",", ".");
        } else if (s.contains(".")) {
            String[] parcalar = s.split("\\.", -1);
            if (parcalar.length == 2 && parcalar[1].length() <= 2) {
                // 12.50 -> 12.50
            } else {
                // 2.834 -> 2.834
                // Noktayı ondalık kabul ediyoruz.
            }
        }

        return Double.parseDouble(s);
    }









    private String geminiIstek(String mesaj, Uri resimUri) {

        HttpURLConnection baglanti = null;

        try {

              android.util.Log.d("EAGLE_NET", "API bağlantısı başlıyor: " + API_URL);
            URL url = new URL(API_URL);

            baglanti =
                    (HttpURLConnection) url.openConnection();
              android.util.Log.d("EAGLE_NET", "HttpURLConnection oluşturuldu");

            baglanti.setRequestMethod("POST");
            baglanti.setConnectTimeout(10000);
            baglanti.setReadTimeout(60000);
            baglanti.setDoOutput(true);
            baglanti.setRequestProperty(
                    "Content-Type",
                    "application/json; charset=UTF-8"
            );

            JSONArray history = new JSONArray();

            int baslangic =
                    Math.max(0, gecmis.size() - 20);

            for (int i = baslangic;
                 i < gecmis.size();
                 i++) {

                JSONObject item = gecmis.get(i);

                JSONObject h = new JSONObject();

                h.put("role", item.getString("role"));
                h.put("text", item.getString("text"));

                history.put(h);
            }

            JSONObject body = new JSONObject();

            body.put("message", mesaj);
            body.put("history", history);

            // 📎 Seçilen dosyayı API'ye gönder
            if (resimUri != null) {
                String dosya64 = dosyaBase64(resimUri);
                String mime = getContentResolver()
                        .getType(resimUri);

                if (dosya64 != null) {
                    body.put("file_base64", dosya64);
                    body.put(
                            "file_mime",
                            mime != null
                                    ? mime
                                    : "application/octet-stream"
                    );
                }
            }

            byte[] veri =
                    body.toString()
                            .getBytes(StandardCharsets.UTF_8);

            OutputStream output =
                    baglanti.getOutputStream();
              android.util.Log.d("EAGLE_NET", "OutputStream alındı");

            output.write(veri);
            output.flush();
            output.close();

            int kod = baglanti.getResponseCode();
              android.util.Log.d("EAGLE_NET", "HTTP cevap kodu alındı: " + kod);

            BufferedReader reader;

            if (kod >= 200 && kod < 300) {

                reader = new BufferedReader(
                        new InputStreamReader(
                                baglanti.getInputStream(),
                                StandardCharsets.UTF_8
                        )
                );

            } else {

                reader = new BufferedReader(
                        new InputStreamReader(
                                baglanti.getErrorStream(),
                                StandardCharsets.UTF_8
                        )
                );
            }

            StringBuilder sonuc =
                    new StringBuilder();

            String satir;

            while ((satir = reader.readLine()) != null) {
                sonuc.append(satir);
            }

            reader.close();

            JSONObject cevapJson =
                    new JSONObject(sonuc.toString());

            if (kod >= 200 &&
                    kod < 300 &&
                    cevapJson.optBoolean("ok", false)) {

                String cevap =
                        cevapJson.optString(
                                "answer",
                                "Eagle-AI cevap vermedi."
                        );

                JSONObject userMessage =
                        new JSONObject();

                userMessage.put("role", "user");
                userMessage.put("text", mesaj);

                JSONObject modelMessage =
                        new JSONObject();

                modelMessage.put("role", "model");
                modelMessage.put("text", cevap);

                synchronized (gecmis) {
                    gecmis.add(userMessage);
                    gecmis.add(modelMessage);
                }

                return cevap;
            }

            return "API hatası: " +
                    cevapJson.optString(
                            "error",
                            "Bilinmeyen hata."
                    );

        } catch (Exception e) {

            android.util.Log.e(
                    "EAGLE_NET",
                    "AĞ HATASI: " + e.getClass().getSimpleName() +
                    " | " + String.valueOf(e.getMessage()),
                    e
            );

            return "Bağlantı hatası: " +
                    e.getClass().getSimpleName();

        } finally {

            if (baglanti != null) {
                baglanti.disconnect();
            }
        }
    }

    private void yerelMesajEkle(String mesaj) {

        mesajAlani.addView(mesajOlustur(mesaj));

        kaydirma.post(() ->
                kaydirma.fullScroll(View.FOCUS_DOWN)
        );
    }

    private static final String SOHBET_PREF = "eagle_sohbetler";
    private static final String SOHBET_KEY = "sohbetler";
    private static String aktifSohbetId = null;

    private static final String GECMIS_PREF = "eagle_gecmis";
    private static final String GECMIS_KEY = "mesajlar";

    private void gecmiseKaydet(String metin) {
        try {
            SharedPreferences sp = getSharedPreferences(GECMIS_PREF, MODE_PRIVATE);
            String mevcut = sp.getString(GECMIS_KEY, "[]");
            JSONArray dizi = new JSONArray(mevcut);
            dizi.put(metin);
            sp.edit().putString(GECMIS_KEY, dizi.toString()).apply();
        } catch (Exception e) {
            // Kaydedilemezse sessizce geç, sohbeti bozmasın.
        }
    }

    private void gecmisiYukle() {
        try {
            SharedPreferences sp = getSharedPreferences(GECMIS_PREF, MODE_PRIVATE);
            String mevcut = sp.getString(GECMIS_KEY, "[]");
            JSONArray dizi = new JSONArray(mevcut);

            for (int i = 0; i < dizi.length(); i++) {
                String metin = dizi.getString(i);
                mesajAlani.addView(mesajOlustur(metin));
            }
        } catch (Exception e) {
            // Yüklenemezse sessizce geç.
        }
    }

    private void gecmisiTemizle() {
        SharedPreferences sp = getSharedPreferences(GECMIS_PREF, MODE_PRIVATE);
        sp.edit().putString(GECMIS_KEY, "[]").apply();
        mesajAlani.removeAllViews();
        mesajAlani.addView(mesajOlustur(
                "🦅 Özhan, hoş geldin!\n" +
                "Nasıl yardımcı olabilirim?"
        ));
    }


      private void sonSohbetleriGoster() {
          try {
              SharedPreferences sp = getSharedPreferences(SOHBET_PREF, MODE_PRIVATE);
              String mevcut = sp.getString(SOHBET_KEY, "[]");
              JSONArray sohbetler = new JSONArray(mevcut);

              LinearLayout liste = new LinearLayout(this);
              liste.setOrientation(LinearLayout.VERTICAL);
              int padding = 24;
              liste.setPadding(padding, padding, padding, padding);

              if (sohbetler.length() == 0) {
                  TextView bos = new TextView(this);
                  bos.setText("🕘 Henüz kayıtlı sohbet yok.");
                  bos.setTextSize(17);
                  bos.setPadding(12, 20, 12, 20);
                  liste.addView(bos);
              } else {
                  for (int i = 0; i < sohbetler.length(); i++) {
                      JSONObject sohbet = sohbetler.getJSONObject(i);

                      String id = sohbet.optString("id", "");
                      String baslik = sohbet.optString("baslik", "Yeni Sohbet");
                      String tarih = sohbet.optString("tarih", "");

                      TextView satir = new TextView(this);
                      satir.setText("💬 " + baslik + "\n🕒 " + tarih);
                      satir.setTextSize(16);
                      satir.setPadding(16, 20, 16, 20);

                      satir.setOnClickListener(v -> sohbetYukle(id));

                      satir.setOnLongClickListener(v -> {
                          sohbetSilOnayi(id, baslik);
                          return true;
                      });

                      liste.addView(satir);

                      View ayirici = new View(this);
                      ayirici.setLayoutParams(new LinearLayout.LayoutParams(
                              LinearLayout.LayoutParams.MATCH_PARENT, 1
                      ));
                      liste.addView(ayirici);
                  }
              }

              AlertDialog dialog = new AlertDialog.Builder(this)
                      .setTitle("🕘 Son Sohbetler")
                      .setView(liste)
                      .setPositiveButton("Kapat", null)
                      .create();

              dialog.show();

          } catch (Exception e) {
              Toast.makeText(
                      this,
                      "Sohbetler yüklenemedi.",
                      Toast.LENGTH_SHORT
              ).show();
          }
      }

              private void yeniSohbet() {
            aktifSohbetId = null;
            mesajAlani.removeAllViews();

            mesajAlani.addView(
                    mesajOlustur(
                            "🦅 Özhan, hoş geldin!\n" +
                            "Nasıl yardımcı olabilirim?"
                    )
            );
        }

private void sohbetYukle(String id) {
        try {
            SharedPreferences sp = getSharedPreferences(SOHBET_PREF, MODE_PRIVATE);
            String mevcut = sp.getString(SOHBET_KEY, "[]");
            JSONArray sohbetler = new JSONArray(mevcut);

            for (int i = 0; i < sohbetler.length(); i++) {
                JSONObject sohbet = sohbetler.getJSONObject(i);

                if (id.equals(sohbet.optString("id", ""))) {
                    aktifSohbetId = id;

                    mesajAlani.removeAllViews();

                    JSONArray mesajlar = sohbet.optJSONArray("mesajlar");

                    if (mesajlar != null) {
                        for (int j = 0; j < mesajlar.length(); j++) {
                            mesajAlani.addView(
                                    mesajOlustur(mesajlar.getString(j))
                            );
                        }
                    }

                    kaydirma.post(() ->
                            kaydirma.fullScroll(View.FOCUS_DOWN)
                    );

                    Toast.makeText(
                            this,
                            "💬 Sohbet açıldı",
                            Toast.LENGTH_SHORT
                    ).show();

                    break;
                }
            }

        } catch (Exception e) {
            Toast.makeText(
                    this,
                    "Sohbet açılamadı.",
                    Toast.LENGTH_SHORT
            ).show();
        }
    }

    private void sohbetSilOnayi(String id, String baslik) {
          new AlertDialog.Builder(this)
                  .setTitle("🗑️ Sohbeti Sil")
                  .setMessage(
                          "Bu sohbet silinsin mi?\n\n" +
                          baslik
                  )
                  .setNegativeButton("Vazgeç", null)
                  .setPositiveButton("Sil", (dialog, which) -> sohbetSil(id))
                  .show();
      }

      private void sohbetSil(String id) {
          try {
              SharedPreferences sp = getSharedPreferences(SOHBET_PREF, MODE_PRIVATE);
              String mevcut = sp.getString(SOHBET_KEY, "[]");
              JSONArray eski = new JSONArray(mevcut);
              JSONArray yeni = new JSONArray();

              for (int i = 0; i < eski.length(); i++) {
                  JSONObject sohbet = eski.getJSONObject(i);

                  if (!id.equals(sohbet.optString("id", ""))) {
                      yeni.put(sohbet);
                  }
              }

              sp.edit()
                      .putString(SOHBET_KEY, yeni.toString())
                      .apply();

              if (id.equals(aktifSohbetId)) {
                  aktifSohbetId = null;
              }

              Toast.makeText(
                      this,
                      "🗑️ Sohbet silindi",
                      Toast.LENGTH_SHORT
              ).show();

          } catch (Exception e) {
              Toast.makeText(
                      this,
                      "Sohbet silinemedi.",
                      Toast.LENGTH_SHORT
              ).show();
          }
      }

    private void sohbeteMesajEkle(String metin) {
        try {
            SharedPreferences sp = getSharedPreferences(SOHBET_PREF, MODE_PRIVATE);
            String mevcut = sp.getString(SOHBET_KEY, "[]");
            JSONArray sohbetler = new JSONArray(mevcut);

            if (aktifSohbetId == null) {
                String id = String.valueOf(System.currentTimeMillis());

                String baslik = metin;
                if (baslik.startsWith("Sen: ")) {
                    baslik = baslik.substring(5).trim();
                }

                if (baslik.length() > 45) {
                    baslik = baslik.substring(0, 45) + "...";
                }

                JSONObject sohbet = new JSONObject();
                sohbet.put("id", id);
                sohbet.put("baslik", baslik);
                sohbet.put(
                        "tarih",
                        new SimpleDateFormat(
                                "dd.MM.yyyy HH:mm",
                                java.util.Locale.getDefault()
                        ).format(new Date())
                );

                JSONArray mesajlar = new JSONArray();
                mesajlar.put(metin);
                sohbet.put("mesajlar", mesajlar);

                JSONArray yeniSohbetler = new JSONArray();
                yeniSohbetler.put(sohbet);

                for (int i = 0; i < sohbetler.length(); i++) {
                    yeniSohbetler.put(sohbetler.getJSONObject(i));
                }

                sp.edit()
                        .putString(SOHBET_KEY, yeniSohbetler.toString())
                        .apply();

                aktifSohbetId = id;

            } else {
                for (int i = 0; i < sohbetler.length(); i++) {
                    JSONObject sohbet = sohbetler.getJSONObject(i);

                    if (aktifSohbetId.equals(sohbet.optString("id", ""))) {
                        JSONArray mesajlar = sohbet.optJSONArray("mesajlar");

                        if (mesajlar == null) {
                            mesajlar = new JSONArray();
                            sohbet.put("mesajlar", mesajlar);
                        }

                        mesajlar.put(metin);

                        sohbet.put(
                                "tarih",
                                new SimpleDateFormat(
                                        "dd.MM.yyyy HH:mm",
                                        java.util.Locale.getDefault()
                                ).format(new Date())
                        );

                        break;
                    }
                }

                sp.edit()
                        .putString(SOHBET_KEY, sohbetler.toString())
                        .apply();
            }

        } catch (Exception e) {
            Toast.makeText(
                    this,
                    "Sohbet kaydedilemedi.",
                    Toast.LENGTH_SHORT
            ).show();
        }
    }

    private CharSequence renklendirKod(String kod) {
        SpannableStringBuilder styled = new SpannableStringBuilder(kod);
        Pattern tokenPattern = Pattern.compile(
                "#[^\n]*|\"(?:\\\\.|[^\"])*\"|'(?:\\\\.|[^'\\\\])*'|\\b\\d+(?:\\.\\d+)?\\b|\\b(def|return|if|else|elif|for|while|import|from|class|try|except|with|as|True|False|None)\\b"
        );
        Matcher tokenMatcher = tokenPattern.matcher(kod);
        while (tokenMatcher.find()) {
            String token = tokenMatcher.group();
            int color;
            if (token.startsWith("#")) {
                color = Color.rgb(132, 174, 151);
            } else if (token.startsWith("\"") || token.startsWith("'")) {
                color = Color.rgb(255, 184, 130);
            } else if (Character.isDigit(token.charAt(0))) {
                color = Color.rgb(76, 218, 218);
            } else {
                color = Color.rgb(157, 180, 255);
            }
            styled.setSpan(new ForegroundColorSpan(color), tokenMatcher.start(), tokenMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
        return styled;
    }

    private boolean sporCevabiMi(String metin) {
        String k = metin.toLowerCase(java.util.Locale.ROOT);

        boolean sporKelimesi =
                k.contains("futbol") ||
                k.contains("voleybol") ||
                k.contains("basketbol") ||
                k.contains("tenis") ||
                k.contains("maç") ||
                k.contains("mac") ||
                k.contains("lig") ||
                k.contains("şampiyona") ||
                k.contains("sampiyona") ||
                k.contains("turnuva") ||
                k.contains("yarı final") ||
                k.contains("yari final") ||
                k.contains("çeyrek final") ||
                k.contains("ceyrek final") ||
                k.contains("final") ||
                k.contains("set") ||
                k.contains("skor") ||
                k.contains("galibiyet") ||
                k.contains("kazandı") ||
                k.contains("kazandi") ||
                k.contains("yendi") ||
                k.contains("berabere");

        boolean skorVar =
                java.util.regex.Pattern.compile(
                        "\\b\\d{1,3}\\s*[-–]\\s*\\d{1,3}\\b"
                ).matcher(k).find();

        boolean eslesmeVar =
                java.util.regex.Pattern.compile(
                        "(?m)^\\s*(?:\\*\\s*)?\\*\\*[^*\\n]+?\\s+[-–]\\s+[^*\\n]+?\\*\\*"
                ).matcher(metin).find();

        return sporKelimesi || skorVar || eslesmeVar;
    }

    private CharSequence sporMetniRenklendir(String metin) {
        SpannableStringBuilder styled = new SpannableStringBuilder(metin);

        // Maç / set skorları: 3-1, 2–1, 25-22 vb.
        Pattern skorPattern = Pattern.compile(
                "\\b\\d{1,3}\\s*[-–]\\s*\\d{1,3}\\b"
        );
        Matcher skorMatcher = skorPattern.matcher(metin);

        while (skorMatcher.find()) {
            styled.setSpan(
                    new ForegroundColorSpan(Color.rgb(255, 125, 135)),
                    skorMatcher.start(),
                    skorMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
            styled.setSpan(
                    new StyleSpan(Typeface.BOLD),
                    skorMatcher.start(),
                    skorMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
        }

        // Tarih ve saat ifadeleri
        Pattern tarihPattern = Pattern.compile(
                "\\b(?:[0-3]?\\d[./-][0-1]?\\d(?:[./-]\\d{2,4})?|[0-3]?\\d\\s+(?:Ocak|Şubat|Mart|Nisan|Mayıs|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kasım|Aralık|Ocak|Subat|Mart|Nisan|Mayis|Haziran|Temmuz|Agustos|Eylul|Ekim|Kasim|Aralik)|(?:bugün|bugun|yarın|yarin|dün|dun)|\\b\\d{1,2}:\\d{2}\\b)"
        );
        Matcher tarihMatcher = tarihPattern.matcher(metin);

        while (tarihMatcher.find()) {
            styled.setSpan(
                    new ForegroundColorSpan(Color.rgb(90, 205, 235)),
                    tarihMatcher.start(),
                    tarihMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
            styled.setSpan(
                    new StyleSpan(Typeface.BOLD),
                    tarihMatcher.start(),
                    tarihMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
        }

        // Spor sonucunu anlatan güçlü ifadeler
        Pattern sonucPattern = Pattern.compile(
                "(?i)\\b(?:kazandı|kazandi|yendi|galip|galibiyet|maç sonucu|mac sonucu|sonuç|sonuc|skor|yarı final|yari final|çeyrek final|ceyrek final|final)\\b"
        );
        Matcher sonucMatcher = sonucPattern.matcher(metin);

        while (sonucMatcher.find()) {
            styled.setSpan(
                    new ForegroundColorSpan(Color.rgb(105, 220, 165)),
                    sonucMatcher.start(),
                    sonucMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
            styled.setSpan(
                    new StyleSpan(Typeface.BOLD),
                    sonucMatcher.start(),
                    sonucMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
            );
        }

        // Spor müsabakaları: takım veya oyuncu eşleşmelerini "Taraf A - Taraf B" biçiminde ayır
        Pattern sporPattern = Pattern.compile(
                "(?m)^(?:\\s*[\\*•-]\\s*)?\\*\\*([^*\\n]+?)\\s+[-–]\\s+([^*\\n]+?)\\*\\*(?=\\s*(?:\\(|-|$))"
        );
        Matcher sporMatcher = sporPattern.matcher(metin);

        while (sporMatcher.find()) {
            String spor1 = sporMatcher.group(1).trim();
            String spor2 = sporMatcher.group(2).trim();

            // Çok kısa/genel ifadeleri takım adı olarak boyama
            if (spor1.length() >= 3 && spor2.length() >= 3) {
                int spor1Baslangic = sporMatcher.start(1);
                int spor1Bitis = sporMatcher.end(1);
                int spor2Baslangic = sporMatcher.start(2);
                int spor2Bitis = sporMatcher.end(2);

                styled.setSpan(
                        new ForegroundColorSpan(Color.rgb(105, 205, 235)),
                        spor1Baslangic,
                        spor1Bitis,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                );
                styled.setSpan(
                        new StyleSpan(Typeface.BOLD),
                        spor1Baslangic,
                        spor1Bitis,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                );

                styled.setSpan(
                        new ForegroundColorSpan(Color.rgb(255, 145, 150)),
                        spor2Baslangic,
                        spor2Bitis,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                );
                styled.setSpan(
                        new StyleSpan(Typeface.BOLD),
                        spor2Baslangic,
                        spor2Bitis,
                        Spanned.SPAN_EXCLUSIVE_EXCLUSIVE
                );
            }
        }

        return styled;
    }

    private TextView normalMetinOlustur(String metin) {
        TextView tv = new TextView(this);

        String temizMetin = metin.trim();

        if (sporCevabiMi(temizMetin)) {
            tv.setText(sporMetniRenklendir(temizMetin));
        } else {
            tv.setText(temizMetin);
        }

        tv.setTextSize(16);
        tv.setTextColor(Color.rgb(231, 241, 245));
        tv.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));
        tv.setLineSpacing(2f, 1.05f);
        tv.setTextIsSelectable(true);
        return tv;
    }

    private void uzunMetinOlustur(LinearLayout kutu, String metin) {
        String temiz = metin.trim();

        if (temiz.length() <= 1200) {
            kutu.addView(normalMetinOlustur(temiz));
            return;
        }

        final int limit = 500;
        int kes = temiz.lastIndexOf(" ", limit);

        if (kes < 300) {
            kes = limit;
        }

        final String kisaMetin = temiz.substring(0, kes).trim();
        final String tamMetin = temiz;

        LinearLayout alan = new LinearLayout(this);
        alan.setOrientation(LinearLayout.VERTICAL);

        TextView metinTv = normalMetinOlustur(kisaMetin);

        TextView devamBtn = new TextView(this);
        devamBtn.setText("Daha fazlasını göster");
        devamBtn.setTextSize(14);
        devamBtn.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        devamBtn.setTextColor(Color.rgb(75, 218, 220));
        devamBtn.setGravity(Gravity.CENTER);
        devamBtn.setPadding(18, 12, 18, 12);

        GradientDrawable kenarlik = new GradientDrawable();
        kenarlik.setColor(Color.TRANSPARENT);
        kenarlik.setStroke(2, Color.rgb(0, 174, 185));
        kenarlik.setCornerRadius(24);
        devamBtn.setBackground(kenarlik);

        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        btnLp.gravity = Gravity.CENTER_HORIZONTAL;
        btnLp.setMargins(0, 12, 0, 4);
        devamBtn.setLayoutParams(btnLp);

        devamBtn.setOnClickListener(v -> {
            boolean acik = "Daha azını göster".contentEquals(devamBtn.getText());

            if (!acik) {
                metinTv.setText(tamMetin);
                devamBtn.setText("Daha azını göster");
            } else {
                metinTv.setText(kisaMetin);
                devamBtn.setText("Daha fazlasını göster");
            }
        });

        alan.addView(metinTv);
        alan.addView(devamBtn);
        kutu.addView(alan);
    }

    private LinearLayout kodKutusuOlustur(String kod) {
        final String kodTrim = kod.trim();

        LinearLayout disKutu = new LinearLayout(this);
        disKutu.setOrientation(LinearLayout.VERTICAL);
        disKutu.setBackgroundResource(R.drawable.kod_cercevesi);

        LinearLayout.LayoutParams disLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        disLp.setMargins(0, 12, 0, 12);
        disKutu.setLayoutParams(disLp);

        LinearLayout baslikSatiri = new LinearLayout(this);
        baslikSatiri.setOrientation(LinearLayout.HORIZONTAL);
        baslikSatiri.setGravity(Gravity.CENTER_VERTICAL);

        TextView dilEtiketi = new TextView(this);
        dilEtiketi.setText("Kod");
        dilEtiketi.setTextColor(Color.rgb(130, 190, 202));
        dilEtiketi.setTextSize(13);
        LinearLayout.LayoutParams dilLp = new LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1f
        );
        dilEtiketi.setLayoutParams(dilLp);

        TextView kopyalaBtn = new TextView(this);
        kopyalaBtn.setText("📋");
        kopyalaBtn.setTextSize(18);
        kopyalaBtn.setPadding(16, 8, 16, 8);
        kopyalaBtn.setOnClickListener(v -> {
            ClipboardManager clipboard =
                    (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            ClipData clip = ClipData.newPlainText("Eagle Kod", kodTrim);
            clipboard.setPrimaryClip(clip);
            Toast.makeText(this, "📋 Kod kopyalandı", Toast.LENGTH_SHORT).show();
        });

        TextView buyutBtn = new TextView(this);
        buyutBtn.setText("⤢");
        buyutBtn.setTextSize(18);
        buyutBtn.setPadding(16, 8, 16, 8);
        buyutBtn.setOnClickListener(v -> {
            TextView dialogTv = new TextView(this);
            dialogTv.setText(renklendirKod(kodTrim), TextView.BufferType.SPANNABLE);
            dialogTv.setTypeface(Typeface.MONOSPACE);
            dialogTv.setTextSize(15);
            dialogTv.setTextColor(Color.rgb(231, 241, 245));
            dialogTv.setPadding(24, 24, 24, 24);
            dialogTv.setTextIsSelectable(true);

            ScrollView scroll = new ScrollView(this);
            scroll.addView(dialogTv);

            new AlertDialog.Builder(this)
                    .setTitle("Kod")
                    .setView(scroll)
                    .setPositiveButton("Kapat", null)
                    .show();
        });

        baslikSatiri.addView(dilEtiketi);
        baslikSatiri.addView(kopyalaBtn);
        baslikSatiri.addView(buyutBtn);

        TextView tv = new TextView(this);
        tv.setText(renklendirKod(kodTrim), TextView.BufferType.SPANNABLE);
        tv.setTextSize(13);
        tv.setTextColor(Color.rgb(231, 241, 245));
        tv.setTypeface(Typeface.MONOSPACE);
        tv.setTextIsSelectable(true);

        disKutu.addView(baslikSatiri);
        disKutu.addView(tv);

        return disKutu;
    }


    private boolean superLigPuanKartlariEkle(LinearLayout kutu, String metin) {
        if (!metin.contains("EAGLE SPOR")
                || !metin.contains("SÜPER LİG PUAN DURUMU")) {
            return false;
        }

        java.util.ArrayList<String[]> takimlar = new java.util.ArrayList<>();
        java.util.regex.Pattern desen = java.util.regex.Pattern.compile(
                "^(\\d+)\\.\\s+(.+?)\\s+—\\s+(\\d+)\\s+puan$"
        );

        for (String satir : metin.split("\\n")) {
            java.util.regex.Matcher m = desen.matcher(satir.trim());
            if (m.matches()) {
                takimlar.add(new String[]{
                        m.group(1), m.group(2).trim(), m.group(3)
                });
            }
        }

        if (takimlar.isEmpty()) return false;

        TextView baslik = new TextView(this);
        baslik.setText("🏟️  SÜPER LİG PUAN DURUMU");
        baslik.setTextSize(18);
        baslik.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        baslik.setTextColor(Color.rgb(25, 65, 115));
        baslik.setPadding(2, 2, 2, 14);
        kutu.addView(baslik);

        for (String[] takim : takimlar) {
            int sira = Integer.parseInt(takim[0]);

            LinearLayout satir = new LinearLayout(this);
            satir.setOrientation(LinearLayout.HORIZONTAL);
            satir.setGravity(android.view.Gravity.CENTER_VERTICAL);
            satir.setPadding(10, 9, 10, 9);

            android.graphics.drawable.GradientDrawable satirArkaPlan =
                    new android.graphics.drawable.GradientDrawable();
            satirArkaPlan.setColor(Color.rgb(248, 251, 255));
            satirArkaPlan.setCornerRadius(15);
            satirArkaPlan.setStroke(1, Color.rgb(222, 233, 245));
            satir.setBackground(satirArkaPlan);

            int siraRengi;
            if (sira == 1) {
                siraRengi = Color.rgb(238, 176, 55);
            } else if (sira == 2) {
                siraRengi = Color.rgb(48, 158, 177);
            } else if (sira == 3) {
                siraRengi = Color.rgb(239, 125, 91);
            } else {
                siraRengi = Color.rgb(54, 105, 174);
            }

            TextView siraRozeti = new TextView(this);
            siraRozeti.setText(takim[0]);
            siraRozeti.setTextColor(Color.WHITE);
            siraRozeti.setTextSize(13);
            siraRozeti.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            siraRozeti.setGravity(android.view.Gravity.CENTER);
            siraRozeti.setMinWidth(34);
            siraRozeti.setPadding(8, 7, 8, 7);

            android.graphics.drawable.GradientDrawable rozetArkaPlan =
                    new android.graphics.drawable.GradientDrawable();
            rozetArkaPlan.setColor(siraRengi);
            rozetArkaPlan.setCornerRadius(11);
            siraRozeti.setBackground(rozetArkaPlan);

            satir.addView(siraRozeti);

            TextView takimAdi = new TextView(this);
            takimAdi.setText(takim[1]);
            takimAdi.setTextSize(13);
            takimAdi.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            takimAdi.setTextColor(Color.rgb(39, 53, 73));
            takimAdi.setPadding(10, 0, 6, 0);
            satir.addView(takimAdi, new LinearLayout.LayoutParams(
                    0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

            TextView puanRozeti = new TextView(this);
            puanRozeti.setText(takim[2] + " P");
            puanRozeti.setTextSize(14);
            puanRozeti.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            puanRozeti.setTextColor(Color.rgb(25, 105, 145));
            puanRozeti.setGravity(android.view.Gravity.CENTER);
            puanRozeti.setPadding(10, 8, 10, 8);

            android.graphics.drawable.GradientDrawable puanArkaPlan =
                    new android.graphics.drawable.GradientDrawable();
            puanArkaPlan.setColor(Color.rgb(224, 245, 250));
            puanArkaPlan.setCornerRadius(12);
            puanRozeti.setBackground(puanArkaPlan);
            satir.addView(puanRozeti);

            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT);
            lp.bottomMargin = 7;
            kutu.addView(satir, lp);
        }

        return true;
    }

    private boolean voleybolSonucKartlariEkle(LinearLayout kutu, String metin) {
        if (!metin.contains("TVF RESMÎ SON VOLEYBOL SONUÇLARI")) {
            return false;
        }

        TextView baslik = new TextView(this);
        baslik.setText("🏐 VOLEYBOL MAÇ SONUÇLARI");
        baslik.setTextSize(18);
        baslik.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        baslik.setTextColor(Color.rgb(25, 65, 115));
        baslik.setPadding(0, 0, 0, 12);
        kutu.addView(baslik);

        String ev = null, deplasman = null, lig = "", setler = "", tarihSaat = "";
        java.util.regex.Pattern skorDeseni = java.util.regex.Pattern.compile(
                "^\\*\\*(.+?)\\s+(\\d+)-(\\d+)\\s+(.+?)\\*\\*$"
        );

        for (String satir : metin.split("\\n")) {
            String temiz = satir.trim();
            java.util.regex.Matcher eslesme = skorDeseni.matcher(temiz);

            if (eslesme.matches()) {
                if (ev != null) {
                    voleybolKartEkle(kutu, ev, deplasman, lig, setler, tarihSaat);
                }
                ev = eslesme.group(1).trim() + "  " + eslesme.group(2);
                deplasman = eslesme.group(4).trim() + "  " + eslesme.group(3);
                lig = "";
                setler = "";
                tarihSaat = "";
            } else if (ev != null && temiz.startsWith("📅 ")
                    && temiz.contains("🕓")) {
                tarihSaat = temiz;
            } else if (ev != null && temiz.startsWith("_") && temiz.endsWith("_")) {
                lig = temiz.substring(1, temiz.length() - 1);
            } else if (ev != null && temiz.startsWith("Setler:")) {
                setler = temiz;
            }
        }

        if (ev == null) return false;
        voleybolKartEkle(kutu, ev, deplasman, lig, setler, tarihSaat);
        return true;
    }

    private void voleybolKartEkle(
            LinearLayout kutu, String ev, String deplasman, String lig,
            String setler, String tarihSaat) {
        LinearLayout kart = new LinearLayout(this);
        kart.setOrientation(LinearLayout.VERTICAL);
        kart.setPadding(16, 14, 16, 14);

        android.graphics.drawable.GradientDrawable arkaPlan =
                new android.graphics.drawable.GradientDrawable();
        arkaPlan.setColor(Color.rgb(248, 250, 253));
        arkaPlan.setCornerRadius(18);
        arkaPlan.setStroke(1, Color.rgb(220, 228, 238));
        kart.setBackground(arkaPlan);

        LinearLayout satir = new LinearLayout(this);
        satir.setOrientation(LinearLayout.HORIZONTAL);
        satir.setGravity(android.view.Gravity.CENTER_VERTICAL);

        String evAdi = ev.replaceFirst("\\s+\\d+$", "");
        String deplasmanAdi = deplasman.replaceFirst("\\s+\\d+$", "");
        String skor = ev.substring(ev.lastIndexOf(' ') + 1) + "–"
                + deplasman.substring(deplasman.lastIndexOf(' ') + 1);

        TextView takimlar = new TextView(this);
        takimlar.setText(evAdi + "\n" + deplasmanAdi);
        takimlar.setTextSize(15);
        takimlar.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        takimlar.setTextColor(Color.rgb(35, 45, 60));
        takimlar.setLineSpacing(5, 1f);
        satir.addView(takimlar, new LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f));

        TextView skorYazisi = new TextView(this);
        skorYazisi.setText(skor);
        skorYazisi.setTextSize(23);
        skorYazisi.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        skorYazisi.setTextColor(Color.rgb(180, 30, 45));
        skorYazisi.setGravity(android.view.Gravity.END | android.view.Gravity.CENTER_VERTICAL);
        satir.addView(skorYazisi, new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));

        kart.addView(satir);

        if (!tarihSaat.isEmpty()) {
            TextView tarihYazisi = new TextView(this);
            tarihYazisi.setText(tarihSaat);
            tarihYazisi.setTextSize(13);
            tarihYazisi.setTextColor(Color.rgb(65, 90, 120));
            tarihYazisi.setPadding(0, 7, 0, 0);
            kart.addView(tarihYazisi);
        }

        if (!lig.isEmpty()) {
            TextView ligYazisi = new TextView(this);
            ligYazisi.setText(lig);
            ligYazisi.setTextSize(12);
            ligYazisi.setTextColor(Color.rgb(90, 100, 115));
            ligYazisi.setPadding(0, 8, 0, 0);
            kart.addView(ligYazisi);
        }

        if (!setler.isEmpty()) {
            TextView setYazisi = new TextView(this);
            setYazisi.setText(setler);
            setYazisi.setTextSize(13);
            setYazisi.setTextColor(Color.rgb(45, 95, 145));
            setYazisi.setPadding(0, 5, 0, 0);
            kart.addView(setYazisi);
        }

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT);
        lp.bottomMargin = 12;
        kutu.addView(kart, lp);
    }

    private void mesajIcerigiEkle(LinearLayout kutu, String metin) {
        if (superLigPuanKartlariEkle(kutu, metin)) return;
        if (voleybolSonucKartlariEkle(kutu, metin)) return;
        Pattern blockPattern = Pattern.compile("```[a-zA-Z]*\\n([\\s\\S]*?)```");
        Matcher blockMatcher = blockPattern.matcher(metin);

        int sonBitis = 0;

        while (blockMatcher.find()) {
            int start = blockMatcher.start();
            int end = blockMatcher.end();

            if (start > sonBitis) {
                String normalMetin = metin.substring(sonBitis, start);
                if (!normalMetin.trim().isEmpty()) {
                    uzunMetinOlustur(kutu, normalMetin);
                }
            }

            String kodMetni = blockMatcher.group(1);
            kutu.addView(kodKutusuOlustur(kodMetni));

            sonBitis = end;
        }

        if (sonBitis < metin.length()) {
            String kalan = metin.substring(sonBitis);
            if (!kalan.trim().isEmpty()) {
                uzunMetinOlustur(kutu, kalan);
            }
        }
    }

    private void icerikleriGuvenliEkle(LinearLayout kutu, String metin) {
        final int esik = 1500;
        final int onizlemeHedefi = 600;

        if (metin.length() <= esik) {
            mesajIcerigiEkle(kutu, metin);
            return;
        }

        int kes = metin.lastIndexOf(" ", onizlemeHedefi);
        if (kes < 300) {
            kes = onizlemeHedefi;
        }

        int fenceSayisi = 0;
        int aranan = 0;
        while (true) {
            int bulunan = metin.indexOf("```", aranan);
            if (bulunan == -1 || bulunan >= kes) {
                break;
            }
            fenceSayisi++;
            aranan = bulunan + 3;
        }

        if (fenceSayisi % 2 != 0) {
            int kapanis = metin.indexOf("```", kes);
            if (kapanis != -1) {
                kes = kapanis + 3;
            } else {
                kes = metin.length();
            }
        }

        final int kesFinal = Math.min(kes, metin.length());
        final String kisaMetin = metin.substring(0, kesFinal).trim();
        final String tamMetin = metin;

        if (kesFinal >= metin.length()) {
            mesajIcerigiEkle(kutu, metin);
            return;
        }

        final LinearLayout alan = new LinearLayout(this);
        alan.setOrientation(LinearLayout.VERTICAL);

        final TextView devamBtn = new TextView(this);
        devamBtn.setText("Daha fazlasını göster");
        devamBtn.setTextSize(14);
        devamBtn.setTypeface(Typeface.create("sans-serif-medium", Typeface.NORMAL));
        devamBtn.setTextColor(Color.rgb(75, 218, 220));
        devamBtn.setGravity(Gravity.CENTER);
        devamBtn.setPadding(18, 14, 18, 14);

        GradientDrawable kenarlik = new GradientDrawable();
        kenarlik.setColor(Color.TRANSPARENT);
        kenarlik.setStroke(2, Color.rgb(0, 174, 185));
        kenarlik.setCornerRadius(24);
        devamBtn.setBackground(kenarlik);

        LinearLayout.LayoutParams btnLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        btnLp.gravity = Gravity.CENTER_HORIZONTAL;
        btnLp.setMargins(0, 12, 0, 4);
        devamBtn.setLayoutParams(btnLp);

        mesajIcerigiEkle(alan, kisaMetin);
        alan.addView(devamBtn);

        devamBtn.setOnClickListener(v -> {
            boolean acik = "Daha azını göster".contentEquals(devamBtn.getText());
            alan.removeAllViews();

            if (!acik) {
                mesajIcerigiEkle(alan, tamMetin);
                alan.addView(devamBtn);
                devamBtn.setText("Daha azını göster");
            } else {
                mesajIcerigiEkle(alan, kisaMetin);
                alan.addView(devamBtn);
                devamBtn.setText("Daha fazlasını göster");
            }
        });

        kutu.addView(alan);
    }

    private boolean gorselAramasiUygunMu(String soru, String cevap) {
        if (soru == null || cevap == null) return false;

        String q = soru.toLowerCase(Locale.ROOT).trim();
        String a = cevap.toLowerCase(Locale.ROOT).trim();

        // Tek kelimelik konu sorularını da destekle: "Adana", "İzmir", "Norveç".
        if (q.length() < 3) return false;

        // Görsel gerektirmeyen sohbet, hesaplama, kod ve özel konuları dışarıda tut.
        String[] engeller = {
                "merhaba", "selam", "teşekkür", "teşekkur", "nasılsın",
                "kaç eder", "hesapla", "kökünü bul", "kod yaz", "kodla",
                "python", "java", "javascript", "hata ayıkla", "debug",
                "şifre", "parola", "kişisel", "tanı koy"
        };
        for (String e : engeller) {
            if (q.contains(e)) return false;
        }

        // Artık yalnızca belirli soru kalıplarına bağlı değil.
        // Konu içeren kısa ve doğal sorular da görsel aramasına gider.
        return true;
    }

    private void commonsGorselleriEkle(LinearLayout kart, String soru) {
        android.util.Log.i("EagleGorsel", "1 - Görsel araması çağrıldı: " + soru);
        gorselExecutor.execute(() -> {
            HttpURLConnection baglanti = null;
            try {
                // Sorudaki istek kalıplarını ve Türkçe hâl eklerini temizle.
                // Böylece "Adana'yı tanıtır mısın?" -> "Adana" olur.
                // Orijinal harfleri koru. Özellikle "İzmir" kelimesi
                // Locale.ROOT ile küçük harfe çevrilince birleşen nokta
                // karakteri içerir; onu harf dışı sayıp silmek "zmir" hatası üretirdi.
                String hamKonu = soru == null ? "" : soru.trim();

                if (hamKonu.length() > 120) {
                    int konuSiniri = -1;
                    char[] ayiricilar = {'(', ',', ':', '.', '\n'};
                    for (char ayirici : ayiricilar) {
                        int konum = hamKonu.indexOf(ayirici);
                        if (konum > 0 && konum < 100
                                && (konuSiniri < 0 || konum < konuSiniri)) {
                            konuSiniri = konum;
                        }
                    }
                    if (konuSiniri > 0) {
                        String kisaKonu = hamKonu.substring(0, konuSiniri).trim();
                        if (!kisaKonu.isEmpty() && kisaKonu.split("\\s+").length <= 4) {
                            hamKonu = kisaKonu;
                        }
                    }
                }
                hamKonu = hamKonu.replaceAll("[^\\p{L}\\p{M}\\p{N}]+", " ").trim();
                String[] durKelimeler = {
                        "bilgi", "ver", "verir", "misin", "misiniz", "mi", "mu", "mı", "mü",
                        "hakkinda", "nedir", "kimdir", "anlat", "tanit", "goster",
                        "gosterir", "resim", "resimleri", "fotograf", "fotograflari",
                        "lutfen", "ile", "icin", "ve", "bir", "bana", "lazim",
                        "yi", "yı", "yu", "yü", "nin", "nın", "nun", "nün",
                        "den", "dan", "de", "da", "ye", "ya", "e", "a", "i", "in"
                };
                java.util.Set<String> durSet = new java.util.HashSet<>(java.util.Arrays.asList(durKelimeler));
                StringBuilder konuBuilder = new StringBuilder();
                for (String kelime : hamKonu.split("\\s+")) {
                    String normalizeKelime = java.text.Normalizer.normalize(
                            kelime.toLowerCase(Locale.ROOT), java.text.Normalizer.Form.NFD)
                            .replaceAll("\\p{M}+", "")
                            .replace('ı', 'i').replace('ş', 's').replace('ğ', 'g')
                            .replace('ü', 'u').replace('ö', 'o').replace('ç', 'c');
                    if (normalizeKelime.length() < 2 || durSet.contains(normalizeKelime)) continue;
                    if (konuBuilder.length() > 0) konuBuilder.append(' ');
                    konuBuilder.append(kelime);
                }
                String konu = konuBuilder.toString().trim();
                if (konu.length() < 2) {
                    android.util.Log.w("EagleGorsel", "Arama konusu çıkarılamadı: " + soru);
                    return;
                }
                android.util.Log.i("EagleGorsel", "Temizlenen görsel konusu: " + konu);

                // Konuyu genel biçimde koru; şehir ve ülke listesi kullanma.
                String sorgu = URLEncoder.encode(konu, "UTF-8");
                String api = "https://commons.wikimedia.org/w/api.php"
                        + "?action=query&generator=search&gsrnamespace=6&gsrlimit=40"
                        + "&gsrsearch=" + sorgu
                        + "&prop=imageinfo&iiprop=url%7Cextmetadata&iiurlwidth=640&format=json";

                URL url = new URL(api);
                baglanti = (HttpURLConnection) url.openConnection();
                baglanti.setConnectTimeout(7000);
                baglanti.setReadTimeout(9000);
                baglanti.setRequestProperty("User-Agent", "EagleAI-Android/1.0 (Wikimedia Commons image preview)");
                baglanti.setRequestProperty("Accept", "application/json");
                int httpKod = baglanti.getResponseCode();
                android.util.Log.i("EagleGorsel", "2 - Wikimedia HTTP: " + httpKod);
                if (httpKod != HttpURLConnection.HTTP_OK) {
                    gorselDurumunuGoster(kart, "Görseller şu anda alınamadı (HTTP " + httpKod + ").");
                    return;
                }

                StringBuilder jsonMetni = new StringBuilder();
                try (InputStream in = baglanti.getInputStream();
                     BufferedReader r = new BufferedReader(
                             new InputStreamReader(in, StandardCharsets.UTF_8))) {
                    String satir;
                    while ((satir = r.readLine()) != null) jsonMetni.append(satir);
                }

                String hamJson = jsonMetni.toString().trim();
if (hamJson.startsWith("\uFEFF")) {
    hamJson = hamJson.substring(1);
}
if (hamJson.isEmpty()) {
    throw new IOException("Wikimedia boş yanıt döndürdü.");
}

JSONObject kok;
try {
    kok = new JSONObject(hamJson);
} catch (org.json.JSONException jsonHata) {
    String onizleme = hamJson.substring(0, Math.min(180, hamJson.length()))
            .replace('\n', ' ').replace('\r', ' ');
    throw new IOException(
            "JSON okunamadı. Uzunluk=" + hamJson.length()
                    + " Yanıt=" + onizleme,
            jsonHata
    );
}
                JSONObject apiHata = kok.optJSONObject("error");
                if (apiHata != null) {
                    String hataMetni = apiHata.optString("info", "Wikimedia arama hatası");
                    android.util.Log.e("EagleGorsel", hataMetni);
                    gorselDurumunuGoster(kart, "Görsel araması tamamlanamadı: " + hataMetni);
                    return;
                }
                JSONObject query = kok.optJSONObject("query");
                JSONObject pages = query == null ? null : query.optJSONObject("pages");
                if (pages == null || pages.length() == 0) {
                    android.util.Log.w("EagleGorsel", "Wikimedia bu konu için sayfa döndürmedi: " + konu);
                    gorselDurumunuGoster(kart, "Bu konu için Wikimedia'da görsel bulunamadı.");
                    return;
                }
                android.util.Log.i("EagleGorsel", "3 - API sayfa sayısı: " + pages.length());

                String konuKucukPuan = konu.toLowerCase(Locale.ROOT);
                String[] kelimeler = konuKucukPuan
                        .split("[^\\p{L}\\p{N}]+");
                List<JSONObject> secilenler = new ArrayList<>();

                JSONArray pageIds = pages.names();
                if (pageIds == null) return;

                for (int i = 0; i < pageIds.length(); i++) {
                    JSONObject page = pages.optJSONObject(pageIds.optString(i));
                    if (page == null) continue;


                    String baslik = page.optString("title", "")
                            .replaceFirst("(?i)^File:", "")
                            .replace('_', ' ')
                            .toLowerCase(Locale.ROOT);

                    JSONArray infos = page.optJSONArray("imageinfo");
                    if (infos == null || infos.length() == 0) continue;
                    JSONObject info = infos.optJSONObject(0);
                    if (info == null) continue;

                    // Wikimedia görsel açıklamasını da eşleştirmede kullan.
                    JSONObject ext = info.optJSONObject("extmetadata");
                    JSONObject descObj = ext == null
                            ? null : ext.optJSONObject("ImageDescription");
                    String aciklama = descObj == null
                            ? ""
                            : descObj.optString("value", "")
                                    .replaceAll("<[^>]*>", " ")
                                    .replaceAll("\\s+", " ")
                                    .toLowerCase(Locale.ROOT);

                    String[] gorselKelimeleri = konu.toLowerCase(Locale.ROOT)
                            .split("[^\\p{L}\\p{N}]+");

                    int anlamli = 0;
                    int baslikEslesme = 0;
                    int aciklamaEslesme = 0;
                    int puan = 0;

                    for (String kelime : gorselKelimeleri) {
                        if (kelime.length() < 3) continue;
                        anlamli++;

                        String kelimeNorm = java.text.Normalizer.normalize(
                                kelime.toLowerCase(Locale.ROOT),
                                java.text.Normalizer.Form.NFD)
                                .replaceAll("\\p{M}+", "");

                        String baslikNorm = java.text.Normalizer.normalize(
                                baslik, java.text.Normalizer.Form.NFD)
                                .replaceAll("\\p{M}+", "")
                                .replaceAll("[^\\p{L}\\p{N}]+", " ").trim();

                        String aciklamaNorm = java.text.Normalizer.normalize(
                                aciklama, java.text.Normalizer.Form.NFD)
                                .replaceAll("\\p{M}+", "")
                                .replaceAll("[^\\p{L}\\p{N}]+", " ").trim();

                        String kelimeSiniri = " " + kelimeNorm + " ";

                        if ((" " + baslikNorm + " ").contains(kelimeSiniri)) {
                            baslikEslesme++;
                            puan += 6;
                        } else if ((" " + aciklamaNorm + " ").contains(kelimeSiniri)) {
                            aciklamaEslesme++;
                            puan += 1;
                        }
                    }

                    if (anlamli == 0 || (baslikEslesme + aciklamaEslesme) == 0) continue;

                    // Başlık veya açıklamadaki konu eşleşmesi yeterlidir.

                    String konuBaslik = konu.toLowerCase(Locale.ROOT)
                            .replaceAll("\\s+", " ").trim();

                    if (konuBaslik.length() >= 4
                            && baslik.contains(konuBaslik)) {
                        puan += 12;
                    }

                    if (baslik.matches("(?s).*\\b(map|maps|chart|diagram|"
                            + "drawing|engraving|blueprint)\\b.*")) {
                        puan -= 5;
                    }

                    if (baslik.matches("(?s).*\\b(photo|photograph|view|"
                            + "panorama|skyline|coast|beach)\\b.*")) {
                        puan += 2;
                    }

String thumb = info.optString("thumburl", "");
                    if (!thumb.startsWith("https://")) continue;


String turMetni = (baslik + " " + aciklama).toLowerCase(Locale.ROOT);
String kategori = "diger";

if (turMetni.matches("(?s).*\\b(waterfall|waterfalls|cascade|falls)\\b.*")) {
    kategori = "selale";
} else if (turMetni.matches("(?s).*\\b(glacier|glaciers|iceberg|icefield)\\b.*")) {
    kategori = "buzul";
} else if (turMetni.matches("(?s).*\\b(volcano|volcanic|geyser|crater)\\b.*")) {
    kategori = "volkan";
} else if (turMetni.matches("(?s).*\\b(coast|coastal|beach|shore|seaside)\\b.*")) {
    kategori = "kiyi";
} else if (turMetni.matches("(?s).*\\b(city|town|urban|skyline|capital|street)\\b.*")) {
    kategori = "sehir";
} else if (turMetni.matches("(?s).*\\b(architecture|building|church|house|cathedral|museum)\\b.*")) {
    kategori = "mimari";
} else if (turMetni.matches("(?s).*\\b(mountain|mountains|landscape|panorama|forest|nature)\\b.*")) {
    kategori = "doga";
} else if (turMetni.matches("(?s).*\\b(lake|river|water|island)\\b.*")) {
    kategori = "su";
} else if (turMetni.matches("(?s).*\\b(wildlife|animal|animals|bird|birds)\\b.*")) {
    kategori = "canli";
}

JSONObject item = new JSONObject();
                    item.put("title", page.optString("title", "Wikimedia Commons"));
                    item.put("thumb", thumb);
                        item.put("original", info.optString("url", ""));
                    item.put("source", info.optString("descriptionurl",
                            "https://commons.wikimedia.org/"));
                    item.put("category", kategori);
                    item.put("score", puan);

                    // Sonuçları puana göre azalan sırada tut.
                    int konum = 0;
                    while (konum < secilenler.size()
                            && secilenler.get(konum).optInt("score") >= puan) {
                        konum++;
                    }
                    secilenler.add(konum, item);
                }

                List<JSONObject> cesitliSecilenler = new ArrayList<>();
                java.util.Set<String> kullanilanTurler = new java.util.HashSet<>();

                // Önce farklı kategorilerden en alakalı görselleri seç.
                for (JSONObject aday : secilenler) {
                    String tur = aday.optString("category", "diger");
                    if (kullanilanTurler.add(tur) && cesitliSecilenler.size() < 4) {
                        cesitliSecilenler.add(aday);
                    }
                }

                // Dört farklı tür bulunamazsa kalan yerleri alakalı sonuçlarla tamamla.
                for (JSONObject aday : secilenler) {
                    if (cesitliSecilenler.size() >= 4) break;
                    if (!cesitliSecilenler.contains(aday)) {
                        cesitliSecilenler.add(aday);
                    }
                }

                secilenler.clear();
                secilenler.addAll(cesitliSecilenler);

                // Alakali sonuc bulunamazsa Commons aramasinin ilk gorsellerini goster.
                if (secilenler.isEmpty()) {
                    for (int i = 0; i < pageIds.length() && secilenler.size() < 4; i++) {
                        JSONObject page = pages.optJSONObject(pageIds.optString(i));
                        if (page == null) continue;

                        JSONArray infos = page.optJSONArray("imageinfo");
                        if (infos == null || infos.length() == 0) continue;

                        JSONObject info = infos.optJSONObject(0);
                        if (info == null) continue;

                        String thumb = info.optString("thumburl", "");
                        if (!thumb.startsWith("https://")) continue;

                        JSONObject item = new JSONObject();
                        item.put("title", page.optString("title", "Wikimedia Commons"));
                        item.put("thumb", thumb);
                        item.put("original", info.optString("url", ""));
                        item.put("source", info.optString("descriptionurl",
                                "https://commons.wikimedia.org/"));
                        item.put("score", 0);
                        secilenler.add(item);
                    }
                }

                android.util.Log.i("EagleGorsel", "4 - Gösterilecek görsel sayısı: " + secilenler.size());
                if (secilenler.isEmpty()) {
                    gorselDurumunuGoster(kart, "Arama yapıldı ancak görüntülenebilir görsel bulunamadı.");
                    return;
                }
                if (isFinishing()) return;

                runOnUiThread(() -> {
                    android.util.Log.i("EagleGorsel", "5 - Galeri ekleme aşamasına ulaşıldı");
                    if (isFinishing() || kart.getParent() == null) return;
                    int altSatirIndex = kart.getChildCount() - 1;
                    if (altSatirIndex < 0) return;

                    LinearLayout galeri = new LinearLayout(this);
                    galeri.setOrientation(LinearLayout.VERTICAL);
                    galeri.setPadding(0, 10, 0, 10);

                    for (JSONObject item : secilenler) {
                        String baslik = item.optString("title", "Wikimedia Commons")
                                .replaceFirst("(?i)^File:", "").replace('_', ' ');
                        String thumb = item.optString("thumb", "");
                        String kaynak = item.optString("source", "");

                        TextView baslikView = new TextView(this);
                        baslikView.setText("🖼 " + baslik);
                        baslikView.setTextSize(12);
                        baslikView.setTextColor(Color.GRAY);
                        galeri.addView(baslikView);

                        ImageView resim = new ImageView(this);
                        resim.setAdjustViewBounds(true);
                        resim.setScaleType(ImageView.ScaleType.FIT_CENTER);
                        resim.setContentDescription(baslik);
                        resim.setMaxHeight(420);
                        resim.setLayoutParams(new LinearLayout.LayoutParams(
                                LinearLayout.LayoutParams.MATCH_PARENT,
                                LinearLayout.LayoutParams.WRAP_CONTENT
                        ));
                        resim.setOnClickListener(v -> {
                            try {
                                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(kaynak)));
                            } catch (Exception ignored) {}
                        });
                        galeri.addView(resim);

                        TextView kaynakView = new TextView(this);
                        kaynakView.setText("Kaynak: Wikimedia Commons");
                        kaynakView.setTextSize(11);
                        kaynakView.setTextColor(Color.GRAY);
                        kaynakView.setOnClickListener(v -> {
                            try {
                                startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(kaynak)));
                            } catch (Exception ignored) {}
                        });
                        galeri.addView(kaynakView);

                        gorselExecutor.execute(() -> {
                            try {
                                Bitmap bitmap = wikimediaGorselIndir(
                                        thumb, item.optString("original", ""));
                                if (bitmap != null && !isFinishing()) {
                                    runOnUiThread(() -> {
                                        if (resim.getParent() != null) {
                                            resim.setImageBitmap(bitmap);
                                        }
                                    });
                                } else {
                                    android.util.Log.e("EagleGorsel",
                                            "Görsel iki adresle de indirilemedi: " + baslik);
                                    runOnUiThread(() -> {
                                        if (resim.getParent() != null) {
                                            resim.setImageResource(android.R.drawable.ic_menu_report_image);
                                            resim.setContentDescription("Görsel yüklenemedi: " + baslik);
                                        }
                                    });
                                }
                            } catch (Exception hata) {
                                android.util.Log.e("EagleGorsel",
                                        "Görsel indirilemedi: " + thumb, hata);
                                runOnUiThread(() -> {
                                    if (resim.getParent() != null) {
                                        resim.setImageResource(android.R.drawable.ic_menu_report_image);
                                        resim.setContentDescription("Görsel yüklenemedi: " + baslik);
                                    }
                                });
                            }
                        });
                    }

                    kart.addView(galeri, altSatirIndex);
                    kaydirma.post(() -> kaydirma.fullScroll(View.FOCUS_DOWN));
                });

            } catch (Exception e) {
                android.util.Log.e("EagleGorsel", "Commons görsel araması başarısız", e);
                gorselDurumunuGoster(kart, "Görsel araması sırasında bağlantı hatası oluştu: "
                        + (e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage()));
            } finally {
                if (baglanti != null) baglanti.disconnect();
            }
        });
    }


    // Hata/sonuç mesajını cevap kartına güvenli biçimde ekle.
    private void gorselDurumunuGoster(LinearLayout kart, String mesaj) {
        runOnUiThread(() -> {
            if (isFinishing() || kart == null || kart.getParent() == null) return;
            TextView durum = new TextView(this);
            durum.setText("🖼 " + mesaj);
            durum.setTextSize(12);
            durum.setTextColor(Color.GRAY);
            durum.setPadding(0, 8, 0, 8);
            int index = Math.max(0, kart.getChildCount() - 1);
            kart.addView(durum, index);
        });
    }

    private Bitmap wikimediaGorselIndir(String kucukResimUrl, String orijinalUrl)
            throws IOException {
        String[] adresler = {kucukResimUrl, orijinalUrl};

        for (String adres : adresler) {
            if (adres == null || !adres.startsWith("https://")) continue;

            HttpURLConnection bag = null;
            try {
                bag = (HttpURLConnection) new URL(adres).openConnection();
                bag.setInstanceFollowRedirects(true);
                bag.setConnectTimeout(10000);
                bag.setReadTimeout(15000);
                bag.setRequestProperty("User-Agent",
                        "EagleAI-Android/1.0 (Wikimedia Commons image preview)");

                int kod = bag.getResponseCode();
                String tip = bag.getContentType();

                android.util.Log.i("EagleGorsel",
                        "Görsel HTTP=" + kod + ", tür=" + tip + ", adres=" + adres);

                if (kod != HttpURLConnection.HTTP_OK
                        || tip == null
                        || !tip.toLowerCase(Locale.ROOT).startsWith("image/")) {
                    continue;
                }

                try (InputStream akis = bag.getInputStream()) {
                    Bitmap bitmap = BitmapFactory.decodeStream(akis);
                    if (bitmap != null) return bitmap;
                }
            } catch (Exception hata) {
                android.util.Log.w("EagleGorsel",
                        "Adres başarısız, diğer adres denenecek: " + adres, hata);
            } finally {
                if (bag != null) bag.disconnect();
            }
        }
        return null;
    }

    private GradientDrawable yuvarlakArkaPlan(int renk, int kenarlikRengi, float yaricapDp) {
        float yogunluk = getResources().getDisplayMetrics().density;
        GradientDrawable arkaPlan = new GradientDrawable();
        arkaPlan.setColor(renk);
        arkaPlan.setCornerRadius(yaricapDp * yogunluk);
        arkaPlan.setStroke(Math.max(1, (int) (yogunluk + 0.5f)), kenarlikRengi);
        return arkaPlan;
    }

    private LinearLayout mesajOlustur(String metin) {
        LinearLayout kutu = new LinearLayout(this);
        kutu.setOrientation(LinearLayout.VERTICAL);
        kutu.setPadding(16, 14, 16, 14);

        if (metin.startsWith("Sen: ")) {
            kutu.setBackgroundResource(R.drawable.kullanici_mesaji_cercevesi);
        } else {
            kutu.setBackgroundResource(R.drawable.eagle_mesaji_cercevesi);
        }
        kutu.setElevation(6f);

        boolean kullaniciMesaji = metin.startsWith("Sen: ");

        LinearLayout kimlikSatiri = new LinearLayout(this);
        kimlikSatiri.setOrientation(LinearLayout.HORIZONTAL);
        kimlikSatiri.setGravity(Gravity.CENTER_VERTICAL);
        kimlikSatiri.setPadding(0, 0, 0, 8);

        TextView avatar = new TextView(this);
        avatar.setText(kullaniciMesaji ? "👤" : "🦅");
        avatar.setTextSize(17);
        avatar.setGravity(Gravity.CENTER);
        avatar.setBackground(yuvarlakArkaPlan(
                kullaniciMesaji
                        ? Color.rgb(231, 218, 194)
                        : Color.rgb(196, 232, 234),
                kullaniciMesaji
                        ? Color.rgb(199, 169, 121)
                        : Color.rgb(85, 174, 181),
                18
        ));
        kimlikSatiri.addView(avatar, new LinearLayout.LayoutParams(34, 34));

        TextView kimlik = new TextView(this);
        kimlik.setText(kullaniciMesaji ? "SEN" : "EAGLE-AI");
        kimlik.setTextSize(11);
        kimlik.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
        kimlik.setTextColor(kullaniciMesaji
                ? Color.rgb(225, 205, 170)
                : Color.rgb(105, 220, 225));

        LinearLayout.LayoutParams kimlikLp = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        kimlikLp.setMargins(9, 0, 0, 0);
        kimlikSatiri.addView(kimlik, kimlikLp);

        kutu.addView(kimlikSatiri);
        // Kart başlığındaki kimlik bilgileri mesaj gövdesinde tekrar etmesin.
        String gorunenMetin = metin;
        if (kullaniciMesaji && gorunenMetin.startsWith("Sen: ")) {
            gorunenMetin = gorunenMetin.substring(5).trim();
        } else if (gorunenMetin.startsWith("🦅")) {
            gorunenMetin = gorunenMetin.replaceFirst("^🦅\\s*", "").trim();
        }
        icerikleriGuvenliEkle(kutu, gorunenMetin);

        LinearLayout altSatir = new LinearLayout(this);
        altSatir.setOrientation(LinearLayout.HORIZONTAL);
        altSatir.setGravity(Gravity.CENTER_VERTICAL);

        TextView saat = new TextView(this);
        saat.setText(
                new SimpleDateFormat("HH:mm", java.util.Locale.getDefault())
                        .format(new Date())
        );
        saat.setTextSize(11);
        saat.setTextColor(Color.rgb(142, 174, 185));
        LinearLayout.LayoutParams saatLp = new LinearLayout.LayoutParams(
                0,
                LinearLayout.LayoutParams.WRAP_CONTENT,
                1f
        );
        saat.setLayoutParams(saatLp);

        TextView kopyalaBtn = new TextView(this);
        kopyalaBtn.setText("📋");
        kopyalaBtn.setTextSize(18);
        kopyalaBtn.setGravity(Gravity.CENTER);
        kopyalaBtn.setPadding(12, 4, 4, 4);
        kopyalaBtn.setContentDescription("Mesajı kopyala");
        kopyalaBtn.setOnClickListener(v -> {
            ClipboardManager clipboard =
                    (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            String kopyalanacak = metin;
            if (kopyalanacak.startsWith("Sen: ")) {
                kopyalanacak = kopyalanacak.substring(5).trim();
            } else if (kopyalanacak.startsWith("🦅")) {
                kopyalanacak = kopyalanacak.replaceFirst("^🦅\\s*", "").trim();
            }
            ClipData clip = ClipData.newPlainText("Eagle Mesaj", kopyalanacak);
            clipboard.setPrimaryClip(clip);
            Toast.makeText(this, "📋 Mesaj kopyalandı", Toast.LENGTH_SHORT).show();
        });

        altSatir.addView(saat);
        altSatir.addView(kopyalaBtn);
        kutu.addView(altSatir);

        int ekranGenisligi = getResources().getDisplayMetrics().widthPixels;
        int maxBalonGenisligi = (int) (ekranGenisligi * 0.84f);
        int ekranSiniri = (int) (640 * getResources().getDisplayMetrics().density);
        maxBalonGenisligi = Math.min(maxBalonGenisligi, ekranSiniri);

        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(
                maxBalonGenisligi,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        lp.gravity = metin.startsWith("Sen: ")
                ? Gravity.END : Gravity.START;

        lp.setMargins(0, 0, 0, 12);
        kutu.setLayoutParams(lp);

        return kutu;
    }

    private void uzunCevapOlustur(LinearLayout kutu, String metin) {
        final int limit = 500;

        int kes = metin.lastIndexOf(" ", limit);

        if (kes < 300) {
            kes = limit;
        }

        final String kisaMetin = metin.substring(0, kes).trim();
        final String tamMetin = metin;

        LinearLayout alan = new LinearLayout(this);
        alan.setOrientation(LinearLayout.VERTICAL);

        TextView metinTv = normalMetinOlustur(kisaMetin);

        TextView devamBtn = new TextView(this);
        devamBtn.setText("Daha fazlasını göster");
        devamBtn.setTextSize(14);
        devamBtn.setTypeface(
                Typeface.create("sans-serif-medium", Typeface.NORMAL)
        );
        devamBtn.setTextColor(Color.rgb(75, 218, 220));
        devamBtn.setGravity(Gravity.CENTER);
        devamBtn.setPadding(18, 12, 18, 12);

        GradientDrawable kenarlik = new GradientDrawable();
        kenarlik.setColor(Color.TRANSPARENT);
        kenarlik.setStroke(2, Color.rgb(0, 174, 185));
        kenarlik.setCornerRadius(24);
        devamBtn.setBackground(kenarlik);

        LinearLayout.LayoutParams btnLp =
                new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.WRAP_CONTENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                );

        btnLp.gravity = Gravity.CENTER_HORIZONTAL;
        btnLp.setMargins(0, 12, 0, 4);
        devamBtn.setLayoutParams(btnLp);

        devamBtn.setOnClickListener(v -> {
            boolean acik =
                    "Daha azını göster".contentEquals(devamBtn.getText());

            alan.removeAllViews();

            if (!acik) {
                // Açıldığında mevcut kod blokları da normal şekilde çizilecek.
                mesajIcerigiEkle(alan, tamMetin);
                alan.addView(devamBtn);
                devamBtn.setText("Daha azını göster");
            } else {
                // Tekrar kısa önizlemeye dön.
                alan.addView(normalMetinOlustur(kisaMetin));
                alan.addView(devamBtn);
                devamBtn.setText("Daha fazlasını göster");
            }
        });

        alan.addView(metinTv);
        alan.addView(devamBtn);
        kutu.addView(alan);
    }

    private void sesiMetneCevir() {
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                    new String[]{Manifest.permission.RECORD_AUDIO},
                    3001
            );
            return;
        }

        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
        );
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "tr-TR");
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "Konuş...");

        try {
            startActivityForResult(intent, 2001);
        } catch (Exception e) {
            Toast.makeText(
                    this,
                    "Ses tanıma bu cihazda desteklenmiyor",
                    Toast.LENGTH_SHORT
            ).show();
        }
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == 3001
                && grantResults.length > 0
                && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
            sesiMetneCevir();
        }
    }

    private void sesSecimMenusuGoster() {
        if (konusmaMotoru == null) {
            Toast.makeText(this, "Ses motoru hazır değil", Toast.LENGTH_SHORT).show();
            return;
        }

        java.util.List<Voice> turkceSesler = new java.util.ArrayList<>();
        java.util.List<String> gosterimListesi = new java.util.ArrayList<>();

        try {
            Set<Voice> sesler = konusmaMotoru.getVoices();
            if (sesler != null) {
                for (Voice v : sesler) {
                    if (v.getLocale().getLanguage().equals("tr")) {
                        turkceSesler.add(v);
                        gosterimListesi.add(v.getName());
                    }
                }
            }
        } catch (Exception e) {
            Toast.makeText(this, "Sesler alınamadı", Toast.LENGTH_SHORT).show();
            return;
        }

        if (turkceSesler.isEmpty()) {
            Toast.makeText(this, "Türkçe ses bulunamadı", Toast.LENGTH_SHORT).show();
            return;
        }

        String[] isimler = gosterimListesi.toArray(new String[0]);

        new AlertDialog.Builder(this)
                .setTitle("Bir ses seç (dinlemek için dokun)")
                .setItems(isimler, (dialog, which) -> {
                    Voice secilen = turkceSesler.get(which);
                    konusmaMotoru.setVoice(secilen);

                    SharedPreferences sp = getSharedPreferences("eagle_ses", MODE_PRIVATE);
                    sp.edit().putString("secili_ses", secilen.getName()).apply();

                    konusmaMotoru.speak(
                            "Merhaba, ben Eagle Yapay Zeka. Bu benim sesim.",
                            TextToSpeech.QUEUE_FLUSH,
                            null,
                            "ses_testi"
                    );
                })
                .setNegativeButton("Kapat", null)
                .show();
    }

    private void sesMotoruBaslat() {
        konusmaMotoru = new TextToSpeech(this, status -> {
            if (status == TextToSpeech.SUCCESS) {
                konusmaMotoru.setLanguage(new Locale("tr", "TR"));
                konusmaMotoru.setPitch(1.05f);
                konusmaMotoru.setSpeechRate(1.0f);

                try {
                    Set<Voice> sesler = konusmaMotoru.getVoices();
                    if (sesler != null) {
                        Voice enIyi = null;
                        for (Voice v : sesler) {
                            if (v.getLocale().getLanguage().equals("tr")
                                    && v.getName().toLowerCase().contains("female")) {
                                enIyi = v;
                                break;
                            }
                        }
                        if (enIyi == null) {
                            for (Voice v : sesler) {
                                if (v.getLocale().getLanguage().equals("tr")) {
                                    enIyi = v;
                                    break;
                                }
                            }
                        }
                        SharedPreferences sp = getSharedPreferences("eagle_ses", MODE_PRIVATE);
                        String kayitliSes = sp.getString("secili_ses", null);

                        if (kayitliSes != null) {
                            for (Voice v : sesler) {
                                if (v.getName().equals(kayitliSes)) {
                                    enIyi = v;
                                    break;
                                }
                            }
                        }

                        if (enIyi != null) {
                            konusmaMotoru.setVoice(enIyi);
                        }
                    }
                } catch (Exception e) {
                    // Ses listesi alinamazsa varsayilan sesle devam.
                }
            }
        });
    }

    private void metniSesliOku(String metin) {
        if (konusmaMotoru == null || !sesAcik) {
            return;
        }

        String temizMetin = metin.replaceAll("```[a-zA-Z]*\\n[\\s\\S]*?```", " ");
        temizMetin = temizMetin.replaceAll("[\\*#_>`]", "");

        // Emoji ve emoji sembollerini TTS'den çıkar.
        temizMetin = temizMetin.replaceAll(
                "[\\x{1F000}-\\x{1FAFF}\\x{2600}-\\x{27BF}\\x{2300}-\\x{23FF}\\x{2B00}-\\x{2BFF}\\x{FE0F}\\x{200D}]",
                " "
        );

        temizMetin = temizMetin.replaceAll("\\s{2,}", " ").trim();

        if (temizMetin.isEmpty()) {
            return;
        }

        // Skorları TTS için doğal okut: 2-0 / 2–0 -> 2 0
        // Görünen cevapta 2-0 aynen korunur.
        String sesMetni = temizMetin.replaceAll(
                "(.+?)\\s+(\\d{1,3})\\s*[-–]\\s*(\\d{1,3})\\s+(.+)",
                "$1 $2 $4 $3"
        );

        konusmaMotoru.speak(
                sesMetni,
                TextToSpeech.QUEUE_FLUSH,
                null,
                "eagle_cevap"
        );
    }

    private void dosyaSec() {
        String[] secenekler = {"📷 Kamera", "🖼️ Galeri", "📁 Dosyalar"};

        new AlertDialog.Builder(this)
                .setTitle("Ekle")
                .setItems(secenekler, (dialog, which) -> {
                    if (which == 0) {
                        kameraAc();
                    } else if (which == 1) {
                        galeriAc();
                    } else {
                        dosyalardanSec();
                    }
                })
                .show();
    }

    private void galeriAc() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("image/*");
        startActivityForResult(intent, 1001);
    }

    private void dosyalardanSec() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        startActivityForResult(intent, 1001);
    }

    private void kameraAc() {
        Intent intent = new Intent(android.provider.MediaStore.ACTION_IMAGE_CAPTURE);
        if (intent.resolveActivity(getPackageManager()) != null) {
            startActivityForResult(intent, 1002);
        } else {
            Toast.makeText(this, "Kamera bulunamadı", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);

        if (requestCode == 1002) {
            if (resultCode == RESULT_OK && data != null && data.getExtras() != null) {
                android.graphics.Bitmap foto =
                        (android.graphics.Bitmap) data.getExtras().get("data");

                if (foto != null) {
                    try {
                        File cacheDosya = new File(
                                getCacheDir(),
                                "eagle_kamera_" + System.currentTimeMillis() + ".jpg"
                        );

                        FileOutputStream cikis = new FileOutputStream(cacheDosya);
                        foto.compress(
                                android.graphics.Bitmap.CompressFormat.JPEG,
                                90,
                                cikis
                        );
                        cikis.flush();
                        cikis.close();

                        secilenDosyaUri = FileProvider.getUriForFile(
                                this,
                                "com.eagleai.borclar.fileprovider",
                                cacheDosya
                        );

                        onizlemeResmi.setImageBitmap(foto);
                        onizlemeAlani.setVisibility(View.VISIBLE);

                        Toast.makeText(
                                this,
                                "📷 Fotoğraf eklendi",
                                Toast.LENGTH_SHORT
                        ).show();

                    } catch (Exception exc) {
                        android.util.Log.e(
                                "EAGLE_CAMERA",
                                "Fotoğraf kaydedilemedi: " + exc.getMessage()
                        );
                        Toast.makeText(
                                this,
                                "Fotoğraf kaydedilemedi",
                                Toast.LENGTH_SHORT
                        ).show();
                    }
                }
            }
            return;
        }

        if (requestCode == 2001) {
            if (resultCode == RESULT_OK && data != null) {
                java.util.ArrayList<String> sonuclar = data.getStringArrayListExtra(
                        RecognizerIntent.EXTRA_RESULTS
                );
                if (sonuclar != null && !sonuclar.isEmpty()) {
                    String metin = sonuclar.get(0);
            android.util.Log.d("EAGLE_MIC", "Mikrofon sonucu: " + metin);
                    String mevcut = mesajKutusu.getText().toString();
                    if (mevcut.isEmpty()) {
                        mesajKutusu.setText(metin);
                    } else {
                        mesajKutusu.setText(mevcut + " " + metin);
                    }
                    mesajKutusu.setSelection(mesajKutusu.getText().length());

                    // 🎤 Konuşma metni hazırsa otomatik gönder.
                    mesajGonder();
                }
            }
            return;
        }

        if (requestCode != 1001 || resultCode != RESULT_OK || data == null) {
            return;
        }

        secilenDosyaUri = data.getData();
        Uri uri = secilenDosyaUri;

        if (uri == null) {
            Toast.makeText(this, "Dosya seçilemedi", Toast.LENGTH_SHORT).show();
            return;
        }

        try {
            String dosyaAdi = uri.getLastPathSegment();
            String mime = getContentResolver().getType(uri);

            if (mime == null) {
                mime = "application/octet-stream";
            }

            if (mime.startsWith("image/")) {
                onizlemeResmi.setImageURI(uri);
                onizlemeAlani.setVisibility(View.VISIBLE);
            }

            /*
             * Metin dosyalarını oku.
             * Resim, APK, ZIP, TAR.GZ gibi binary dosyaları
             * UTF-8 olarak okumuyoruz.
             */
            boolean metinDosyasi =
                    mime.startsWith("text/") ||
                    mime.equals("application/json") ||
                    mime.equals("application/xml") ||
                    mime.equals("application/javascript") ||
                    mime.equals("application/x-python") ||
                    mime.equals("application/x-java");

            if (metinDosyasi) {

                InputStream inputStream =
                        getContentResolver().openInputStream(uri);

                if (inputStream == null) {
                    Toast.makeText(
                            this,
                            "Dosya okunamadı",
                            Toast.LENGTH_SHORT
                    ).show();
                    return;
                }

                BufferedReader reader =
                        new BufferedReader(
                                new InputStreamReader(
                                        inputStream,
                                        StandardCharsets.UTF_8
                                )
                        );

                StringBuilder icerik = new StringBuilder();
                String satir;

                while ((satir = reader.readLine()) != null) {
                    icerik.append(satir).append("\n");
                }

                reader.close();

                mesajKutusu.setText(
                        "📎 Dosya: " + dosyaAdi + "\n\n" +
                        icerik.toString()
                );

                mesajKutusu.setSelection(mesajKutusu.length());

                Toast.makeText(
                        this,
                        "📄 Metin dosyası eklendi",
                        Toast.LENGTH_SHORT
                ).show();

            } else {

                // 📷 Resmi sohbet alanında önizle
                if (mime.startsWith("image/")) {

                    ImageView onizleme = new ImageView(this);
                    onizleme.setImageURI(uri);
                    onizleme.setAdjustViewBounds(true);
                    onizleme.setScaleType(
                            ImageView.ScaleType.CENTER_CROP
                    );

                    LinearLayout.LayoutParams resimLp =
                            new LinearLayout.LayoutParams(
                                    LinearLayout.LayoutParams.MATCH_PARENT,
                                    420
                            );

                    resimLp.setMargins(18, 10, 18, 10);


                    kaydirma.post(() ->
                            kaydirma.fullScroll(
                                    View.FOCUS_DOWN
                            )
                    );

                    mesajKutusu.setText("");

                    Toast.makeText(
                            this,
                            "📷 Resim hazır — mesajını yazıp GÖNDER'e bas.",
                            Toast.LENGTH_SHORT
                    ).show();

                } else {

                    mesajKutusu.setText(
                            "📎 " + dosyaAdi + "\n" +
                            "Tür: " + mime + "\n\n" +
                            "Dosya Eagle-AI'ye gönderilmeye hazır."
                    );

                    mesajKutusu.setSelection(
                            mesajKutusu.length()
                    );

                    Toast.makeText(
                            this,
                            "📎 Dosya hazır",
                            Toast.LENGTH_SHORT
                    ).show();
                }
            }

        } catch (Exception e) {
            Toast.makeText(
                    this,
                    "Dosya işlenemedi: " + e.getMessage(),
                    Toast.LENGTH_LONG
            ).show();
        }
    }

    @Override
    protected void onDestroy() {

        if (konusmaMotoru != null) {
            konusmaMotoru.stop();
            konusmaMotoru.shutdown();
        }

        executor.shutdownNow();
        gorselExecutor.shutdownNow();

        super.onDestroy();
    }

    private void scrollMesajAlaniAlta() {
        try {
            if (kaydirma != null) {
                kaydirma.post(() ->
                        kaydirma.fullScroll(android.view.View.FOCUS_DOWN)
                );
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
