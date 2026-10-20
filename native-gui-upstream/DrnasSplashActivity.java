/* Experimental DRNAS loading screen. Blender brand image belongs to upstream Blender.
 * Shows the real bundled-runtime extraction off the UI thread while animated
 * Windows-inspired dots move horizontally between the logo and status line.
 */
package org.blender.blender;

import android.animation.ValueAnimator;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;

public final class DrnasSplashActivity extends Activity {
    private static final String VERSION = "5.3";
    private static final int BACKGROUND = Color.rgb(32, 31, 35);
    private final Handler handler = new Handler(Looper.getMainLooper());
    private ValueAnimator dotsAnimator;
    private long shownAtMs;
    private TextView status;

    private int dp(float value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                             WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().getDecorView().setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION |
            View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        shownAtMs = android.os.SystemClock.uptimeMillis();

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(BACKGROUND);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setGravity(Gravity.CENTER_HORIZONTAL);

        ImageView logo = new ImageView(this);
        int iconId = getResources().getIdentifier("ic_splash_logo", "drawable", getPackageName());
        if (iconId != 0) {
            logo.setImageResource(iconId);
        }
        logo.setScaleType(ImageView.ScaleType.FIT_CENTER);
        column.addView(logo, new LinearLayout.LayoutParams(dp(185), dp(138)));

        final View dots = new View(this) {
            final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
            @Override protected void onDraw(Canvas canvas) {
                super.onDraw(canvas);
                float phase = getTag() instanceof Float ? (Float)getTag() : 0f;
                float span = Math.min(getWidth() - dp(12), dp(164));
                float left = (getWidth() - span) / 2f;
                for (int i = 0; i < 6; ++i) {
                    float p = (phase - i * 0.115f + 6f) % 1f;
                    /* Acceleration along horizontal path, easing out at the edge. */
                    float t = p * p * (3f - 2f * p);
                    float x = left + span * t;
                    float fade = (float)Math.sin(Math.PI * p);
                    paint.setColor(Color.rgb(211, 219, 231));
                    paint.setAlpha(Math.max(0, Math.min(255, Math.round(fade * 245))));
                    canvas.drawCircle(x, getHeight() * .5f, dp(3.0f), paint);
                }
            }
        };
        column.addView(dots, new LinearLayout.LayoutParams(dp(195), dp(38)));

        status = new TextView(this);
        status.setText("Setting up Blender for the first time...");
        status.setTextColor(Color.rgb(181, 181, 184));
        status.setTextSize(15f);
        status.setGravity(Gravity.CENTER);
        status.setPadding(dp(6), dp(14), dp(6), 0);
        column.addView(status, new LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT, dp(65)));

        FrameLayout.LayoutParams centered = new FrameLayout.LayoutParams(
            FrameLayout.LayoutParams.WRAP_CONTENT, FrameLayout.LayoutParams.WRAP_CONTENT,
            Gravity.CENTER);
        root.addView(column, centered);
        setContentView(root);

        dotsAnimator = ValueAnimator.ofFloat(0f, 1f);
        dotsAnimator.setDuration(1350);
        dotsAnimator.setRepeatCount(ValueAnimator.INFINITE);
        dotsAnimator.setInterpolator(new android.view.animation.LinearInterpolator());
        dotsAnimator.addUpdateListener(a -> {
            dots.setTag((Float)a.getAnimatedValue());
            dots.invalidate();
        });
        dotsAnimator.start();

        new Thread(() -> {
            try {
                ensureRuntime();
                handler.post(() -> {
                    if (isFinishing() || isDestroyed()) return;
                    status.setText("Starting Blender...");
                    long elapsed = android.os.SystemClock.uptimeMillis() - shownAtMs;
                    handler.postDelayed(this::startBlender, Math.max(0, 500 - elapsed));
                });
            } catch (Exception error) {
                android.util.Log.e("DRNAS-Splash", "Unable to unpack Blender runtime", error);
                handler.post(() -> {
                    status.setText("Blender setup failed. Tap to retry.");
                    root.setOnClickListener(v -> recreate());
                });
            }
        }, "DRNAS-setup-worker").start();
    }

    private void startBlender() {
        if (isFinishing() || isDestroyed()) return;
        startActivity(new Intent(this, BlenderActivity.class));
        finish();
    }

    private void ensureRuntime() throws Exception {
        File root = new File(getFilesDir(), "blender/" + VERSION);
        File marker = new File(root, ".installed-" + VERSION);
        long stamp = getPackageManager().getPackageInfo(getPackageName(), 0).lastUpdateTime;
        String wanted = Long.toString(stamp);
        if (marker.isFile() &&
            wanted.equals(new String(Files.readAllBytes(marker.toPath()), StandardCharsets.UTF_8)))
            return;

        File stage = new File(root.getParentFile(), VERSION + "-drnas-stage");
        deleteTree(stage);
        if (!stage.mkdirs()) throw new IllegalStateException("Cannot create runtime stage");
        String safeRoot = stage.getCanonicalPath() + File.separator;
        byte[] buf = new byte[65536];
        try (InputStream input = getAssets().open("blender_runtime.zip");
             ZipInputStream zip = new ZipInputStream(input)) {
            ZipEntry entry;
            while ((entry = zip.getNextEntry()) != null) {
                File out = new File(stage, entry.getName());
                if (!out.getCanonicalPath().startsWith(safeRoot))
                    throw new IllegalArgumentException("Invalid path in Blender runtime zip");
                if (entry.isDirectory()) {
                    if (!out.isDirectory() && !out.mkdirs())
                        throw new IllegalStateException("Cannot create directory");
                    continue;
                }
                File parent = out.getParentFile();
                if (parent != null && !parent.exists() && !parent.mkdirs())
                    throw new IllegalStateException("Cannot create parent directory");
                try (FileOutputStream dest = new FileOutputStream(out)) {
                    int count;
                    while ((count = zip.read(buf)) > 0) dest.write(buf, 0, count);
                }
            }
        }
        Files.write(new File(stage, ".installed-" + VERSION).toPath(),
                    wanted.getBytes(StandardCharsets.UTF_8));
        deleteTree(root);
        if (!stage.renameTo(root))
            throw new IllegalStateException("Cannot activate verified Blender runtime");
    }

    private static void deleteTree(File path) throws Exception {
        if (!path.exists()) return;
        if (path.isDirectory()) {
            File[] children = path.listFiles();
            if (children != null) for (File child : children) deleteTree(child);
        }
        if (!path.delete()) throw new IllegalStateException("Cannot remove " + path);
    }

    @Override protected void onDestroy() {
        if (dotsAnimator != null) dotsAnimator.cancel();
        handler.removeCallbacksAndMessages(null);
        super.onDestroy();
    }
}
