package com.eagleai.borclar;

import android.content.Intent;
import android.os.Bundle;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import java.util.Locale;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;
import android.service.voice.VoiceInteractionSession;

public class EagleAssistantSession extends VoiceInteractionSession {

    private SpeechRecognizer speechRecognizer;
    private TextToSpeech konusmaMotoru;

    public EagleAssistantSession(android.content.Context context) {
        super(context);
    }

    @Override
    public void onCreate() {
        super.onCreate();

        konusmaMotoru = new TextToSpeech(
                getContext(),
                status -> {
                    if (status == TextToSpeech.SUCCESS) {
                        konusmaMotoru.setLanguage(new Locale("tr", "TR"));
                        konusmaMotoru.setPitch(1.05f);
                        konusmaMotoru.setSpeechRate(1.0f);

                        android.util.Log.d(
                                "EAGLE_ASSIST",
                                "EagleAI TTS hazır"
                        );
                    }
                }
        );

        android.util.Log.d(
                "EAGLE_ASSIST",
                "EagleAssistantSession oluşturuldu"
        );
    }

    @Override
    public void onShow(android.os.Bundle args, int showFlags) {
        baslatSesTanima();
        super.onShow(args, showFlags);
        android.util.Log.d(
                "EAGLE_ASSIST",
                "EagleAssistantSession GÖSTERİLDİ. showFlags=" + showFlags
        );
    }

    private void baslatSesTanima() {
        if (!SpeechRecognizer.isRecognitionAvailable(getContext())) {
            android.util.Log.e(
                    "EAGLE_ASSIST",
                    "Bu cihazda ses tanıma kullanılamıyor"
            );
            return;
        }

        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(getContext());

        speechRecognizer.setRecognitionListener(
                new RecognitionListener() {

                    @Override
                    public void onResults(Bundle results) {
                        java.util.ArrayList<String> sonuclar =
                                results.getStringArrayList(
                                        SpeechRecognizer.RESULTS_RECOGNITION
                                );

                        if (sonuclar != null && !sonuclar.isEmpty()) {
                            String metin = sonuclar.get(0);

                            android.util.Log.d(
                                    "EAGLE_ASSIST",
                                    "Asistan sesi algıladı: " + metin
                            );

                            eagleApiIstek(metin);
                        }
                    }

                    @Override public void onReadyForSpeech(Bundle params) {}
                    @Override public void onBeginningOfSpeech() {}
                    @Override public void onRmsChanged(float rmsdB) {}
                    @Override public void onBufferReceived(byte[] buffer) {}
                    @Override public void onEndOfSpeech() {}
                    @Override public void onError(int error) {
                        android.util.Log.e(
                                "EAGLE_ASSIST",
                                "Ses tanıma hatası: " + error
                        );
                    }

                    @Override public void onPartialResults(Bundle partialResults) {}
                    @Override public void onEvent(int eventType, Bundle params) {}
                }
        );

        Intent intent = new Intent(
                RecognizerIntent.ACTION_RECOGNIZE_SPEECH
        );

        intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
        );

        intent.putExtra(
                RecognizerIntent.EXTRA_LANGUAGE,
                "tr-TR"
        );

        speechRecognizer.startListening(intent);
    }

    private void eagleApiIstek(String mesaj) {
        new Thread(() -> {
            HttpURLConnection baglanti = null;

            try {
                URL url = new URL(
                        "https://eagleai-8p9b4.faable.link/api/sohbet"
                );

                baglanti = (HttpURLConnection) url.openConnection();
                baglanti.setRequestMethod("POST");
                baglanti.setConnectTimeout(10000);
                baglanti.setReadTimeout(60000);
                baglanti.setDoOutput(true);
                baglanti.setRequestProperty(
                        "Content-Type",
                        "application/json; charset=UTF-8"
                );

                JSONObject body = new JSONObject();
                body.put("message", mesaj);

                OutputStream cikti = baglanti.getOutputStream();
                cikti.write(
                        body.toString().getBytes("UTF-8")
                );
                cikti.flush();
                cikti.close();

                int kod = baglanti.getResponseCode();

                BufferedReader okuyucu;

                if (kod >= 200 && kod < 300) {
                    okuyucu = new BufferedReader(
                            new InputStreamReader(
                                    baglanti.getInputStream(),
                                    "UTF-8"
                            )
                    );
                } else {
                    okuyucu = new BufferedReader(
                            new InputStreamReader(
                                    baglanti.getErrorStream(),
                                    "UTF-8"
                            )
                    );
                }

                StringBuilder cevapMetni = new StringBuilder();
                String satir;

                while ((satir = okuyucu.readLine()) != null) {
                    cevapMetni.append(satir);
                }

                okuyucu.close();

                JSONObject cevapJson =
                        new JSONObject(cevapMetni.toString());

                String cevap =
                        cevapJson.optString(
                                "answer",
                                "EagleAI cevap vermedi."
                        );

                android.util.Log.d(
                        "EAGLE_ASSIST",
                        "API cevabı: " + cevap
                );

                new android.os.Handler(
                        android.os.Looper.getMainLooper()
                ).post(() -> {
                    if (konusmaMotoru != null) {
                        konusmaMotoru.speak(
                                cevap,
                                TextToSpeech.QUEUE_FLUSH,
                                null,
                                "eagle_api_cevap"
                        );
                    }
                });

            } catch (Exception e) {
                android.util.Log.e(
                        "EAGLE_ASSIST",
                        "EagleAI API hatası",
                        e
                );
            } finally {
                if (baglanti != null) {
                    baglanti.disconnect();
                }
            }
        }).start();
    }

    @Override
    public void onDestroy() {
        if (speechRecognizer != null) {
            speechRecognizer.destroy();
            speechRecognizer = null;
        }

        if (konusmaMotoru != null) {
            konusmaMotoru.stop();
            konusmaMotoru.shutdown();
            konusmaMotoru = null;
        }
        android.util.Log.d("EAGLE_ASSIST", "EagleAssistantSession kapandı");
        super.onDestroy();
    }
}
