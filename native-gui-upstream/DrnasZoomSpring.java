package org.blender.blender;

/** Deflection controls zoom velocity, independent of touch-move event rate. */
public final class DrnasZoomSpring {
  private boolean tracking;
  private int progress = 50;
  public void begin(int value) { tracking = true; update(value); }
  public void update(int value) { progress = Math.max(0, Math.min(100, value)); }
  public void release() { tracking = false; progress = 50; }
  public boolean isTracking() { return tracking; }
  public double advance(double dt) {
    if (!tracking) return 0;
    double displacement = (progress - 50) / 50.0;
    double magnitude = Math.max(0, (Math.abs(displacement) - 0.08) / 0.92);
    double rate = Math.copySign(12.0 * magnitude * magnitude, displacement);
    return rate * Math.max(0, Math.min(0.05, dt));
  }
}
