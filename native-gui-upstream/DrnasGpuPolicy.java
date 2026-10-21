package org.blender.blender;
import java.util.regex.*;
/** GPU eligibility and aspect fit, independent of Android UI. */
public final class DrnasGpuPolicy {
  public static boolean supports(String target, String renderer) {
    String gpu = renderer == null ? "" : renderer;
    Matcher adreno = Pattern.compile("(?i)adreno\\s*(?:\\(tm\\))?[^0-9]{0,12}(\\d{3})(?![0-9])").matcher(gpu);
    if (adreno.find()) {
      String chip = adreno.group(1);
      if (target.equals("A6XX_A7XX")) return chip.matches("610|612|615|616|618|619|620|630|640|642|643|644|650|660|662|663|680|690|702|710|720|722|725|730|732|735|740|750");
      return target.equals("A"+chip);
    }
    Matcher mali = Pattern.compile("(?i)mali\\s*[- ]?g(52|72|76)(?![0-9])").matcher(gpu);
    return mali.find() && (target.equals("MALI_G52_G72_G76") || target.equals("MALI_G52") && mali.group(1).equals("52"));
  }
  public static int[] fit(int w, int h, int capW, int capH) {
    if (w <= 0 || h <= 0) return new int[]{0,0};
    if (capW <= 0 || capH <= 0) return new int[]{w,h};
    if (w < h) { int swap=capW; capW=capH; capH=swap; }
    double f=Math.min(1d,Math.min((double)capW/w,(double)capH/h));
    if (f >= 1d) return new int[]{w,h};
    return new int[]{Math.max(2,((int)(w*f)/2)*2),Math.max(2,((int)(h*f)/2)*2)};
  }
}
