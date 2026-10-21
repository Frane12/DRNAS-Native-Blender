package org.blender.blender;
public final class DrnasGpuPolicyTest {
  private static void check(boolean ok){if(!ok)throw new AssertionError();}
  public static void main(String[] args) {
    check(DrnasGpuPolicy.supports("A840","Adreno (TM) 840"));
    check(!DrnasGpuPolicy.supports("A830","Adreno (TM) 840"));
    check(!DrnasGpuPolicy.supports("A6XX_A7XX","Adreno (TM) 840"));
    check(DrnasGpuPolicy.supports("A6XX_A7XX","Adreno 642L"));
    check(DrnasGpuPolicy.supports("A6XX_A7XX","Adreno 740"));
    check(!DrnasGpuPolicy.supports("A840","Snapdragon 840"));
    check(!DrnasGpuPolicy.supports("A810","Adreno 8100"));
    check(DrnasGpuPolicy.supports("MALI_G52","Mali-G52 MC2"));
    check(!DrnasGpuPolicy.supports("MALI_G52","Mali-G72"));
    check(DrnasGpuPolicy.supports("MALI_G52_G72_G76","Mali-G76"));
    check(!DrnasGpuPolicy.supports("MALI_G52_G72_G76","Mali-G610"));
    check(!DrnasGpuPolicy.supports("A840",null));
    for(int[] size:new int[][]{{2400,1080},{1920,1080},{2560,1600},{1080,2400},{1280,720}}) {
      for(int[] cap:new int[][]{{960,544},{1280,720},{1600,900},{1920,1080},{2560,1440}}) {
        int[] r=DrnasGpuPolicy.fit(size[0],size[1],cap[0],cap[1]);
        check(r[0]<=size[0]&&r[1]<=size[1]);
        check(Math.abs((double)r[0]/r[1]-(double)size[0]/size[1])<0.01);
        int cw=size[0]<size[1]?cap[1]:cap[0],ch=size[0]<size[1]?cap[0]:cap[1];
        check(r[0]<=cw&&r[1]<=ch);
      }
    }
    int[] r=DrnasGpuPolicy.fit(1920,1080,960,544);check(r[0]==960&&r[1]==540);
    r=DrnasGpuPolicy.fit(2400,1080,1280,720);check(r[0]==1280&&r[1]==576);
    System.out.println("PASS: driver family exclusions and aspect-preserving presets");
  }
}
