package com.eagleai.borclar;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;

public class EagleVoiceService extends Service {

    private static final String KANAL_ID = "eagle_voice_channel";

    @Override
    public void onCreate() {
        super.onCreate();

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel kanal = new NotificationChannel(
                    KANAL_ID,
                    "EagleAI Sesli Asistan",
                    NotificationManager.IMPORTANCE_LOW
            );

            NotificationManager yonetici =
                    getSystemService(NotificationManager.class);

            if (yonetici != null) {
                yonetici.createNotificationChannel(kanal);
            }
        }
    }

    @Override
    public int onStartCommand(
            Intent intent,
            int flags,
            int startId
    ) {
        Notification bildirim;

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            bildirim = new Notification.Builder(this, KANAL_ID)
                    .setContentTitle("EagleAI")
                    .setContentText("Sesli asistan aktif")
                    .setSmallIcon(android.R.drawable.ic_btn_speak_now)
                    .setOngoing(true)
                    .build();
        } else {
            bildirim = new Notification.Builder(this)
                    .setContentTitle("EagleAI")
                    .setContentText("Sesli asistan aktif")
                    .setSmallIcon(android.R.drawable.ic_btn_speak_now)
                    .setOngoing(true)
                    .build();
        }

        startForeground(1001, bildirim);

        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
