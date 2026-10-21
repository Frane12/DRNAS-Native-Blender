import org.blender.blender.DrnasInputHold;
import java.util.ArrayList;

public class DrnasInputHoldTest {
  static void check(boolean value, String message) { if (!value) throw new AssertionError(message); }
  public static void main(String[] args) {
    ArrayList<Boolean> events = new ArrayList<>();
    DrnasInputHold hold = new DrnasInputHold(events::add, 300);
    hold.down(1000); check(hold.isHeld(), "Press must hold immediately");
    hold.up(1050, true); check(!hold.isHeld(), "Single tap releases");
    hold.down(1150); hold.up(1190, true);
    check(hold.isHeld() && hold.isLatched(), "Double tap must latch");
    check(events.size() == 3, "Latch must not send a synthetic UP");
    hold.down(1500); hold.up(1540, true);
    check(!hold.isHeld() && !hold.isLatched(), "Next tap unlocks without re-pressing");
    hold.down(2000); hold.up(2600, true);
    hold.down(2700); hold.up(2740, true);
    check(!hold.isLatched(), "Long drag must not count as a first tap");
    hold.cancel(); hold.down(3000); hold.up(3040, false);
    hold.down(3100); hold.up(3140, true);
    check(!hold.isLatched(), "Movement must not count as double tap");
    hold.cancel(); hold.down(4000); hold.up(4040, true); hold.down(4100); hold.up(4140, true);
    hold.cancel(); check(!hold.isHeld() && !hold.isLatched(), "Background/cancel releases locks");
    DrnasInputHold left = new DrnasInputHold(v -> {}, 300), right = new DrnasInputHold(v -> {}, 300);
    left.down(5000); right.down(5000); left.up(5100, true);
    check(!left.isHeld() && right.isHeld(), "Different fingers/keys must be independent");
    right.cancel();
    System.out.println("PASS: tap, immediate hold, double-tap latch, unlock, long press, movement, cancel and independent keys");
  }
}
