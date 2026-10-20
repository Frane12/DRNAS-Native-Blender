package hr.drnas.nativeprobe;

import android.app.Activity;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.pm.ActivityInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.MotionEvent;
import android.view.Surface;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.SeekBar;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Locale;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;

public final class MainActivity extends Activity implements SurfaceHolder.Callback {
    static { System.loadLibrary("drnas_vulkan"); }

    private native String nativeVulkanDraw(Surface surface);
    private native void nativeInput(int action, float x, float y, float value);
    // action: 1=move, 2=LMB down, 3=LMB up, 4=RMB down,
    // 5=RMB up, 6=zoom delta. Native FIFO feeds the future Android GHOST backend.

    private FrameLayout root;
    private SurfaceView canvas;
    private TextView status;
    private boolean editMode = false;
    private boolean surfaceReady = false;
    private int session = 0;
    private boolean fullscreen = true;
    private final AtomicBoolean rendering = new AtomicBoolean(false);
    private int zoomPrevious = 50;
    private StringBuilder diagnostics = new StringBuilder();
    private final int white = Color.rgb(231, 239, 249);
    private final int panel = Color.argb(215, 20, 30, 45);

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + .5f);
    }
    private GradientDrawable bubble(int background, int radius) {
        GradientDrawable shape = new GradientDrawable();
        shape.setColor(background);
        shape.setCornerRadius(dp(radius));
        shape.setStroke(dp(1), Color.argb(100, 105, 173, 215));
        return shape;
    }
    private TextView label(String text, int size) {
        TextView t = new TextView(this);
        t.setText(text);
        t.setTextColor(white);
        t.setTextSize(size);
        t.setGravity(Gravity.CENTER);
        return t;
    }
    private void log(String line) {
        diagnostics.append(line).append('\n');
        if (status != null) {
            final String tail = diagnostics.length() > 720
                ? diagnostics.substring(diagnostics.length() - 720) : diagnostics.toString();
            status.setText(tail);
        }
    }
    private void fullScreen(boolean enabled) {
        fullscreen = enabled;
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON,
                WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        if (enabled) {
            getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);
        } else {
            getWindow().getDecorView().setSystemUiVisibility(0);
        }
    }
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        setRequestedOrientation(ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE);
        fullScreen(true);
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(10, 16, 26));

        canvas = new SurfaceView(this);
        canvas.getHolder().addCallback(this);
        canvas.setOnTouchListener((v, e) -> {
            if (editMode) return true;
            int action = e.getActionMasked();
            if (action == MotionEvent.ACTION_DOWN || action == MotionEvent.ACTION_MOVE) {
                nativeInput(1, e.getX(), e.getY(), 0);
                return true;
            }
            return action == MotionEvent.ACTION_UP;
        });
        root.addView(canvas, new FrameLayout.LayoutParams(-1, -1));

        LinearLayout header = new LinearLayout(this);
        header.setOrientation(LinearLayout.HORIZONTAL);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(10), dp(4), dp(10), dp(4));
        header.setBackground(bubble(panel, 12));
        FrameLayout.LayoutParams hp = new FrameLayout.LayoutParams(-1, dp(48), Gravity.TOP);
        hp.setMargins(dp(8), dp(6), dp(8), 0);
        root.addView(header, hp);

        TextView title = label("DRNAS  •  NATIVE GUI BRIDGE LAB", 16);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        header.addView(title, new LinearLayout.LayoutParams(0, -1, 1));
        addHeaderButton(header, "VULKAN", () -> renderVulkan());
        addHeaderButton(header, "LTS", this::testBlenderVersion);
        addHeaderButton(header, "EDIT", () -> {
            editMode = !editMode;
            log(editMode ? "Kontrole: EDIT MODE (povuci LMB / RMB / ZOOM)" :
                    "Kontrole: RUN MODE");
        });
        addHeaderButton(header, "⛶", () -> fullScreen(!fullscreen));
        addHeaderButton(header, "COPY", this::copyLog);

        TextView legend = label(
            "Vulkan Surface • ARM64 • GHOST-ready input FIFO | Blender viewport: nije povezan", 12);
        legend.setBackground(bubble(Color.argb(200, 18, 27, 40), 9));
        FrameLayout.LayoutParams lp = new FrameLayout.LayoutParams(-2, dp(33), Gravity.TOP | Gravity.CENTER_HORIZONTAL);
        lp.topMargin = dp(62);
        root.addView(legend, lp);

        addFloatingButton("LMB", 14, 0, 2, 3);
        addFloatingButton("RMB", 14, 1, 4, 5);
        addZoomControl();

        status = label("DRNAS Native GUI • Vulkan initialization pending...", 12);
        status.setTypeface(Typeface.MONOSPACE);
        status.setGravity(Gravity.LEFT | Gravity.CENTER_VERTICAL);
        status.setPadding(dp(14), dp(4), dp(14), dp(4));
        status.setBackground(bubble(Color.argb(220, 9, 17, 29), 12));
        FrameLayout.LayoutParams sp = new FrameLayout.LayoutParams(-1, dp(84), Gravity.BOTTOM);
        sp.setMargins(dp(8), 0, dp(8), dp(6));
        root.addView(status, sp);
        setContentView(root);
        log("Android SDK " + Build.VERSION.SDK_INT + ", ABIs " + Arrays.toString(Build.SUPPORTED_ABIS));
        log("Native Vulkan površina + GHOST-ready input FIFO spremni za test.");
    }
    private void addHeaderButton(LinearLayout row, String text, Runnable run) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextSize(11);
        b.setAllCaps(false);
        b.setMinWidth(0);
        b.setMinimumWidth(0);
        b.setPadding(dp(2), 0, dp(2), 0);
        row.addView(b, new LinearLayout.LayoutParams(dp(text.length() > 4 ? 77 : 55), dp(42)));
        b.setOnClickListener(v -> run.run());
    }
    private void position(View v, int side, int dx, int dy, int width, int height) {
        FrameLayout.LayoutParams p = new FrameLayout.LayoutParams(dp(width), dp(height),
            Gravity.BOTTOM | (side == 0 ? Gravity.LEFT : Gravity.RIGHT));
        if (side == 0) p.leftMargin = dp(dx);
        else p.rightMargin = dp(dx);
        p.bottomMargin = dp(dy);
        root.addView(v, p);
    }
    private boolean moveControl(View v, MotionEvent event, float[] old) {
        if (!editMode) return false;
        if (event.getActionMasked() == MotionEvent.ACTION_DOWN) {
            old[0] = event.getRawX();
            old[1] = event.getRawY();
            return true;
        }
        if (event.getActionMasked() == MotionEvent.ACTION_MOVE) {
            float dx = event.getRawX() - old[0];
            float dy = event.getRawY() - old[1];
            v.setTranslationX(v.getTranslationX() + dx);
            v.setTranslationY(v.getTranslationY() + dy);
            old[0] = event.getRawX();
            old[1] = event.getRawY();
            return true;
        }
        return true;
    }
    private void addFloatingButton(String text, int inset, int side, int down, int up) {
        TextView b = label(text, 19);
        b.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        b.setBackground(bubble(Color.argb(230, 18, 47, 68), 19));
        position(b, side, inset, 107, 90, 65);
        float[] old = {0, 0};
        b.setOnTouchListener((v, event) -> {
            if (moveControl(v, event, old)) return true;
            int action = event.getActionMasked();
            if (action == MotionEvent.ACTION_DOWN) {
                nativeInput(down, 0, 0, 1);
                b.setAlpha(.58f);
                return true;
            }
            if (action == MotionEvent.ACTION_UP || action == MotionEvent.ACTION_CANCEL) {
                nativeInput(up, 0, 0, 0);
                b.setAlpha(1f);
                return true;
            }
            return true;
        });
    }
    private void addZoomControl() {
        LinearLayout group = new LinearLayout(this);
        group.setOrientation(LinearLayout.VERTICAL);
        group.setGravity(Gravity.CENTER);
        group.setPadding(dp(6), dp(2), dp(6), dp(3));
        group.setBackground(bubble(Color.argb(230, 18, 47, 68), 14));
        group.addView(label("ZOOM", 13), new LinearLayout.LayoutParams(-1, dp(26)));
        SeekBar zoom = new SeekBar(this);
        zoom.setMax(100);
        zoom.setProgress(50);
        group.addView(zoom, new LinearLayout.LayoutParams(dp(165), dp(43)));
        position(group, 0, 112, 107, 182, 77);
        float[] previous = {0, 0};
        group.setOnTouchListener((v, e) -> moveControl(v, e, previous));
        zoom.setOnTouchListener((v, e) -> editMode && moveControl(group, e, previous));
        zoom.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar b, int progress, boolean user) {
                if (!user || editMode) return;
                float delta = (progress - zoomPrevious) / 10f;
                zoomPrevious = progress;
                nativeInput(6, 0, 0, delta);
            }
            @Override public void onStartTrackingTouch(SeekBar b) {}
            @Override public void onStopTrackingTouch(SeekBar b) {
                b.setProgress(50);
                zoomPrevious = 50;
            }
        });
    }
    @Override public void surfaceCreated(SurfaceHolder h) {
        surfaceReady = true;
        renderVulkan();
    }
    @Override public void surfaceChanged(SurfaceHolder h, int format, int width, int height) {
        surfaceReady = true;
    }
    @Override public void surfaceDestroyed(SurfaceHolder h) {
        surfaceReady = false;
        session++;
    }
    private void renderVulkan() {
        if (!surfaceReady || !canvas.getHolder().getSurface().isValid()) {
            log("Vulkan: površina nije spremna");
            return;
        }
        if (!rendering.compareAndSet(false, true)) {
            log("Vulkan: render je već aktivan, preskačem dvostruki zahtjev.");
            return;
        }
        final int attempt = ++session;
        Surface surface = canvas.getHolder().getSurface();
        log("Vulkan: stvaranje Android surface / swapchain...");
        new Thread(() -> {
            String result;
            try { result = nativeVulkanDraw(surface); }
            catch (Throwable e) { result = "JNI Vulkan error: " + e; }
            finally { rendering.set(false); }
            final String finalResult = result;
            runOnUiThread(() -> { if (attempt == session) log(finalResult); });
        }, "DRNAS-Vulkan").start();
    }
    @Override protected void onPause() {
        // Avoid sticky mouse-down when Android backgrounds the Activity.
        nativeInput(3, 0, 0, 0);
        nativeInput(5, 0, 0, 0);
        super.onPause();
    }
    @Override protected void onDestroy() {
        session++; // invalidate queued log callbacks after teardown
        super.onDestroy();
    }
    private void copyLog() {
        ((ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE))
            .setPrimaryClip(ClipData.newPlainText("DRNAS Vulkan LAB", diagnostics.toString()));
        log("Log kopiran.");
    }
    private void testBlenderVersion() {
        log("Pokrećem Blender --version, bez grafičkog GHOST backenda...");
        new Thread(() -> {
            String message;
            File elf = new File(getApplicationInfo().nativeLibraryDir, "libblender.so");
            if (!elf.isFile()) message = "Blender ELF nije ubačen u ovu GUI testnu verziju.";
            else {
                Process process = null;
                try {
                    ProcessBuilder pb = new ProcessBuilder(elf.getAbsolutePath(), "--version");
                    pb.directory(getFilesDir());
                    pb.redirectErrorStream(true);
                    pb.environment().put("TMPDIR", getCacheDir().getAbsolutePath());
                    process = pb.start();
                    if (!process.waitFor(20, TimeUnit.SECONDS)) {
                        process.destroyForcibly();
                        message = "Blender --version: timeout";
                    } else {
                        ByteArrayOutputStream out = new ByteArrayOutputStream();
                        byte[] buf = new byte[1024];
                        InputStream stream = process.getInputStream();
                        int count;
                        while (out.size() < 8192 && (count = stream.read(buf)) != -1) {
                            out.write(buf, 0, count);
                        }
                        message = "Blender exit=" + process.exitValue() + "  " +
                                  new String(out.toByteArray(), StandardCharsets.UTF_8).trim();
                    }
                } catch (Exception e) { message = "Blender ELF: " + e; }
                finally { if (process != null) process.destroy(); }
            }
            String result = message;
            runOnUiThread(() -> log(result));
        }, "DRNAS-Blender-LTS").start();
    }
}
