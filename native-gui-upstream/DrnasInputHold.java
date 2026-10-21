package org.blender.blender;

/** A normal press releases on UP; two short taps latch until the next press. */
public final class DrnasInputHold {
  public interface Sink { void changed(boolean held); }
  private final Sink sink;
  private final long doubleTapMillis;
  private boolean held, latched, down, secondTap, unlocking;
  private long previousUp = Long.MIN_VALUE / 2, downAt;
  public DrnasInputHold(Sink sink, long interval) { this.sink = sink; doubleTapMillis = interval; }
  public boolean isHeld() { return held; }
  public boolean isLatched() { return latched; }
  private void setHeld(boolean value) {
    if (held != value) { held = value; sink.changed(value); }
  }
  public void down(long now) {
    down = true; downAt = now;
    unlocking = latched;
    if (unlocking) {
      latched = false; previousUp = Long.MIN_VALUE / 2; setHeld(false); return;
    }
    secondTap = now - previousUp >= 0 && now - previousUp <= doubleTapMillis;
    setHeld(true);
  }
  public void up(long now, boolean shortTap) {
    if (!down) return;
    down = false;
    if (unlocking) { unlocking = false; return; }
    boolean tap = shortTap && now - downAt <= 250;
    if (secondTap && tap) {
      latched = true; previousUp = Long.MIN_VALUE / 2;
    } else {
      setHeld(false);
      previousUp = tap ? now : Long.MIN_VALUE / 2;
    }
    secondTap = false;
  }
  public void cancel() {
    latched = down = secondTap = unlocking = false;
    previousUp = Long.MIN_VALUE / 2; setHeld(false);
  }
}
