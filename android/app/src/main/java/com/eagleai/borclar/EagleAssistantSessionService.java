package com.eagleai.borclar;

import android.os.Bundle;
import android.service.voice.VoiceInteractionSession;
import android.service.voice.VoiceInteractionSessionService;

public class EagleAssistantSessionService extends VoiceInteractionSessionService {

    @Override
    public VoiceInteractionSession onNewSession(Bundle args) {
        android.util.Log.d(
                "EAGLE_ASSIST",
                "Yeni EagleAI ses oturumu oluşturuluyor"
        );

        return new EagleAssistantSession(this);
    }
}
