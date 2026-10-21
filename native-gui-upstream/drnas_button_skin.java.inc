  private android.graphics.drawable.GradientDrawable drnasKeySurface(boolean active, boolean mouse) {
    android.graphics.drawable.GradientDrawable shape = new android.graphics.drawable.GradientDrawable(
        android.graphics.drawable.GradientDrawable.Orientation.TOP_BOTTOM,
        active ? new int[] {Color.rgb(45, 125, 149), Color.rgb(25, 78, 109)}
               : new int[] {Color.argb(240, 48, 72, 92), Color.argb(240, 23, 39, 56)});
    shape.setCornerRadius(dpDrnas(mouse ? 16 : 13));
    shape.setStroke(dpDrnas(1), active ? Color.argb(235, 151, 236, 241)
                                              : Color.argb(130, 111, 164, 188));
    return shape;
  }
  private void drnasStyleKey(TextView button, boolean mouse) {
    android.graphics.drawable.StateListDrawable states = new android.graphics.drawable.StateListDrawable();
    states.addState(new int[] {android.R.attr.state_pressed}, drnasKeySurface(true, mouse));
    states.addState(new int[] {android.R.attr.state_activated}, drnasKeySurface(true, mouse));
    states.addState(new int[] {}, drnasKeySurface(false, mouse));
    button.setBackground(new android.graphics.drawable.RippleDrawable(
        android.content.res.ColorStateList.valueOf(Color.argb(55, 143, 233, 242)), states, null));
    button.setTextColor(Color.rgb(238, 248, 255));
    button.setTypeface(android.graphics.Typeface.create("sans-serif-medium", android.graphics.Typeface.NORMAL));
    button.setTextSize(mouse ? 14 : 13);
    button.setAllCaps(false);
    button.setSingleLine(true);
    button.setIncludeFontPadding(false);
    button.setLetterSpacing(0.015f);
    button.setGravity(Gravity.CENTER);
    button.setPadding(dpDrnas(7), 0, dpDrnas(7), 0);
    button.setElevation(dpDrnas(2));
  }
