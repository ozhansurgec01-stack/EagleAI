package com.eagleai.borclar;

import android.content.Intent;
import android.speech.RecognitionService;
import android.speech.RecognizerIntent;

public class EagleAssistantRecognitionService extends RecognitionService {

    @Override
    protected void onStartListening(
            Intent intent,
            Callback callback
    ) {
        android.util.Log.d(
                "EAGLE_ASSIST",
                "RecognitionService dinlemeye başladı"
        );

        try {
            callback.readyForSpeech(null);
        } catch (android.os.RemoteException e) {
            android.util.Log.e("EAGLE_ASSIST", "readyForSpeech hatası", e);
        }
    }

    @Override
    protected void onStopListening(Callback callback) {
        android.util.Log.d(
                "EAGLE_ASSIST",
                "RecognitionService dinlemeyi durdurdu"
        );

        try {
            callback.endOfSpeech();
        } catch (android.os.RemoteException e) {
            android.util.Log.e("EAGLE_ASSIST", "endOfSpeech hatası", e);
        }
    }

    @Override
    protected void onCancel(Callback callback) {
        android.util.Log.d(
                "EAGLE_ASSIST",
                "RecognitionService iptal edildi"
        );
    }
}
