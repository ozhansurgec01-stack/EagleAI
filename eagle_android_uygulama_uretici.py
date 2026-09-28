from pathlib import Path
import re


class EagleAndroidUygulamaUretici:
    """Üretilmiş uygulama planından bağımsız Android projesi oluşturur."""

    def uret(self, plan, cikti_dizini):
        if not plan:
            return {
                "ok": False,
                "hata": "Plan bulunamadı.",
            }

        root = Path(cikti_dizini).resolve()
        paket = self._paket_adi(plan.get("konu"))
        varliklar = list(plan.get("varliklar") or ["kayit"])
        alanlar = dict(plan.get("alanlar") or {"kayit": ["id", "veri"]})

        islemler = list(plan.get("islemler") or [])
        ekranlar = list(plan.get("ekranlar") or [])
        gereksinimler = plan.get("gereksinimler") or {}

        gelismis_uygulama = (
            "uye" in varliklar
            and (
                "odeme" in varliklar
                or "dashboard" in ekranlar
                or "kalici_veri" in islemler
                or "odeme_gecmisi" in islemler
                or "uyelik_durumu" in islemler
            )
        )

        haber_uygulamasi = (
            "haber" in varliklar
            or "haber" in str(plan.get("konu", "")).casefold()
            or "haberler" in str(plan.get("konu", "")).casefold()
        )

        dosyalar = {
            "settings.gradle": self._settings(),
            "build.gradle": self._root_build_gradle(),
            "gradle.properties": self._gradle_properties(),
            "app/build.gradle": self._app_build_gradle(paket),
            "app/src/main/AndroidManifest.xml": self._manifest(
                paket,
                internet=haber_uygulamasi,
                sms=gelismis_uygulama,
            ),
            "app/src/main/java/"
            + paket.replace(".", "/")
            + "/MainActivity.java": (
                self._haber_main_activity(
                    paket,
                    plan.get("konu", "Haberler"),
                )
                if haber_uygulamasi
                else (
                    self._gelismis_uye_main_activity(
                        paket,
                        plan.get("konu", "Uygulama"),
                        varliklar,
                        alanlar,
                        islemler,
                        ekranlar,
                        gereksinimler,
                    )
                    if gelismis_uygulama
                    else self._main_activity(
                        paket,
                        plan.get("konu", "Uygulama"),
                        varliklar,
                        alanlar,
                    )
                )
            ),
        }

        if haber_uygulamasi:
            java_dizini = (
                "app/src/main/java/"
                + paket.replace(".", "/")
                + "/"
            )
            dosyalar[java_dizini + "NewsSource.java"] = self._news_source(paket)
            dosyalar[java_dizini + "NewsNotifier.java"] = self._news_notifier(paket)
            dosyalar[java_dizini + "NewsAlarmReceiver.java"] = self._news_alarm_receiver(paket)

        for yol, icerik in dosyalar.items():
            hedef = root / yol
            hedef.parent.mkdir(parents=True, exist_ok=True)
            hedef.write_text(icerik, encoding="utf-8")

        return {
            "ok": True,
            "proje_dizini": str(root),
            "paket": paket,
            "dosyalar": sorted(dosyalar),
            "cikti_turu": "android_proje",
        }

    @staticmethod
    def _paket_adi(konu):
        cevir = str.maketrans({
            "ç": "c", "ğ": "g", "ı": "i", "ö": "o",
            "ş": "s", "ü": "u",
            "Ç": "C", "Ğ": "G", "İ": "I", "Ö": "O",
            "Ş": "S", "Ü": "U",
        })
        metin = str(konu or "genel uygulama").translate(cevir).lower()
        parcalar = re.findall(r"[a-z0-9]+", metin)
        parcalar = [p for p in parcalar if p]
        ad = "_".join(parcalar[:4]) or "genel_uygulama"
        return "com.eagleai.generated." + ad

    @staticmethod
    def _settings():
        return """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "GeneratedApp"
include(":app")
"""

    @staticmethod
    def _root_build_gradle():
        return """plugins {
    id 'com.android.application' version '8.6.1' apply false
}
"""

    @staticmethod
    def _gradle_properties():
        return """org.gradle.jvmargs=-Xmx1024m
android.useAndroidX=true
android.aapt2FromMavenOverride=/data/data/com.termux/files/usr/bin/aapt2
"""

    @staticmethod
    def _app_build_gradle(paket):
        return f"""plugins {{
    id 'com.android.application'
}}

android {{
    namespace '{paket}'
    compileSdk 34

    defaultConfig {{
        applicationId '{paket}'
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName '1.0'
    }}
}}

dependencies {{
    implementation 'androidx.core:core:1.12.0'
}}
"""

    @staticmethod
    def _manifest(paket, internet=False, sms=False):
        izin = (
            '    <uses-permission android:name="android.permission.INTERNET" />\\n'
            if internet else ""
        )
        sms_izin = (
            '    <uses-permission android:name="android.permission.SEND_SMS" />\\n'
            if sms else ""
        )
        bildirim_izin = (
            '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\\n'
            if internet else ""
        )
        return f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android">
{izin}{sms_izin}{bildirim_izin}
    <application
        android:theme="@android:style/Theme.Material.Light.NoActionBar"
        android:label="Fitness"
        android:allowBackup="true">

        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>

        <receiver
            android:name=".NewsAlarmReceiver"
            android:exported="false" />

    </application>
</manifest>
"""
    @staticmethod
    def _news_source(paket):
        return f"""package {paket};

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

import org.json.JSONArray;
import org.json.JSONObject;
import org.xmlpull.v1.XmlPullParser;
import android.util.Xml;

public class NewsSource {{

    public interface Callback {{
        void onSuccess(JSONArray articles);
        void onError(String message);
    }}

    public static void fetch(Callback callback) {{
        new Thread(() -> {{
            HttpURLConnection connection = null;

            try {{
                String urlString =
                    "https://news.google.com/rss"
                    + "?hl=tr"
                    + "&gl=TR"
                    + "&ceid=TR:tr";

                URL url = new URL(urlString);
                connection =
                    (HttpURLConnection) url.openConnection();

                connection.setRequestMethod("GET");
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(15000);
                connection.setRequestProperty(
                    "Accept",
                    "application/rss+xml, application/xml"
                );
                connection.setRequestProperty(
                    "User-Agent",
                    "Mozilla/5.0"
                );

                int code = connection.getResponseCode();

                if (code < 200 || code >= 300) {{
                    callback.onError(
                        "Haber kaynağı HTTP " + code
                    );
                    return;
                }}

                InputStream stream =
                    connection.getInputStream();

                XmlPullParser parser = Xml.newPullParser();
                parser.setInput(stream, "UTF-8");

                JSONArray articles = new JSONArray();

                String currentTag = null;
                String title = "";
                String source = "";
                String pubDate = "";
                String link = "";

                int eventType = parser.getEventType();

                while (eventType != XmlPullParser.END_DOCUMENT) {{

                    if (eventType == XmlPullParser.START_TAG) {{
                        currentTag = parser.getName();

                        if ("item".equals(currentTag)) {{
                            title = "";
                            source = "";
                            pubDate = "";
                            link = "";
                        }}
                    }} else if (eventType == XmlPullParser.TEXT) {{
                        if ("title".equals(currentTag)) {{
                            title = parser.getText();
                        }} else if ("source".equals(currentTag)) {{
                            source = parser.getText();
                        }} else if ("pubDate".equals(currentTag)) {{
                            pubDate = parser.getText();
                        }} else if ("link".equals(currentTag)) {{
                            link = parser.getText();
                        }}
                    }} else if (eventType == XmlPullParser.END_TAG) {{
                        String tag = parser.getName();

                        if ("item".equals(tag)) {{
                            JSONObject article = new JSONObject();

                            article.put("title", title);
                            article.put("domain", source);
                            article.put("seendate", pubDate);
                            article.put("url", link);

                            articles.put(article);
                        }}

                        currentTag = null;
                    }}

                    eventType = parser.next();
                }}

                stream.close();

                callback.onSuccess(articles);

            }} catch (Exception e) {{
                callback.onError(
                    e.getClass().getSimpleName()
                    + ": "
                    + String.valueOf(e.getMessage())
                );
            }} finally {{
                if (connection != null) {{
                    connection.disconnect();
                }}
            }}
        }}).start();
    }}
}}

"""
    @staticmethod
    def _news_notifier(paket):
        return f"""package {paket};

import android.Manifest;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.os.Build;

import androidx.core.app.NotificationCompat;
import androidx.core.app.NotificationManagerCompat;

public class NewsNotifier {{
    public static final String CHANNEL_ID = "haberler";
    private static final int NOTIFICATION_ID = 20260927;

    public static void show(
        Context context,
        String title,
        String source,
        String url
    ) {{
        if (Build.VERSION.SDK_INT >= 33 &&
            context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {{
            return;
        }}

        NotificationManager manager =
            (NotificationManager) context.getSystemService(Context.NOTIFICATION_SERVICE);

        if (Build.VERSION.SDK_INT >= 26) {{
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Haber Bildirimleri",
                NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("Yeni haber bildirimleri");
            manager.createNotificationChannel(channel);
        }}

        Intent intent = new Intent(Intent.ACTION_VIEW);
        intent.setData(android.net.Uri.parse(url));

        PendingIntent pendingIntent = PendingIntent.getActivity(
            context,
            Math.abs(url.hashCode()),
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT |
            (Build.VERSION.SDK_INT >= 23 ? PendingIntent.FLAG_IMMUTABLE : 0)
        );

        String icerik = source == null || source.isEmpty()
            ? title
            : source + " • " + title;

        NotificationCompat.Builder builder =
            new NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle("Yeni haber")
                .setContentText(icerik)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(icerik))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setContentIntent(pendingIntent);

        NotificationManagerCompat.from(context)
            .notify(NOTIFICATION_ID, builder.build());
    }}
}}
"""

    @staticmethod
    def _news_alarm_receiver(paket):
        return f"""package {paket};

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;

import org.json.JSONArray;
import org.json.JSONObject;

public class NewsAlarmReceiver extends BroadcastReceiver {{

    private static final String PREFS = "haber_bildirimleri";
    private static final String BASLATILDI = "baslatildi";
    private static final String GORULEN = "gorulen_";

    @Override
    public void onReceive(Context context, Intent intent) {{
        final PendingResult pendingResult = goAsync();

        NewsSource.fetch(new NewsSource.Callback() {{
            @Override
            public void onSuccess(JSONArray articles) {{
                try {{
                SharedPreferences prefs =
                    context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);

                boolean ilkKontrol = !prefs.getBoolean(BASLATILDI, false);

                if (ilkKontrol) {{
                    SharedPreferences.Editor editor = prefs.edit();

                    for (int i = 0; i < articles.length(); i++) {{
                        try {{
                            JSONObject haber = articles.getJSONObject(i);
                            String url = haber.optString("url", "");
                            if (!url.isEmpty()) {{
                                editor.putBoolean(GORULEN + url, true);
                            }}
                        }} catch (Exception ignored) {{
                        }}
                    }}

                    editor.putBoolean(BASLATILDI, true);
                    editor.apply();
                    return;
                }}

                for (int i = 0; i < articles.length(); i++) {{
                    try {{
                        JSONObject haber = articles.getJSONObject(i);

                        String url = haber.optString("url", "");
                        String baslik = haber.optString("title", "Yeni haber");
                        String kaynak = haber.optString("domain", "");

                        if (url.isEmpty()) {{
                            continue;
                        }}

                        if (prefs.getBoolean(GORULEN + url, false)) {{
                            continue;
                        }}

                        prefs.edit()
                            .putBoolean(GORULEN + url, true)
                            .apply();

                        NewsNotifier.show(
                            context,
                            baslik,
                            kaynak,
                            url
                        );

                        break;
                    }} catch (Exception ignored) {{
                    }}
                }}
                }} finally {{
                    pendingResult.finish();
                }}
            }}

            @Override
            public void onError(String message) {{
                // Arka plan kontrol hatası sessizce geçilir.
                pendingResult.finish();
            }}
        }});
    }}
}}
"""

    @staticmethod
    def _haber_main_activity(paket, konu):
        return f'''package {paket};

import android.app.Activity;
import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.pm.PackageManager;
import android.Manifest;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

public class MainActivity extends Activity {{

    private LinearLayout liste;
    private TextView durum;

    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);

        LinearLayout ana = new LinearLayout(this);
        ana.setOrientation(LinearLayout.VERTICAL);
        ana.setPadding(18, 18, 18, 18);
        ana.setBackgroundColor(Color.rgb(248, 249, 251));

        Button yenile = new Button(this);
        yenile.setText("HABERLERİ YENİLE");
        yenile.setTextSize(16);
        yenile.setAllCaps(false);

        ana.addView(
            yenile,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            )
        );

        durum = new TextView(this);
        durum.setText("Güncel haberler yükleniyor...");
        durum.setTextSize(15);
        durum.setTextColor(Color.rgb(80, 80, 80));
        durum.setPadding(4, 12, 4, 12);
        ana.addView(durum);

        ScrollView kaydir = new ScrollView(this);

        liste = new LinearLayout(this);
        liste.setOrientation(LinearLayout.VERTICAL);
        kaydir.addView(liste);

        ana.addView(
            kaydir,
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                0,
                1
            )
        );

        yenile.setOnClickListener(v -> haberleriYukle());

        setContentView(ana);
        haberleriYukle();
        bildirimleriBaslat();
    }}

    private void bildirimleriBaslat() {{
        if (android.os.Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {{
            requestPermissions(
                new String[]{{Manifest.permission.POST_NOTIFICATIONS}},
                7001
            );
        }}

        AlarmManager alarmManager =
            (AlarmManager) getSystemService(Context.ALARM_SERVICE);

        Intent intent = new Intent(this, NewsAlarmReceiver.class);

        PendingIntent pendingIntent = PendingIntent.getBroadcast(
            this,
            7002,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT |
            (android.os.Build.VERSION.SDK_INT >= 23
                ? PendingIntent.FLAG_IMMUTABLE : 0)
        );

        long baslangic =
            android.os.SystemClock.elapsedRealtime()
            + 15L * 60L * 1000L;

        alarmManager.setInexactRepeating(
            AlarmManager.ELAPSED_REALTIME_WAKEUP,
            baslangic,
            15L * 60L * 1000L,
            pendingIntent
        );
    }}

    private void haberleriYukle() {{
        durum.setText("Güncel haberler yükleniyor...");
        liste.removeAllViews();

        NewsSource.fetch(new NewsSource.Callback() {{

            @Override
            public void onSuccess(JSONArray articles) {{
                runOnUiThread(() -> haberleriGoster(articles));
            }}

            @Override
            public void onError(String message) {{
                runOnUiThread(() -> {{
                    durum.setText("Haberler alınamadı.");

                    Toast.makeText(
                        MainActivity.this,
                        message,
                        Toast.LENGTH_LONG
                    ).show();
                }});
            }}
        }});
    }}

    private void haberleriGoster(JSONArray articles) {{
        liste.removeAllViews();

        if (articles.length() == 0) {{
            durum.setText("Güncel haber bulunamadı.");
            return;
        }}

        int gosterilen = 0;

        int[][] kartRenkleri = {{
            {{238, 246, 255}},
            {{245, 240, 255}},
            {{238, 250, 244}},
            {{255, 247, 235}},
            {{255, 240, 243}}
        }};

        int[][] kaynakRenkleri = {{
            {{25, 103, 210}},
            {{123, 63, 170}},
            {{25, 125, 70}},
            {{190, 105, 20}},
            {{190, 55, 85}}
        }};

        for (int i = 0; i < articles.length(); i++) {{
            try {{
                JSONObject haber = articles.getJSONObject(i);

                String baslik = haber.optString(
                    "title",
                    "Başlıksız haber"
                );

                String url = haber.optString("url", "");
                String kaynak = haber.optString("domain", "");
                String tarih = haber.optString("seendate", "");

                int renkIndex =
                    gosterilen % kartRenkleri.length;

                LinearLayout kart = new LinearLayout(this);
                kart.setOrientation(LinearLayout.VERTICAL);
                kart.setPadding(18, 18, 18, 18);

                kart.setBackgroundColor(
                    Color.rgb(
                        kartRenkleri[renkIndex][0],
                        kartRenkleri[renkIndex][1],
                        kartRenkleri[renkIndex][2]
                    )
                );

                TextView baslikView = new TextView(this);
                baslikView.setText(baslik);
                baslikView.setTextSize(18);
                baslikView.setTextColor(Color.rgb(35, 35, 35));
                baslikView.setTypeface(
                    Typeface.DEFAULT,
                    Typeface.BOLD
                );
                kart.addView(baslikView);

                if (!kaynak.isEmpty()) {{
                    TextView kaynakView = new TextView(this);
                    kaynakView.setText(kaynak);
                    kaynakView.setTextSize(14);
                    kaynakView.setTypeface(
                        Typeface.DEFAULT,
                        Typeface.BOLD
                    );
                    kaynakView.setPadding(0, 8, 0, 0);

                    kaynakView.setTextColor(
                        Color.rgb(
                            kaynakRenkleri[renkIndex][0],
                            kaynakRenkleri[renkIndex][1],
                            kaynakRenkleri[renkIndex][2]
                        )
                    );

                    kart.addView(kaynakView);
                }}

                if (!tarih.isEmpty()) {{
                    TextView tarihView = new TextView(this);
                    tarihView.setText(tarih);
                    tarihView.setTextSize(12);
                    tarihView.setTextColor(
                        Color.rgb(100, 100, 100)
                    );
                    tarihView.setPadding(0, 4, 0, 0);
                    kart.addView(tarihView);
                }}

                kart.setClickable(true);

                kart.setOnClickListener(v -> {{
                    if (url.isEmpty()) {{
                        Toast.makeText(
                            MainActivity.this,
                            "Haber bağlantısı bulunamadı.",
                            Toast.LENGTH_SHORT
                        ).show();
                        return;
                    }}

                    try {{
                        Intent intent = new Intent(
                            Intent.ACTION_VIEW,
                            Uri.parse(url)
                        );
                        startActivity(intent);
                    }} catch (Exception e) {{
                        Toast.makeText(
                            MainActivity.this,
                            "Haber açılamadı.",
                            Toast.LENGTH_SHORT
                        ).show();
                    }}
                }});

                LinearLayout.LayoutParams kartParams =
                    new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    );

                kartParams.setMargins(0, 0, 0, 12);
                liste.addView(kart, kartParams);

                gosterilen++;

                if (gosterilen >= 20) {{
                    break;
                }}

            }} catch (Exception ignored) {{
                // Tek bir bozuk haber diğerlerini engellemesin.
            }}
        }}

        durum.setText(
            gosterilen + " güncel haber gösteriliyor."
        );
    }}
}}
'''
    def _main_activity(self, paket, konu, varliklar, alanlar):
        ilk_varlik = varliklar[0]
        alan_listesi = [
            alan for alan in alanlar.get(ilk_varlik, [])
            if alan != "id"
        ]

        alanlar_java = ", ".join(
            '"' + alan.replace('"', '\\"') + '"'
            for alan in alan_listesi
        )

        return f"""package {paket};

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.View;
import android.view.animation.AlphaAnimation;
import android.view.animation.Animation;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;

public class MainActivity extends Activity {{

    private final List<String> kayitlar = new ArrayList<>();
    private LinearLayout liste;

    private static final String[] ALANLAR = new String[] {{
        {alanlar_java}
    }};

    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);

        LinearLayout ana = new LinearLayout(this);
        ana.setOrientation(LinearLayout.VERTICAL);
        ana.setPadding(18, 18, 18, 18);
        ana.setBackgroundColor(Color.rgb(248, 249, 251));

        TextView baslik = new TextView(this);
        baslik.setText("{str(konu).replace(chr(92), chr(92) + chr(92)).replace(chr(34), chr(92) + chr(34)).replace(chr(10), chr(92) + 'n').replace(chr(13), chr(92) + 'r')}");
        baslik.setTextSize(24);
        baslik.setTextColor(Color.rgb(35, 35, 35));
        baslik.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        baslik.setPadding(4, 4, 4, 14);
        ana.addView(baslik);

        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);

        final List<EditText> alanKutulari = new ArrayList<>();

        for (String alan : ALANLAR) {{
            EditText input = new EditText(this);
            input.setHint(alan);
            input.setTextSize(16);
            input.setSingleLine(true);
            input.setPadding(12, 10, 12, 10);

            LinearLayout.LayoutParams inputParams =
                new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                );
            inputParams.setMargins(0, 0, 0, 8);

            form.addView(input, inputParams);
            alanKutulari.add(input);
        }}

        Button ekle = new Button(this);
        ekle.setText("Ekle");
        ekle.setTextSize(16);
        ekle.setAllCaps(false);

        LinearLayout.LayoutParams butonParams =
            new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            );
        butonParams.setMargins(0, 4, 0, 12);

        form.addView(ekle, butonParams);

        ana.addView(form);

        liste = new LinearLayout(this);
        liste.setOrientation(LinearLayout.VERTICAL);
        ana.addView(liste);

        ekle.setOnClickListener(new View.OnClickListener() {{
            @Override
            public void onClick(View v) {{
                StringBuilder kayit = new StringBuilder();

                for (int i = 0; i < ALANLAR.length; i++) {{
                    if (i > 0) {{
                        kayit.append(" | ");
                    }}
                    kayit.append(ALANLAR[i])
                         .append(": ")
                         .append(alanKutulari.get(i).getText().toString());
                }}

                kayitlar.add(kayit.toString());

                int[][] kayitRenkleri = {{
                    {{238, 246, 255}},
                    {{245, 240, 255}},
                    {{238, 250, 244}},
                    {{255, 247, 235}},
                    {{255, 240, 243}}
                }};

                int renkIndex =
                    (kayitlar.size() - 1) % kayitRenkleri.length;

                LinearLayout kart = new LinearLayout(MainActivity.this);
                kart.setOrientation(LinearLayout.VERTICAL);
                kart.setPadding(16, 16, 16, 16);
                kart.setBackgroundColor(
                    Color.rgb(
                        kayitRenkleri[renkIndex][0],
                        kayitRenkleri[renkIndex][1],
                        kayitRenkleri[renkIndex][2]
                    )
                );

                TextView satir = new TextView(MainActivity.this);
                satir.setText(kayit.toString());
                satir.setTextSize(16);
                satir.setTextColor(Color.rgb(35, 35, 35));
                kart.addView(satir);

                LinearLayout.LayoutParams kartParams =
                    new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                    );
                kartParams.setMargins(0, 0, 0, 10);

                liste.addView(kart, kartParams);

                for (EditText input : alanKutulari) {{
                    input.setText("");
                }}

                Toast.makeText(
                    MainActivity.this,
                    "Kayıt eklendi",
                    Toast.LENGTH_SHORT
                ).show();
            }}
        }});

        setContentView(ana);
    }}
}}
"""


    def _gelismis_uye_main_activity(
        self,
        paket,
        konu,
        varliklar,
        alanlar,
        islemler,
        ekranlar,
        gereksinimler,
    ):
        """
        Üye takip uygulamaları için kalıcı, çevrimdışı çalışan Android ekranı.
        Haber/generic üretim akışlarından bağımsızdır.
        """
        return f"""package {paket};

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

public class MainActivity extends Activity {{

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
    protected void onCreate(Bundle savedInstanceState) {{
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

        arama.addTextChangedListener(new android.text.TextWatcher() {{
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {{}}
            public void onTextChanged(CharSequence s, int start, int before, int count) {{
                listele(s.toString());
            }}
            public void afterTextChanged(android.text.Editable s) {{}}
        }});

        uyeSekme.setOnClickListener(v -> {{
            uyelerEkrani.setVisibility(View.VISIBLE);
            odemelerEkrani.setVisibility(View.GONE);
            renkliButon(uyeSekme, Color.rgb(25, 118, 210), Color.WHITE);
            renkliButon(odemeSekme, Color.rgb(96, 125, 139), Color.WHITE);
        }});

        odemeSekme.setOnClickListener(v -> {{
            uyelerEkrani.setVisibility(View.GONE);
            odemelerEkrani.setVisibility(View.VISIBLE);
            renkliButon(uyeSekme, Color.rgb(96, 125, 139), Color.WHITE);
            renkliButon(odemeSekme, Color.rgb(25, 118, 210), Color.WHITE);
            odemeleriGuncelle();
        }});


        yeni.setOnClickListener(v -> uyeFormu(-1));

        arama.addTextChangedListener(new android.text.TextWatcher() {{
            public void beforeTextChanged(CharSequence s, int start, int count, int after) {{}}
            public void onTextChanged(CharSequence s, int start, int before, int count) {{
                listele(s.toString());
            }}
            public void afterTextChanged(android.text.Editable s) {{}}
        }});

        setContentView(ana);
        listele("");

        if (!"🟡 Bugün Bitiyor: 0".equals(bugun.getText().toString())) {{
            new AlertDialog.Builder(this)
                .setTitle("⚠️ Üyelik Uyarısı")
                .setMessage("Bugün süresi dolacak üyeler var.\\n\\nÜye listesinden kontrol edebilirsiniz.")
                .setPositiveButton("Tamam", null)
                .show();
        }}
    }}

    private void renkliButon(Button b, int arkaPlan, int yazi) {{
        b.setTextColor(yazi);
        b.setAllCaps(false);

        GradientDrawable g = new GradientDrawable();
        g.setColor(arkaPlan);
        g.setCornerRadius(22);
        b.setBackground(g);
        b.setPadding(14, 8, 14, 8);
    }}

    private String durumIkonu(String durum) {{
        if ("Aktif".equals(durum)) return "🟢";
        if ("Bugün Bitiyor".equals(durum)) return "🟡";
        if ("Yaklaşıyor".equals(durum)) return "🟠";
        if ("Süresi Doldu".equals(durum)) return "🔴";
        return "⚪";
    }}

    private GradientDrawable kartArkaPlan(String durum) {{
        int renk = Color.rgb(230, 235, 242);

        if ("Aktif".equals(durum)) {{
            renk = Color.rgb(190, 235, 200);
        }}
        if ("Bugün Bitiyor".equals(durum)) {{
            renk = Color.rgb(255, 235, 150);
        }}
        if ("Yaklaşıyor".equals(durum)) {{
            renk = Color.rgb(255, 220, 120);
        }}
        if ("Süresi Doldu".equals(durum)) {{
            renk = Color.rgb(255, 175, 175);
        }}

        GradientDrawable g = new GradientDrawable();
        g.setColor(renk);
        g.setCornerRadius(24);
        g.setStroke(2, Color.rgb(220, 225, 232));
        return g;
    }}

    private TextView kutu(String metin) {{
        TextView t = new TextView(this);
        t.setText(metin);
        t.setTextSize(16);
        t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        t.setTextColor(Color.rgb(35, 35, 35));
        t.setPadding(14, 12, 14, 12);
        return t;
    }}

    private void yanipSonuyor(View hedef) {{
        AlphaAnimation anim = new AlphaAnimation(1.0f, 0.25f);
        anim.setDuration(550);
        anim.setRepeatMode(Animation.REVERSE);
        anim.setRepeatCount(Animation.INFINITE);
        hedef.startAnimation(anim);
    }}

    private void listele(String sorgu) {{
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
            new String[] {{
                "%" + sorgu + "%",
                "%" + sorgu + "%",
                "%" + sorgu + "%"
            }}
        );

        while (c.moveToNext()) {{
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
                "\\n📞 " + telefon +
                "\\n📅 " + baslangic + " → " + bitis +
                "\\n" + durumIkonu(durum) + " " + durum +
                (notlar.isEmpty() ? "" : "\\n📝 " + notlar)
            );
            bilgi.setTextSize(16);
            bilgi.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            bilgi.setTextColor(Color.rgb(35, 35, 35));

            if ("Bugün Bitiyor".equals(durum)) {{
                yanipSonuyor(bilgi);
            }}

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

            Button[] butonDizisi = {{
                duzenle, yenile, odeme, gecmis, sms, sil
            }};

            for (Button buton : butonDizisi) {{
                buton.setMinWidth(0);
                buton.setMinimumWidth(0);
                buton.setMinHeight(0);
                buton.setMinimumHeight(0);
                buton.setTextSize(10);
                buton.setGravity(android.view.Gravity.CENTER);
                buton.setPadding(0, 4, 0, 4);
                buton.setIncludeFontPadding(false);
            }}

            for (Button buton : butonDizisi) {{
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
            }}

            kart.addView(butonlar);

            LinearLayout.LayoutParams lp =
                new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                );
            lp.setMargins(0, 0, 0, 12);
            liste.addView(kart, lp);
        }}

        c.close();

        toplam.setText("Toplam Üye: " + toplamSayi);
        aktif.setText("Aktif Üye: " + aktifSayi);
        bugun.setText("🟡 Bugün Bitiyor: " + bugunSayi);

        bugun.clearAnimation();
        if (bugunSayi > 0) {{
            yanipSonuyor(bugun);
        }}

        yaklasan.setText("Süresi Yaklaşan: " + yaklasanSayi);
        dolan.setText("Süresi Dolan: " + dolanSayi);
    }}

    private String durumHesapla(String bitis) {{
        try {{
            String temiz = bitis == null ? "" : bitis.trim();

            String[] formatlar = {{
                "yyyy-MM-dd",
                "dd.MM.yyyy",
                "dd/MM/yyyy",
                "dd-MM-yyyy"
            }};

            java.util.Date hedef = null;

            for (String desen : formatlar) {{
                try {{
                    java.text.SimpleDateFormat f =
                        new java.text.SimpleDateFormat(desen);
                    f.setLenient(false);
                    hedef = f.parse(temiz);
                    if (hedef != null) break;
                }} catch (Exception ignored) {{
                }}
            }}

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
        }} catch (Exception e) {{
            return "Bilinmiyor";
        }}
    }}

    private void uyeFormu(int id) {{
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

        if (id >= 0) {{
            Cursor c = db.getReadableDatabase().rawQuery(
                "SELECT ad, soyad, telefon, notlar, baslangic, bitis " +
                "FROM uyeler WHERE id=?",
                new String[]{{String.valueOf(id)}}
            );
            if (c.moveToFirst()) {{
                ad.setText(c.getString(0));
                soyad.setText(c.getString(1));
                telefon.setText(c.getString(2));
                notlar.setText(c.getString(3));
                baslangic.setText(c.getString(4));
                bitis.setText(c.getString(5));
            }}
            c.close();
        }}

        new AlertDialog.Builder(this)
            .setTitle(id < 0 ? "Yeni Üye" : "Üye Düzenle")
            .setView(form)
            .setPositiveButton("Kaydet", (dialog, which) -> {{
                ContentValues v = new ContentValues();
                v.put("ad", ad.getText().toString().trim());
                v.put("soyad", soyad.getText().toString().trim());
                v.put("telefon", telefon.getText().toString().trim());
                v.put("notlar", notlar.getText().toString().trim());
                v.put("baslangic", baslangic.getText().toString().trim());
                v.put("bitis", bitis.getText().toString().trim());

                if (id < 0) {{
                    db.getWritableDatabase().insert("uyeler", null, v);
                    Toast.makeText(this, "Üye eklendi", Toast.LENGTH_SHORT).show();
                }} else {{
                    db.getWritableDatabase().update(
                        "uyeler", v, "id=?", new String[]{{String.valueOf(id)}}
                    );
                    Toast.makeText(this, "Üye güncellendi", Toast.LENGTH_SHORT).show();
                }}
                listele(arama.getText().toString());
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private EditText alan(String ipucu) {{
        EditText e = new EditText(this);
        e.setHint(ipucu);
        e.setSingleLine(true);
        return e;
    }}

    private void uyeSil(int id) {{
        new AlertDialog.Builder(this)
            .setTitle("Üye silinsin mi?")
            .setMessage("Bu işlem üyeyi ve bağlı ödeme kayıtlarını kaldırır.")
            .setPositiveButton("Sil", (d, w) -> {{
                SQLiteDatabase sql = db.getWritableDatabase();
                sql.delete("odemeler", "uye_id=?", new String[]{{String.valueOf(id)}});
                sql.delete("uyeler", "id=?", new String[]{{String.valueOf(id)}});
                listele(arama.getText().toString());
                Toast.makeText(this, "Üye silindi", Toast.LENGTH_SHORT).show();
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private void uyelikYenile(int id) {{
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);

        EditText bitis = alan("Yeni bitiş tarihi (YYYY-AA-GG)");
        form.addView(bitis);

        new AlertDialog.Builder(this)
            .setTitle("Üyelik Yenile")
            .setView(form)
            .setPositiveButton("Yenile", (d, w) -> {{
                ContentValues v = new ContentValues();
                v.put("bitis", bitis.getText().toString().trim());
                db.getWritableDatabase().update(
                    "uyeler", v, "id=?", new String[]{{String.valueOf(id)}}
                );
                listele(arama.getText().toString());
                Toast.makeText(this, "Üyelik yenilendi", Toast.LENGTH_SHORT).show();
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private LinearLayout odemeSekmesiOlustur() {{
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

        ekran.setTag(new Object[]{{toplam, adet, liste}});
        return ekran;
    }}

    private double tutarSayiyaCevir(String metin) {{
        if (metin == null) return 0.0;

        String s = metin.trim()
            .replace("TL", "")
            .replace("₺", "")
            .replace(" ", "");

        if (s.isEmpty()) return 0.0;

        try {{
            int virgul = s.lastIndexOf(',');
            int nokta = s.lastIndexOf('.');

            if (virgul >= 0 && nokta >= 0) {{
                if (virgul > nokta) {{
                    s = s.replace(".", "").replace(",", ".");
                }} else {{
                    s = s.replace(",", "");
                }}
            }} else if (virgul >= 0) {{
                s = s.replace(",", ".");
            }} else if (nokta >= 0) {{
                int ondalik = s.length() - nokta - 1;
                if (ondalik == 3) {{
                    s = s.replace(".", "");
                }}
            }}

            return Double.parseDouble(s);
        }} catch (Exception e) {{
            return 0.0;
        }}
    }}

    private void odemeleriGuncelle() {{
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

        while (toplamCursor.moveToNext()) {{
            String tutarMetni = toplamCursor.getString(0);
            String tarihMetni = toplamCursor.getString(1);

            genelToplamTutar += tutarSayiyaCevir(tutarMetni);
            genelOdemeSayisi++;

            if (tarihMetni == null) continue;

            String temizTarih = tarihMetni.trim()
                .replace("/", ".")
                .replace("-", ".");

            String[] parcalarTarih = temizTarih.split("\\\\.");

            int tarihYil = -1;
            int tarihAy = -1;

            try {{
                if (parcalarTarih.length == 3) {{
                    if (parcalarTarih[0].length() == 4) {{
                        tarihYil = Integer.parseInt(parcalarTarih[0]);
                        tarihAy = Integer.parseInt(parcalarTarih[1]);
                    }} else if (parcalarTarih[2].length() == 4) {{
                        tarihYil = Integer.parseInt(parcalarTarih[2]);
                        tarihAy = Integer.parseInt(parcalarTarih[1]);
                    }}
                }}
            }} catch (Exception ignored) {{}}

            if (tarihYil == buYil && tarihAy == buAy) {{
                toplamTutar += tutarSayiyaCevir(tutarMetni);
                odemeSayisi++;
            }}
        }}

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

        while (c.moveToNext()) {{
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
                "\\n💰 " + (tutar == null ? "" : tutar) + " TL" +
                "\\n📆 " + aySayisi + " Ay" +
                "\\n📅 " + (tarih == null ? "" : tarih) +
                ((aciklama == null || aciklama.trim().isEmpty())
                    ? ""
                    : "\\n📝 " + aciklama)
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
        }}

        c.close();

        if (liste.getChildCount() == 0) {{
            TextView bos = new TextView(this);
            bos.setText("Henüz ödeme kaydı bulunmuyor.");
            bos.setTextSize(16);
            bos.setTextColor(Color.rgb(90, 90, 90));
            bos.setPadding(12, 20, 12, 20);
            liste.addView(bos);
        }}
    }}

    private void smsUyeDuyuru(String ad, String soyad, String telefon) {{
        if (telefon == null || telefon.trim().isEmpty()) {{
            Toast.makeText(
                this,
                "Bu üyeye ait telefon numarası bulunamadı.",
                Toast.LENGTH_LONG
            ).show();
            return;
        }}

        final EditText mesaj = new EditText(this);
        mesaj.setHint("SMS mesajı");
        mesaj.setGravity(android.view.Gravity.TOP);
        mesaj.setMinLines(4);
        mesaj.setSingleLine(false);

        String adSoyad = (ad + " " + (soyad == null ? "" : soyad)).trim();

        new AlertDialog.Builder(this)
            .setTitle("📩 " + adSoyad + " — SMS")
            .setView(mesaj)
            .setPositiveButton("Gönder", (d, w) -> {{
                String metin = mesaj.getText().toString().trim();

                if (metin.isEmpty()) {{
                    Toast.makeText(
                        this,
                        "SMS mesajı boş olamaz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }}

                bekleyenSmsTelefon = telefon.trim();
                bekleyenSmsUyeMetni = metin;

                if (android.os.Build.VERSION.SDK_INT >= 23 &&
                    checkSelfPermission(android.Manifest.permission.SEND_SMS)
                        != PackageManager.PERMISSION_GRANTED) {{

                    requestPermissions(
                        new String[]{{android.Manifest.permission.SEND_SMS}},
                        SMS_UYE_IZIN_KODU
                    );
                    return;
                }}

                smsTekUyeGonder(bekleyenSmsTelefon, bekleyenSmsUyeMetni);
                bekleyenSmsTelefon = null;
                bekleyenSmsUyeMetni = null;
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private void smsTekUyeGonder(String telefon, String metin) {{
        if (telefon == null || metin == null ||
            telefon.trim().isEmpty() || metin.trim().isEmpty()) {{
            return;
        }}

        String numara = telefon.trim().replaceAll("[^0-9+]", "");

        if (numara.startsWith("+")) {{
            numara = numara.substring(1);
        }} else if (numara.startsWith("0") && numara.length() == 11) {{
            numara = "90" + numara.substring(1);
        }} else if (numara.length() == 10 && numara.startsWith("5")) {{
            numara = "90" + numara;
        }}

        if (numara.length() != 12 || !numara.startsWith("90")) {{
            Toast.makeText(
                this,
                "Geçerli bir telefon numarası bulunamadı.",
                Toast.LENGTH_LONG
            ).show();
            return;
        }}

        try {{
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

        }} catch (SecurityException e) {{
            Toast.makeText(
                this,
                "SMS gönderme izni verilmedi.",
                Toast.LENGTH_LONG
            ).show();
        }} catch (Exception e) {{
            Toast.makeText(
                this,
                "SMS gönderimi başlatılamadı.",
                Toast.LENGTH_LONG
            ).show();
        }}
    }}

    private void smsDuyuru() {{
        final EditText mesaj = new EditText(this);
        mesaj.setHint("Duyuru mesajı");
        mesaj.setGravity(android.view.Gravity.TOP);
        mesaj.setMinLines(4);
        mesaj.setSingleLine(false);

        new AlertDialog.Builder(this)
            .setTitle("📩 SMS Duyuru")
            .setView(mesaj)
            .setPositiveButton("Devam", (d, w) -> {{
                String metin = mesaj.getText().toString().trim();

                if (metin.isEmpty()) {{
                    Toast.makeText(
                        this,
                        "Duyuru mesajı boş olamaz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }}

                bekleyenSmsMetni = metin;
                smsDuyuruHazirla();
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private void smsDuyuruHazirla() {{
        if (android.os.Build.VERSION.SDK_INT >= 23 &&
            checkSelfPermission(android.Manifest.permission.SEND_SMS)
                != PackageManager.PERMISSION_GRANTED) {{

            requestPermissions(
                new String[]{{android.Manifest.permission.SEND_SMS}},
                SMS_IZIN_KODU
            );
            return;
        }}

        smsDuyuruOnayla();
    }}

    private void smsDuyuruOnayla() {{
        if (bekleyenSmsMetni == null || bekleyenSmsMetni.trim().isEmpty()) {{
            return;
        }}

        java.util.LinkedHashSet<String> numaralar =
            new java.util.LinkedHashSet<>();

        Cursor c = db.getReadableDatabase().query(
            "uyeler",
            new String[]{{"telefon"}},
            "telefon IS NOT NULL AND TRIM(telefon) <> ''",
            null,
            null,
            null,
            "id ASC"
        );

        while (c.moveToNext()) {{
            String telefon = c.getString(0);

            if (telefon == null) {{
                continue;
            }}

            String numara = telefon.trim();
            numara = numara.replaceAll("[^0-9+]", "");

            if (numara.startsWith("+")) {{
                numara = numara.substring(1);
            }} else if (numara.startsWith("0") && numara.length() == 11) {{
                numara = "90" + numara.substring(1);
            }} else if (numara.length() == 10 && numara.startsWith("5")) {{
                numara = "90" + numara;
            }}

            if (numara.length() == 12 && numara.startsWith("90")) {{
                numaralar.add(numara);
            }}
        }}

        c.close();

        if (numaralar.isEmpty()) {{
            Toast.makeText(
                this,
                "SMS gönderilecek geçerli üye telefonu bulunamadı.",
                Toast.LENGTH_LONG
            ).show();
            bekleyenSmsMetni = null;
            return;
        }}

        final int adet = numaralar.size();

        new AlertDialog.Builder(this)
            .setTitle("📩 SMS Gönder")
            .setMessage(
                adet + " üyeye SMS gönderilecek.\\n\\n" +
                "Mesaj:\\n" + bekleyenSmsMetni
            )
            .setPositiveButton("Gönder", (d, w) -> {{
                smsleriGonder(numaralar, bekleyenSmsMetni);
                bekleyenSmsMetni = null;
            }})
            .setNegativeButton("İptal", (d, w) -> {{
                bekleyenSmsMetni = null;
            }})
            .show();
    }}

    private void smsleriGonder(
        java.util.LinkedHashSet<String> numaralar,
        String metin
    ) {{
        if (metin == null || metin.trim().isEmpty()) {{
            return;
        }}

        try {{
            android.telephony.SmsManager smsManager =
                android.telephony.SmsManager.getDefault();

            java.util.ArrayList<String> parcalar =
                smsManager.divideMessage(metin);

            int basarili = 0;

            for (String numara : numaralar) {{
                try {{
                    smsManager.sendMultipartTextMessage(
                        numara,
                        null,
                        parcalar,
                        null,
                        null
                    );
                    basarili++;
                }} catch (Exception ignored) {{
                }}
            }}

            Toast.makeText(
                this,
                basarili + " üyeye SMS gönderimi başlatıldı.",
                Toast.LENGTH_LONG
            ).show();

        }} catch (SecurityException e) {{
            Toast.makeText(
                this,
                "SMS gönderme izni verilmedi.",
                Toast.LENGTH_LONG
            ).show();
        }} catch (Exception e) {{
            Toast.makeText(
                this,
                "SMS gönderimi başlatılamadı.",
                Toast.LENGTH_LONG
            ).show();
        }}
    }}

    @Override
    public void onRequestPermissionsResult(
        int requestCode,
        String[] permissions,
        int[] grantResults
    ) {{
        super.onRequestPermissionsResult(
            requestCode,
            permissions,
            grantResults
        );

        if (requestCode == SMS_IZIN_KODU) {{
            if (grantResults.length > 0 &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED) {{

                smsDuyuruOnayla();

            }} else {{
                bekleyenSmsMetni = null;

                Toast.makeText(
                    this,
                    "SMS gönderme izni verilmedi.",
                    Toast.LENGTH_LONG
                ).show();
            }}

            return;
        }}

        if (requestCode == SMS_UYE_IZIN_KODU) {{
            if (grantResults.length > 0 &&
                grantResults[0] == PackageManager.PERMISSION_GRANTED) {{

                smsTekUyeGonder(
                    bekleyenSmsTelefon,
                    bekleyenSmsUyeMetni
                );

            }} else {{
                Toast.makeText(
                    this,
                    "SMS gönderme izni verilmedi.",
                    Toast.LENGTH_LONG
                ).show();
            }}

            bekleyenSmsTelefon = null;
            bekleyenSmsUyeMetni = null;
        }}
    }}

    private void whatsappUyeDuyuru(String ad, String soyad, String telefon) {{
        final EditText mesaj = new EditText(this);
        mesaj.setHint("Mesajı yazın");
        mesaj.setGravity(android.view.Gravity.TOP);
        mesaj.setMinLines(4);
        mesaj.setSingleLine(false);

        new AlertDialog.Builder(this)
            .setTitle("💬 " + ad + " " + soyad)
            .setView(mesaj)
            .setPositiveButton("WhatsApp'ı Aç", (d, w) -> {{
                String metin = mesaj.getText().toString().trim();

                if (metin.isEmpty()) {{
                    Toast.makeText(
                        this,
                        "Mesaj boş olamaz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }}

                String numara = telefon == null ? "" : telefon.trim();
                numara = numara.replaceAll("[^0-9+]", "");

                if (numara.startsWith("+")) {{
                    numara = numara.substring(1);
                }} else if (numara.startsWith("0") && numara.length() == 11) {{
                    numara = "90" + numara.substring(1);
                }} else if (numara.length() == 10 && numara.startsWith("5")) {{
                    numara = "90" + numara;
                }}

                if (numara.length() < 12 || !numara.startsWith("90")) {{
                    Toast.makeText(
                        this,
                        "Üyenin telefon numarası geçersiz.",
                        Toast.LENGTH_SHORT
                    ).show();
                    return;
                }}

                try {{
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
                }} catch (Exception e) {{
                    Toast.makeText(
                        this,
                        "WhatsApp açılamadı.",
                        Toast.LENGTH_SHORT
                    ).show();
                }}
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private void odemeEkle(int uyeId) {{
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
            .setPositiveButton("Kaydet", (d, w) -> {{
                ContentValues v = new ContentValues();
                v.put("uye_id", uyeId);
                v.put("tutar", tutar.getText().toString().trim());
                v.put("tarih", tarih.getText().toString().trim());
                v.put("aciklama", aciklama.getText().toString().trim());
                String ayMetni = aySayisi.getText().toString().trim();
                int ay = 1;

                try {{
                    ay = Integer.parseInt(ayMetni);
                }} catch (Exception ignored) {{}}

                if (ay < 1) {{
                    ay = 1;
                }}

                v.put("ay_sayisi", ay);

                db.getWritableDatabase().insert("odemeler", null, v);

                // Ödenen toplam süreyi başlangıç tarihinden hesapla.
                if (ay > 1) {{
                    Cursor uyeCursor = db.getReadableDatabase().rawQuery(
                        "SELECT baslangic FROM uyeler WHERE id=?",
                        new String[]{{String.valueOf(uyeId)}}
                    );

                    if (uyeCursor.moveToFirst()) {{
                        String baslangicMetni = uyeCursor.getString(0);

                        try {{
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
                                new String[]{{String.valueOf(uyeId)}}
                            );
                        }} catch (Exception ignored) {{
                        }}
                    }}

                    uyeCursor.close();
                }}

                Toast.makeText(
                    this,
                    "Ödeme kaydedildi",
                    Toast.LENGTH_SHORT
                ).show();
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private void odemeDuzenle(int odemeId, int uyeId) {{
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
            new String[]{{String.valueOf(odemeId)}}
        );

        if (c.moveToFirst()) {{
            tutar.setText(c.getString(0));
            tarih.setText(c.getString(1));
            aciklama.setText(c.getString(2));
            aySayisi.setText(String.valueOf(c.getInt(3)));
        }}
        c.close();

        new AlertDialog.Builder(this)
            .setTitle("Ödeme Düzenle")
            .setView(form)
            .setPositiveButton("Kaydet", (d, w) -> {{
                String ayMetni = aySayisi.getText().toString().trim();
                int ay = 1;

                try {{
                    ay = Integer.parseInt(ayMetni);
                }} catch (Exception ignored) {{}}

                if (ay < 1) {{
                    ay = 1;
                }}

                ContentValues v = new ContentValues();
                v.put("tutar", tutar.getText().toString().trim());
                v.put("tarih", tarih.getText().toString().trim());
                v.put("aciklama", aciklama.getText().toString().trim());
                v.put("ay_sayisi", ay);

                db.getWritableDatabase().update(
                    "odemeler",
                    v,
                    "id=?",
                    new String[]{{String.valueOf(odemeId)}}
                );

                Cursor uyeCursor = db.getReadableDatabase().rawQuery(
                    "SELECT baslangic FROM uyeler WHERE id=?",
                    new String[]{{String.valueOf(uyeId)}}
                );

                if (uyeCursor.moveToFirst()) {{
                    String baslangicMetni = uyeCursor.getString(0);

                    try {{
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
                            new String[]{{String.valueOf(uyeId)}}
                        );
                    }} catch (Exception ignored) {{
                    }}
                }}

                uyeCursor.close();

                odemeleriGuncelle();

                Toast.makeText(
                    this,
                    "Ödeme güncellendi",
                    Toast.LENGTH_SHORT
                ).show();
            }})
            .setNegativeButton("İptal", null)
            .show();
    }}

    private void odemeGecmisi(int uyeId) {{
        Cursor c = db.getReadableDatabase().rawQuery(
            "SELECT tutar, tarih, aciklama FROM odemeler " +
            "WHERE uye_id=? ORDER BY id DESC",
            new String[]{{String.valueOf(uyeId)}}
        );

        StringBuilder metin = new StringBuilder();

        while (c.moveToNext()) {{
            metin.append("Tutar: ")
                .append(c.getString(0))
                .append("\\nTarih: ")
                .append(c.getString(1))
                .append("\\n")
                .append(c.getString(2))
                .append("\\n\\n");
        }}
        c.close();

        if (metin.length() == 0) {{
            metin.append("Bu üyeye ait ödeme kaydı yok.");
        }}

        new AlertDialog.Builder(this)
            .setTitle("Ödeme Geçmişi")
            .setMessage(metin.toString())
            .setPositiveButton("Kapat", null)
            .show();
    }}

    private class Veritabani extends SQLiteOpenHelper {{
        Veritabani() {{
            super(MainActivity.this, "uye_takip.db", null, 2);
        }}

        @Override
        public void onCreate(SQLiteDatabase sql) {{
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
        }}

        @Override
        public void onUpgrade(
            SQLiteDatabase sql,
            int oldVersion,
            int newVersion
        ) {{
            if (oldVersion < 2) {{
                sql.execSQL(
                    "ALTER TABLE odemeler ADD COLUMN ay_sayisi INTEGER DEFAULT 1"
                );
            }}
        }}
    }}
}}
"""


if __name__ == "__main__":
    print("EagleAndroidUygulamaUretici hazır.")
