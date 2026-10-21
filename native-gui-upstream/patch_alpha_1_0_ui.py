#!/usr/bin/env python3
"""Release Alpha 1.0: English by default; optional Croatian DRNAS overlay menu;
Stretch enabled on a fresh installation, respecting subsequent user overrides.

Runs AFTER all v8, v9 and v10 scripts. Only replaces Java sources/manifest,
reusing the verified native ARM64 Vulkan Blender executable unchanged.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
src = root / "build_files/android/apk/app/src/main/java/org/blender/blender"
activity = src / "BlenderActivity.java"
gpu = src / "DrnasGpuOptions.java"
manifest = root / "build_files/android/apk/app/src/main/AndroidManifest.xml"


def replace_once(s, a, b):
    occurrences = s.count(a)
    if occurrences != 1:
        raise RuntimeError(f"Expected exactly one source anchor; got {occurrences}: {a[:120]!r}")
    return s.replace(a, b, 1)


def localized_literals(s, items, activity_context):
    """Translate only exact user-visible literals, not preference keys or code."""
    for croatian, english in items.items():
        old = '"' + croatian + '"'
        if old not in s:
            raise RuntimeError(f"Missing known existing DRNAS label: {croatian!r}")
        en = english.replace('\\', '\\\\').replace('"', '\\"')
        hr = croatian.replace('\\', '\\\\').replace('"', '\\"')
        s = s.replace(old, f'DrnasLanguage.text({activity_context}, "{en}", "{hr}")')
    return s


s = activity.read_text(encoding="utf-8")
# Switch in the real DRNAS settings menu. It affects the *overlay*; Blender's
# own interface translation is configured in Edit > Preferences > Interface.
# One-time Spinner setup does not rewrite existing language choice.
anchor = '    DrnasGpuOptions.install(this, optionRows);'
s = replace_once(s, anchor, '    drnasInstallLanguageMenu(optionRows);\n' + anchor)
s = replace_once(s, '  private void requestAllFilesAccess() {', '''
  private void drnasInstallLanguageMenu(LinearLayout rows) {
    rows.addView(drnasUiLabel(DrnasLanguage.text(this,
        "DRNAS LANGUAGE (restart to apply)",
        "JEZIK DRNAS KONTROLA (primjena nakon ponovnog pokretanja)")));
    final android.widget.Spinner language = new android.widget.Spinner(this);
    final String[] choices = {"English", "Hrvatski"};
    final android.widget.ArrayAdapter<String> adapter = new android.widget.ArrayAdapter<>(
        this, android.R.layout.simple_spinner_item, choices);
    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
    language.setAdapter(adapter);
    language.setSelection(DrnasLanguage.croatian(this) ? 1 : 0, false);
    rows.addView(language, new LinearLayout.LayoutParams(-1, dpDrnas(46)));
    final boolean[] ready = {false};
    language.post(() -> ready[0] = true);
    language.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
      @Override public void onNothingSelected(android.widget.AdapterView<?> parent) {}
      @Override public void onItemSelected(android.widget.AdapterView<?> parent,
                                            View v, int pos, long id) {
        if (v instanceof TextView) ((TextView)v).setTextColor(drnasTextWhite);
        if (!ready[0]) return;
        String selected = pos == 1 ? "hr" : "en";
        if (selected.equals(DrnasLanguage.current(BlenderActivity.this))) return;
        drnasPrefs.edit().putString("drnas_language", selected).apply();
        android.widget.Toast.makeText(BlenderActivity.this,
            pos == 1 ? "Jezik spremljen. Ponovno pokreni aplikaciju." :
                "Language saved. Restart Blender to apply.",
            android.widget.Toast.LENGTH_LONG).show();
      }
    });
  }

  private void requestAllFilesAccess() {''')

# Exact labels appearing in the finished generated v10 Activity (including
# editor windows and save/exit dialogs). English default; Croatian optional.
labels = {
    "Miš / touchpad (isključeno: direktni dodir)": "Relative mouse / touchpad (off: direct touch)",
    "Efekt pokazivača / krug klika (miš način)": "Pointer click indicator (mouse mode)",
    "Brzina miša: ": "Mouse speed: ",
    "Miš: tap = lijevi klik • 2 prsta = zoom / desni tap":
        "Mouse: tap = left click; two fingers = zoom / right tap",
    "Veličina kursora: ": "Cursor size: ",
    "Veličina kursora od 40 do 150 posto": "Cursor size from 40 to 150 percent",
    "Osjetljivost gesta": "Gesture sensitivity",
    "Prikaži ili sakrij zoom slider": "Show or hide zoom slider",
    "Prozirnost ": "Opacity ",
    "miša i zooma": "mouse and zoom",
    "tipkovnice": "keyboard",
    "Uredi miš i zoom": "Edit mouse and zoom",
    "Uredi veličinu i raspored tipkovnice": "Edit keyboard size and layout",
    "Miš i zoom": "Mouse and zoom",
    "Tipkovnica i raspored": "Keyboard and layout",
    "Širina grupe": "Group width",
    "Visina grupe": "Group height",
    "Odaberi tipku i pomakni je u rasporedu": "Select a key and change its position",
    "← Ranije": "← Earlier",
    "Kasnije →": "Later →",
    "Vrati izvorni raspored": "Restore original layout",
    "Smanji prozor miša": "Minimize mouse window",
    "Otvori plutajući prozor miša": "Restore floating mouse window",
    "Drži i pomakni prozor miša": "Hold and move mouse window",
    "Feder zoom: odmak od sredine određuje brzinu, otpusti za stop":
        "Spring zoom: drag from center to set speed; release to stop",
    "Zatvori postavke  ✕": "Close settings  ✕",
    "Zatvori postavke i vrati se Blenderu": "Close settings and return to Blender",
    "Ručkicom ⠿ pomakni kontrole; položaj se sprema automatski":
        "Drag controls using ⠿; position saves automatically",
    "VELIČINA MIŠA I ZOOMA": "MOUSE AND ZOOM SIZE",
    "% • LMB/RMB i zoom blok": "% • LMB/RMB and zoom",
    "Dvostruki dodir: zaključaj tipku • jedan dodir: otključaj":
        "Double-tap to lock; tap once to unlock",
    " — zaključano; dodirni za otključavanje": " — locked; tap to unlock",
    " — dvostruki dodir za zaključavanje": " — double-tap to lock",
    "Spremiti projekt prije izlaska?": "Save project before exit?",
    "Spremi i zatvori aplikaciju ili izađi bez spremanja promjena.":
        "Save your project and exit, or discard unsaved changes.",
    "Bez spremanja": "Exit without saving",
    "Spremi i izađi": "Save and Exit",
    "Spremanje otkazano. Aplikacija ostaje otvorena.":
        "Save cancelled. Blender remains open.",
    "Spremanje još nije spremno. Pokušaj ponovno.":
        "Save is not ready yet. Please try again.",
    "Spremanje projekta… Za novi projekt odaberi naziv i lokaciju u Blenderu.":
        "Saving project… For a new project choose a name and location in Blender.",
    "Spremanje nije pokrenuto. Aplikacija ostaje otvorena.":
        "Save could not start. Blender remains open.",
    "Spremanje nije dovršeno.": "Save was not completed.",
    " Aplikacija ostaje otvorena.": " Blender remains open.",
    "Broj redova": "Number of rows",
    "VELIČINA TIPKOVNICE I NAREDBI": "KEYBOARD AND COMMAND SIZE",
    "VELIČINA BLENDER GUI (UI SCALE)": "BLENDER UI SCALE",
    "Blender GUI veličina sprema se za iduće pokretanje.":
        "Blender UI scale saved. Restart to apply.",
    "Pomakni traku tipki": "Drag shortcut bar",
    "Smooth zoom (kao EmuDRNAS)": "Smooth zoom (EmuDRNAS style)",
    "% • tipkovnica i naredbe": "% • keyboard and commands",
    "100%  • promjena nakon ponovnog pokretanja": "100%  • applies after restart",
    "%  • primjena nakon restarta": "%  • applies after restart",
    "Stretch screen • popuni cijeli zaslon": "Stretch screen • fill available display",
    "Stretch spremljen. Manja rezolucija skalira se na cijeli prozor; omjer slike ostaje očuvan.":
        "Stretch saved. Lower render resolutions fill the window while preserving aspect ratio.",
}
# The Alpha pipeline uses the accepted v10 code, not the unrelated partial
# English test branch. Only actual literals in generated Java are translated.
# Some controls appear twice, which is expected and handled by replace all.
for hr, en in labels.items():
    old = '"' + hr + '"'
    if old not in s:
        # A few GPU-only labels are injected into a different class, while
        # other labels are dynamic substrings within an existing literal.
        # Report a missing Activity label only when it is clearly required.
        if hr not in ("Stretch screen • popuni cijeli zaslon",
                      "Stretch spremljen. Manja rezolucija skalira se na cijeli prozor; omjer slike ostaje očuvan."):
            raise RuntimeError(f"Expected generated Activity literal: {hr!r}")
        continue
    s = s.replace(old, f'DrnasLanguage.text(BlenderActivity.this, "{en}", "{hr}")')
# The mouse/zoom size footer and other labels may be string pieces inside
# concatenations. Translate the *complete* Java string literal there.
s = s.replace('"% • LMB/RMB i zoom blok"', 'DrnasLanguage.text(BlenderActivity.this, "% • LMB/RMB and zoom", "% • LMB/RMB i zoom blok")')
# v10 includes multiple status/control messages not meaningful to native Blender
# itself. These are Android-only.
activity.write_text(s, encoding="utf-8")

g = gpu.read_text(encoding="utf-8")
# Explicit migration-less new-install default; never overwrite an existing
# false value chosen by the user. NativeActivity applies this at startup.
g = replace_once(g,
    '    applyStretch(a);\n    renderer=DrnasGpuProfile.renderer;',
    '''    SharedPreferences stretchPrefs=prefs(a);
    if(!stretchPrefs.contains("stretch_screen"))
      stretchPrefs.edit().putBoolean("stretch_screen",true).commit();
    applyStretch(a);
    renderer=DrnasGpuProfile.renderer;''')
g = g.replace('getBoolean("stretch_screen",false)',
              'getBoolean("stretch_screen",true)')
gpu_labels = {
    "Prethodni GPU start nije uspio; vraćen sistemski driver.":
        "The previous GPU startup failed; using the system driver.",
    "GPU paket nije dostupan; koristi se sistemski driver.":
        "GPU package is unavailable; using the system driver.",
    "Sistemski Vulkan (zadano)": "System Vulkan (default)",
    "Zatraženo pri pokretanju: ": "Requested at startup: ",
    "Aktivno pri pokretanju: ": "Active at startup: ",
    "Driver spremljen. Spremi rad i ponovno pokreni aplikaciju za primjenu.":
        "Driver selected. Save your work and restart Blender to apply.",
    "REZOLUCIJA • očuvan omjer zaslona": "RESOLUTION • keep aspect ratio",
    "Automatski (GPU / memorija)": "Automatic (GPU / memory)",
    "Izvorna • ": "Native • ",
    "Rezolucija spremljena. Spremi rad i ponovno pokreni aplikaciju za primjenu.":
        "Resolution selected. Save your work and restart Blender to apply.",
    "Stretch screen • popuni cijeli zaslon": "Stretch screen • fill available display",
    "Stretch spremljen. Manja rezolucija skalira se na cijeli prozor; omjer slike ostaje očuvan.":
        "Stretch saved. Lower resolutions fill the window, preserving aspect ratio.",
}
for hr, en in gpu_labels.items():
    if '"' + hr + '"' in g:
        g = g.replace('"' + hr + '"', f'DrnasLanguage.text(a, "{en}", "{hr}")')
# Two-line Croatian GPU description is one combined Java string; ensure English
# rather than accidentally shipping an untranslated line at the top of settings.
g = g.replace(
    '"\\nPromjene se primjenjuju nakon spremanja rada i ponovnog pokretanja aplikacije."',
    'DrnasLanguage.text(a, "\\nChanges apply after saving and restarting Blender.", '
    '"\\nPromjene se primjenjuju nakon spremanja rada i ponovnog pokretanja aplikacije.")'
)
gpu.write_text(g, encoding="utf-8")

# Copy compile-time Java helper into the upstream app's source tree.
language = Path(__file__).with_name("DrnasLanguage.java").read_text(encoding="utf-8")
(src / "DrnasLanguage.java").write_text(language, encoding="utf-8")

m = manifest.read_text(encoding="utf-8")
for a,b in (
    ("hr.drnas.blendernativefloatingstretcht2026v10","hr.drnas.blendernativealpha10"),
    ("0.1.10-floating-stretch-test", "1.0-alpha"),
    ("Native Blender Floating Windows v10 TEST", "DRNAS Native Blender Alpha 1.0"),
    ('android:versionCode="11"', 'android:versionCode="100"'),
):
    if a not in m: raise RuntimeError(f"Missing v10 manifest identity {a!r}")
    m = m.replace(a,b)
manifest.write_text(m, encoding="utf-8")
assert 'putBoolean("stretch_screen",true).commit()' in g
assert 'getBoolean("stretch_screen",true)' in g
assert 'drnasInstallLanguageMenu(optionRows)' in s
assert 'DrnasLanguage.croatian(this)' in s
print("PASS: Alpha 1.0 identity, first-install stretch ON, language settings, English default + Croatian overlay strings")
