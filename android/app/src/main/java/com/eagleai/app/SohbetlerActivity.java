package com.eagleai.app;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.TextView;

public class SohbetlerActivity extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        LinearLayout ana = new LinearLayout(this);
        ana.setOrientation(LinearLayout.VERTICAL);
        ana.setBackgroundColor(Color.rgb(245, 245, 245));

        TextView baslik = new TextView(this);
        baslik.setText("‹  Son Sohbetler");
        baslik.setTextSize(21);
        baslik.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));
        baslik.setTextColor(Color.rgb(30, 30, 30));
        baslik.setGravity(Gravity.CENTER_VERTICAL);
        baslik.setPadding(20, 16, 20, 16);

        baslik.setOnClickListener(v -> finish());

        ana.addView(
                baslik,
                new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        64
                )
        );

        View ayirici = new View(this);
        ayirici.setBackgroundColor(Color.rgb(220, 220, 220));

        ana.addView(
                ayirici,
                new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        1
                )
        );

        TextView bilgi = new TextView(this);
        bilgi.setText("Sohbetler burada görünecek.");
        bilgi.setTextSize(16);
        bilgi.setTypeface(Typeface.create("sans-serif", Typeface.NORMAL));
        bilgi.setTextColor(Color.rgb(100, 100, 100));
        bilgi.setPadding(24, 28, 24, 28);

        ana.addView(bilgi);

        setContentView(ana);
    }
}
