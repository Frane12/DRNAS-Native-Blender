import org.blender.blender.DrnasZoomSpring;

public class DrnasZoomSpringTest {
  private static void check(boolean condition, String message) {
    if (!condition) throw new AssertionError(message);
  }
  public static void main(String[] args) {
    DrnasZoomSpring spring = new DrnasZoomSpring();
    spring.begin(50);
    check(spring.advance(0.016) == 0, "Center must be still");
    spring.update(53);
    check(spring.advance(0.016) == 0, "Dead zone must suppress jitter");
    spring.update(65);
    double slow = spring.advance(0.016);
    spring.update(95);
    double fast = spring.advance(0.016);
    check(fast > slow * 4 && slow > 0, "Deflection must control nonlinear intensity");
    check(spring.advance(0.016) == fast, "Stationary held slider must keep zooming");
    spring.release();
    check(spring.advance(0.016) == 0 && !spring.isTracking(), "Release/cancel must stop");
    spring.begin(85);
    double sixty = 0, oneTwenty = 0;
    for (int i = 0; i < 60; i++) sixty += spring.advance(1.0 / 60);
    for (int i = 0; i < 120; i++) oneTwenty += spring.advance(1.0 / 120);
    check(Math.abs(sixty - oneTwenty) < 1e-9, "Zoom must not depend on frame rate");
    spring.update(15);
    check(spring.advance(0.016) < 0, "Left must zoom out");
    check(Math.abs(spring.advance(30)) < 0.6, "Resume must not cause a large jump");
    System.out.println("PASS: spring center, dead zone, intensity, stationary hold, release, frame rate, direction and resume");
  }
}
