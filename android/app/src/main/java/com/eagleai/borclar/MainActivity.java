package com.eagleai.borclar;

import android.text.Spannable;
import android.text.SpannableStringBuilder;
import android.text.style.ForegroundColorSpan;
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
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import android.util.Base64;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class MainActivity extends Activity {

    private static final String API_URL =
            "https://eagleai-8p9b4.faable.link/api/sohbet";

    private static final String MEMORY_URL =
            "https://eagleai-8p9b4.faable.link/api/hafiza";

    private LinearLayout mesajAlani;
    private EditText mesajKutusu;
    private Uri secilenDosyaUri;
    private ScrollView kaydirma;

    private final List<JSONObject> gecmis = new ArrayList<>();

    private final ExecutorService executor =
            Executors.newSingleThreadExecutor();

    private long sonMesajZamani = 0;
    private static final long MESAJ_BEKLEME_MS = 4000;

    private TextToSpeech konusmaMotoru;
    private boolean sesAcik = true;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        arayuzOlustur();
        sesMotoruBaslat();
    }

    private void arayuzOlustur() {

        LinearLayout ana = new LinearLayout(this);
        ana.setOrientation(LinearLayout.VERTICAL);
        ana.setBackgroundColor(Color.rgb(230, 230, 232));

          // ===== ÜST BAR =====
          LinearLayout ustBar = new LinearLayout(this);
          ustBar.setOrientation(LinearLayout.HORIZONTAL);
          ustBar.setGravity(Gravity.CENTER_VERTICAL);
          ustBar.setPadding(6, 8, 12, 8);
          ustBar.setBackgroundColor(Color.rgb(25, 25, 25));

          // ☰ SOL HAMBURGER MENÜ
          Button menuBtn = new Button(this);
          menuBtn.setText("☰");
          menuBtn.setTextSize(25);
          menuBtn.setTextColor(Color.WHITE);
          menuBtn.setAllCaps(false);
          menuBtn.setGravity(Gravity.CENTER);
          menuBtn.setPadding(0, 0, 0, 0);
          menuBtn.setBackgroundColor(Color.TRANSPARENT);

          LinearLayout.LayoutParams menuLp =
                  new LinearLayout.LayoutParams(58, 58);

          ustBar.addView(menuBtn, menuLp);

          // 🦅 EAGLE-AI BAŞLIK
          TextView baslik = new TextView(this);
          baslik.setText("🦅 EAGLE-AI");
          baslik.setTextSize(24);
          baslik.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
          baslik.setTextColor(Color.WHITE);
          baslik.setGravity(Gravity.CENTER_VERTICAL);
          baslik.setPadding(8, 0, 0, 0);

          LinearLayout.LayoutParams baslikLp =
                  new LinearLayout.LayoutParams(
                          0,
                          LinearLayout.LayoutParams.WRAP_CONTENT,
                          1
                  );

          ustBar.addView(baslik, baslikLp);

          ana.addView(ustBar);

        kaydirma = new ScrollView(this);

        mesajAlani = new LinearLayout(this);
        mesajAlani.setOrientation(LinearLayout.VERTICAL);
        mesajAlani.setPadding(16, 16, 16, 16);

        mesajAlani.addView(mesajOlustur(
                "🦅 Özhan, hoş geldin!\n\n" +
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
        alt.setPadding(8, 8, 8, 10);
        alt.setBackgroundColor(Color.rgb(245, 245, 245));

        // 📎 Dosya butonu
          // 📎 DOSYA BUTONU
          Button dosya = new Button(this);
          dosya.setText("+");
          dosya.setTextSize(24);
          dosya.setTextColor(Color.WHITE);
          dosya.setAllCaps(false);
          dosya.setGravity(Gravity.CENTER);
          dosya.setBackgroundColor(Color.rgb(70, 70, 70));
          dosya.setPadding(0, 0, 0, 0);

          LinearLayout.LayoutParams dosyaLp =
                  new LinearLayout.LayoutParams(60, 60);
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
        mesajKutusu.setPadding(18, 12, 18, 12);
        mesajKutusu.setTextColor(Color.rgb(30, 30, 30));
        mesajKutusu.setHintTextColor(Color.GRAY);
        mesajKutusu.setBackgroundColor(Color.WHITE);
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

        mesajLp.setMargins(4, 0, 6, 0);

        alt.addView(mesajKutusu, mesajLp);

        // 🎤 Mikrofon butonu
        Button mikrofon = new Button(this);
        mikrofon.setText("🎤");
        mikrofon.setTextSize(22);
        mikrofon.setTextColor(Color.WHITE);
        mikrofon.setAllCaps(false);
        mikrofon.setGravity(Gravity.CENTER);
        mikrofon.setBackgroundColor(Color.rgb(70, 70, 70));
        mikrofon.setPadding(0, 0, 0, 0);

        LinearLayout.LayoutParams mikrofonLp =
                new LinearLayout.LayoutParams(60, 60);
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
        gonder.setBackgroundColor(Color.rgb(10, 132, 255));

        LinearLayout.LayoutParams gonderLp =
                new LinearLayout.LayoutParams(56, 56);

        alt.addView(gonder, gonderLp);

        ana.addView(alt);

        dosya.setOnClickListener(v -> dosyaSec());

        mikrofon.setOnClickListener(v -> sesiMetneCevir());

        gonder.setOnClickListener(v -> mesajGonder());

        menuBtn.setOnClickListener(v -> {
            PopupMenu popup = new PopupMenu(this, menuBtn);
            popup.getMenu().add("🧠 Hafıza");
            popup.getMenu().add("💳 Borçlar");
            popup.getMenu().add("❓ Yardım");
            popup.getMenu().add("🆕 Yeni");
              popup.getMenu().add("🕘 Son Sohbetler");
            popup.getMenu().add("🗑️ Temizle");
            popup.getMenu().add("🔊 Ses Seç");
            popup.getMenu().add(sesAcik ? "🔇 Sesi Kapat" : "🔊 Sesi Aç");

            popup.setOnMenuItemClickListener(item -> {
                String secim = item.getTitle().toString();

                if (secim.contains("Borçlar")) {
                    yerelMesajEkle("💳 Borçlar yükleniyor...");

                    executor.execute(() -> {
                        String sonuc = borclarIstek();
                        final String cevapFinal = sonuc;

                        runOnUiThread(() -> {
                            mesajAlani.addView(
                                    mesajOlustur(
                                            "💳 BORÇ VE TAKSİT RAPORU\n\n" +
                                            cevapFinal
                                    )
                            );

                            kaydirma.post(() ->
                                    kaydirma.fullScroll(View.FOCUS_DOWN)
                            );
                        });
                    });
                } else if (secim.contains("Hafıza")) {
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

        final String mesaj =
                mesajKutusu.getText().toString().trim();

        if (mesaj.isEmpty()) {
            return;
        }

        long simdi = System.currentTimeMillis();
        if (simdi - sonMesajZamani < MESAJ_BEKLEME_MS) {
            Toast.makeText(
                    this,
                    "Çok hızlı gönderiyorsun, biraz bekle 🦅",
                    Toast.LENGTH_SHORT
            ).show();
            return;
        }
        sonMesajZamani = simdi;

        mesajAlani.addView(mesajOlustur("Sen: " + mesaj));
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
            String sonucCevap = geminiIstek(mesaj);

            if (sonucCevap == null) {
                sonucCevap =
                        "❌ Eagle-AI API bağlantısı kurulamadı.\n\n" +
                        "Telefonun aynı Wi-Fi ağında olduğundan " +
                        "ve Termux'taki eagle_api.py sunucusunun çalıştığından emin ol.";
            }

            final String cevapFinal = sonucCevap;

            runOnUiThread(() -> {
                mesajAlani.removeView(durum);

                mesajAlani.addView(
                        mesajOlustur("🦅\n\n" + cevapFinal)
                );
                gecmiseKaydet("🦅\n\n" + cevapFinal);
                  sohbeteMesajEkle("🦅\n\n" + cevapFinal);
                metniSesliOku(cevapFinal);

                kaydirma.post(() ->
                        kaydirma.fullScroll(View.FOCUS_DOWN)
                );
            });
        });
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

                JSONArray memory =
                        json.optJSONArray("memory");

                if (memory == null || memory.length() == 0) {
                    return "Hafıza şu anda boş.";
                }

                StringBuilder metin =
                        new StringBuilder();

                for (int i = 0; i < memory.length(); i++) {
                    metin.append("• ")
                         .append(memory.optString(i))
                         .append("\\n");
                }

                return metin.toString().trim();
            }

            return "❌ Hafıza API hatası: " +
                    json.optString(
                            "error",
                            "Bilinmeyen hata."
                    );

        } catch (Exception e) {

            return "❌ Hafıza bağlantı hatası: " +
                    e.getClass().getSimpleName();

        } finally {

            if (baglanti != null) {
                baglanti.disconnect();
            }
        }
    }

    private String dosyaBase64() {
        if (secilenDosyaUri == null) {
            return null;
        }

        try {
            InputStream inputStream =
                    getContentResolver().openInputStream(secilenDosyaUri);

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

    private String borclarIstek() {
        HttpURLConnection baglanti = null;

        try {
            URL url = new URL(
                    API_URL.replace("/api/sohbet", "/api/borclar")
            );

            baglanti = (HttpURLConnection) url.openConnection();
            baglanti.setRequestMethod("GET");
            baglanti.setConnectTimeout(10000);
            baglanti.setReadTimeout(30000);

            int kod = baglanti.getResponseCode();

            InputStreamReader inputReader;

            if (kod >= 200 && kod < 300) {
                inputReader = new InputStreamReader(
                        baglanti.getInputStream(),
                        StandardCharsets.UTF_8
                );
            } else {
                inputReader = new InputStreamReader(
                        baglanti.getErrorStream(),
                        StandardCharsets.UTF_8
                );
            }

            BufferedReader reader = new BufferedReader(inputReader);

            StringBuilder sonuc = new StringBuilder();
            String satir;

            while ((satir = reader.readLine()) != null) {
                sonuc.append(satir);
            }

            reader.close();

            JSONObject json = new JSONObject(sonuc.toString());

            if (kod >= 200 &&
                    kod < 300 &&
                    json.optBoolean("success", false)) {

                JSONObject rapor = json.optJSONObject("rapor");

                if (rapor == null) {
                    return "Borç raporu alınamadı.";
                }

                JSONArray borclar = json.optJSONArray("borclar");
                StringBuilder metin = new StringBuilder();

                if (borclar != null && borclar.length() > 0) {

                    for (int i = 0; i < borclar.length(); i++) {

                        JSONObject borc = borclar.getJSONObject(i);

                        metin.append("• ")
                                .append(borc.optString("ad", "Borç"))
                                .append("\n")
                                .append("  Kategori: ")
                                .append(borc.optString("kategori", "-"))
                                .append("\n")
                                .append("  Toplam: ")
                                .append(String.format(
                                        java.util.Locale.US,
                                        "%,.2f TL",
                                        borc.optDouble("toplam_borc", 0)
                                ))
                                .append("\n")
                                .append("  Ödenen: ")
                                .append(String.format(
                                        java.util.Locale.US,
                                        "%,.2f TL",
                                        borc.optDouble("odenen_tutar", 0)
                                ))
                                .append("\n")
                                .append("  Kalan: ")
                                .append(String.format(
                                        java.util.Locale.US,
                                        "%,.2f TL",
                                        borc.optDouble("kalan_borc", 0)
                                ))
                                .append("\n")
                                .append("  Taksit: ")
                                .append(borc.optInt("taksit_sayisi", 1))
                                .append("\n\n");
                    }

                } else {
                    metin.append("Kayıtlı borç bulunmuyor.\n\n");
                }

                metin.append("💰 Genel Toplam: ")
                        .append(String.format(
                                java.util.Locale.US,
                                "%,.2f TL",
                                rapor.optDouble("toplam_borc", 0)
                        ))
                        .append("\n💵 Ödenen: ")
                        .append(String.format(
                                java.util.Locale.US,
                                "%,.2f TL",
                                rapor.optDouble("toplam_odenen", 0)
                        ))
                        .append("\n📌 Kalan: ")
                        .append(String.format(
                                java.util.Locale.US,
                                "%,.2f TL",
                                rapor.optDouble("toplam_kalan", 0)
                        ));

                return metin.toString();
            }

            return "API hatası: " +
                    json.optString("error", "Bilinmeyen hata.");

        } catch (Exception e) {

            return "Borç API bağlantı hatası: " +
                    e.getClass().getSimpleName() +
                    " - " +
                    e.getMessage();

        } finally {

            if (baglanti != null) {
                baglanti.disconnect();
            }
        }
    }

    private String geminiIstek(String mesaj) {

        HttpURLConnection baglanti = null;

        try {

            URL url = new URL(API_URL);

            baglanti =
                    (HttpURLConnection) url.openConnection();

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
            if (secilenDosyaUri != null) {
                String dosya64 = dosyaBase64();
                String mime = getContentResolver()
                        .getType(secilenDosyaUri);

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

            output.write(veri);
            output.flush();
            output.close();

            int kod = baglanti.getResponseCode();

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
                "🦅 Özhan, hoş geldin!\n\n" +
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
                            "🦅 Özhan, hoş geldin!\n\n" +
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
                color = Color.rgb(0, 128, 0);
            } else if (token.startsWith("\"") || token.startsWith("'")) {
                color = Color.rgb(165, 42, 42);
            } else if (Character.isDigit(token.charAt(0))) {
                color = Color.rgb(0, 150, 160);
            } else {
                color = Color.rgb(0, 0, 255);
            }
            styled.setSpan(new ForegroundColorSpan(color), tokenMatcher.start(), tokenMatcher.end(),
                    Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);
        }
        return styled;
    }

    private TextView normalMetinOlustur(String metin) {
        TextView tv = new TextView(this);
        tv.setText(metin.trim());
        tv.setTextSize(16);
        tv.setTextColor(Color.rgb(25, 25, 25));
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
        devamBtn.setTextColor(Color.rgb(0, 122, 255));
        devamBtn.setGravity(Gravity.CENTER);
        devamBtn.setPadding(18, 12, 18, 12);

        GradientDrawable kenarlik = new GradientDrawable();
        kenarlik.setColor(Color.TRANSPARENT);
        kenarlik.setStroke(2, Color.rgb(0, 122, 255));
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
        dilEtiketi.setTextColor(Color.GRAY);
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
        tv.setTypeface(Typeface.MONOSPACE);
        tv.setTextIsSelectable(true);

        disKutu.addView(baslikSatiri);
        disKutu.addView(tv);

        return disKutu;
    }

    private void mesajIcerigiEkle(LinearLayout kutu, String metin) {
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
        devamBtn.setTextColor(Color.rgb(0, 122, 255));
        devamBtn.setGravity(Gravity.CENTER);
        devamBtn.setPadding(18, 14, 18, 14);

        GradientDrawable kenarlik = new GradientDrawable();
        kenarlik.setColor(Color.TRANSPARENT);
        kenarlik.setStroke(2, Color.rgb(0, 122, 255));
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

    private LinearLayout mesajOlustur(String metin) {
        LinearLayout kutu = new LinearLayout(this);
        kutu.setOrientation(LinearLayout.VERTICAL);
        kutu.setPadding(18, 18, 18, 18);

        if (metin.startsWith("Sen: ")) {
            kutu.setBackgroundResource(R.drawable.kullanici_mesaji_cercevesi);
        } else {
            kutu.setBackgroundResource(R.drawable.eagle_mesaji_cercevesi);
        }
        kutu.setElevation(6f);

        icerikleriGuvenliEkle(kutu, metin);

        TextView saat = new TextView(this);
        saat.setText(
                new SimpleDateFormat("HH:mm", java.util.Locale.getDefault())
                        .format(new Date())
        );
        saat.setTextSize(11);
        saat.setTextColor(Color.GRAY);
        saat.setGravity(Gravity.END);

        kutu.addView(saat);

        LinearLayout.LayoutParams lp =
                new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                );

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
        devamBtn.setTextColor(Color.rgb(0, 122, 255));
        devamBtn.setGravity(Gravity.CENTER);
        devamBtn.setPadding(18, 12, 18, 12);

        GradientDrawable kenarlik = new GradientDrawable();
        kenarlik.setColor(Color.TRANSPARENT);
        kenarlik.setStroke(2, Color.rgb(0, 122, 255));
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

        // Emoji ve sembolleri seslendirmeden çıkar.
        temizMetin = temizMetin.replaceAll(
                "[\\uD800-\\uDBFF][\\uDC00-\\uDFFF]|[\\u2600-\\u27BF]|[\\uFE00-\\uFE0F]",
                " "
        );

        temizMetin = temizMetin.replaceAll("\\s{2,}", " ").trim();

        if (temizMetin.isEmpty()) {
            return;
        }

        konusmaMotoru.speak(
                temizMetin,
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
                    ImageView onizleme = new ImageView(this);
                    onizleme.setImageBitmap(foto);
                    onizleme.setAdjustViewBounds(true);
                    onizleme.setScaleType(ImageView.ScaleType.CENTER_CROP);

                    LinearLayout.LayoutParams resimLp =
                            new LinearLayout.LayoutParams(
                                    LinearLayout.LayoutParams.MATCH_PARENT,
                                    420
                            );
                    resimLp.setMargins(18, 10, 18, 10);

                    mesajAlani.addView(onizleme, resimLp);

                    kaydirma.post(() ->
                            kaydirma.fullScroll(View.FOCUS_DOWN)
                    );

                    Toast.makeText(this, "📷 Fotoğraf eklendi", Toast.LENGTH_SHORT).show();
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
                    String mevcut = mesajKutusu.getText().toString();
                    if (mevcut.isEmpty()) {
                        mesajKutusu.setText(metin);
                    } else {
                        mesajKutusu.setText(mevcut + " " + metin);
                    }
                    mesajKutusu.setSelection(mesajKutusu.getText().length());
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

                    mesajAlani.addView(
                            onizleme,
                            resimLp
                    );

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

        super.onDestroy();
    }
}

