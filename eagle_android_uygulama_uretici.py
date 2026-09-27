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
            ),
            "app/src/main/java/"
            + paket.replace(".", "/")
            + "/MainActivity.java": (
                self._haber_main_activity(
                    paket,
                    plan.get("konu", "Haberler"),
                )
                if haber_uygulamasi
                else self._main_activity(
                    paket,
                    plan.get("konu", "Uygulama"),
                    varliklar,
                    alanlar,
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
        metin = str(konu or "genel uygulama").lower()
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
    def _manifest(paket, internet=False):
        izin = (
            '    <uses-permission android:name="android.permission.INTERNET" />\\n'
            if internet else ""
        )
        bildirim_izin = (
            '    <uses-permission android:name="android.permission.POST_NOTIFICATIONS" />\\n'
            if internet else ""
        )
        return f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android">
{izin}{bildirim_izin}
    <application
        android:theme="@android:style/Theme.Material.Light.NoActionBar"
        android:label="Generated App"
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
        baslik.setText("{str(konu).replace('"', '\\"')}");
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


if __name__ == "__main__":
    print("EagleAndroidUygulamaUretici hazır.")
