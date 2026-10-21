package org.blender.blender;

import android.content.Context;

/**
 * DRNAS Android overlay language, separate from upstream Blender's own
 * language setting (Edit > Preferences > Interface > Translation).
 */
public final class DrnasLanguage {
  private static final String PREFS = "drnas_native_controls_v1";
  private DrnasLanguage() {}

  public static String current(Context context) {
    return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
        .getString("drnas_language", "en");
  }

  public static boolean croatian(Context context) {
    return "hr".equals(current(context));
  }

  public static String text(Context context, String english, String croatian) {
    return croatian(context) ? croatian : english;
  }
}
