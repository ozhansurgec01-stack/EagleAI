package com.eagleai.borclar;

import android.os.Bundle;
import android.service.voice.VoiceInteractionService;

public class EagleAssistantService extends VoiceInteractionService {

    @Override
    public void onReady() {
        super.onReady();
        android.util.Log.d(
                "EAGLE_ASSIST",
                "EagleAssistantService hazır"
        );
    }

    @Override
    public void onPrepareToShowSession(
            Bundle args,
            int showFlags
    ) {
        android.util.Log.d(
                "EAGLE_ASSIST",
                "EagleAI oturumu hazırlanıyor. showFlags=" + showFlags
        );

        super.onPrepareToShowSession(args, showFlags);
    }

    @Override
    public void onShutdown() {
        android.util.Log.d(
                "EAGLE_ASSIST",
                "EagleAssistantService kapandı"
        );
        super.onShutdown();
    }
}
