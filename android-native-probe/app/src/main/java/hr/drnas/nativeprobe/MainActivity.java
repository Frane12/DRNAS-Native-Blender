package hr.drnas.nativeprobe;

import android.app.Activity;
import android.os.Build;
import android.os.Bundle;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.graphics.Typeface;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.concurrent.TimeUnit;

public final class MainActivity extends Activity {
    private TextView logView;
    private Button runButton;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int p = (int) (16 * getResources().getDisplayMetrics().density);
        root.setPadding(p, p, p, p);

        TextView title = new TextView(this);
        title.setText("DRNAS Native ARM64 • LAB");
        title.setTextSize(22);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        root.addView(title);

        TextView sub = new TextView(this);
        sub.setText("Testiranje stvarnog Android ARM64 izvršavanja. Ovo nije grafički Blender.");
        sub.setTextSize(14);
        root.addView(sub);

        runButton = new Button(this);
        runButton.setText("POKRENI NATIVNI TEST");
        runButton.setOnClickListener(v -> startProbe());
        root.addView(runButton);

        Button copy = new Button(this);
        copy.setText("KOPIRAJ LOG");
        copy.setOnClickListener(v -> {
            ClipboardManager cb = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
            cb.setPrimaryClip(ClipData.newPlainText("DRNAS Native LAB", logView.getText()));
            Toast.makeText(this, "Log kopiran", Toast.LENGTH_SHORT).show();
        });
        root.addView(copy);

        ScrollView scroll = new ScrollView(this);
        logView = new TextView(this);
        logView.setTextSize(13);
        logView.setTypeface(Typeface.MONOSPACE);
        logView.setTextIsSelectable(true);
        logView.setText("Spremno za test.\n");
        scroll.addView(logView);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
    }

    private void startProbe() {
        runButton.setEnabled(false);
        logView.setText("Pokretanje testa…\n");
        new Thread(() -> {
            StringBuilder out = new StringBuilder();
            try {
                String nativeDir = getApplicationInfo().nativeLibraryDir;
                out.append("SDK: ").append(Build.VERSION.SDK_INT).append("\n");
                out.append("ABI: ").append(Arrays.toString(Build.SUPPORTED_ABIS)).append("\n");
                out.append("Native libs: ").append(nativeDir).append("\n\n");

                if (!Arrays.asList(Build.SUPPORTED_ABIS).contains("arm64-v8a")) {
                    out.append("GREŠKA: Uređaj ne podržava ARM64-v8a.\n");
                } else {
                    testExecutable(out, new File(nativeDir, "libdrnas_smoke.so"), "DRNAS ARM64 izvršni test");
                    testExecutable(out, new File(nativeDir, "libblender.so"), "Blender --version");
                }
            } catch (Exception e) {
                out.append("GREŠKA: ").append(e).append("\n");
            }
            String result = out.toString();
            runOnUiThread(() -> {
                logView.setText(result);
                runButton.setEnabled(true);
            });
        }, "DRNAS-native-probe").start();
    }

    private void testExecutable(StringBuilder log, File file, String name) {
        log.append("=== ").append(name).append(" ===\n");
        if (!file.isFile()) {
            if (file.getName().equals("libblender.so")) {
                log.append("Blender ELF nije uključen u ovaj APK. Treba uspješan ARM64 build.\n\n");
            } else {
                log.append("GREŠKA: Nema izvršnog modula: ").append(file).append("\n\n");
            }
            return;
        }
        Process process = null;
        try {
            ProcessBuilder pb = new ProcessBuilder(file.getAbsolutePath(), "--version");
            pb.redirectErrorStream(true);
            pb.directory(getFilesDir());
            pb.environment().put("TMPDIR", getCacheDir().getAbsolutePath());
            process = pb.start();
            if (!process.waitFor(20, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                log.append("TIMEOUT nakon 20 sekundi\n\n");
                return;
            }
            log.append("Exit code: ").append(process.exitValue()).append("\n");
            ByteArrayOutputStream buf = new ByteArrayOutputStream();
            InputStream in = process.getInputStream();
            byte[] block = new byte[1024];
            int n;
            while (buf.size() < 16384 && (n = in.read(block)) != -1) {
                buf.write(block, 0, n);
            }
            log.append(new String(buf.toByteArray(), StandardCharsets.UTF_8)).append("\n\n");
        } catch (Exception e) {
            log.append("GREŠKA izvršavanja: ").append(e).append("\n\n");
        } finally {
            if (process != null) process.destroy();
        }
    }
}
