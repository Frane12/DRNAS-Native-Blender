package org.blender.blender;
import android.app.Activity;
import android.os.*;
import android.system.Os;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Bounded initialization log; requested driver and observed evidence remain distinct. */
public final class DrnasInitLog {
  private static File local, shared;
  private static Activity activity;
  private static final Handler handler=new Handler(Looper.getMainLooper());
  public static void start(Activity a) {
    activity=a;
    local=new File(new File(a.getFilesDir(),"DRNAS"),"native-blender-init.log");
    local.getParentFile().mkdirs();
    try {
      if(local.exists())Files.copy(local.toPath(),new File(local.getParentFile(),"native-blender-init.previous.log").toPath(),StandardCopyOption.REPLACE_EXISTING);
      Files.write(local.toPath(),new byte[0]);
      Os.setenv("DRNAS_INIT_LOG",local.getAbsolutePath(),true);
    }catch(Exception ignored){}
    line("START "+new Date()+" package="+a.getPackageName());
    line("Android="+Build.VERSION.RELEASE+" model="+Build.MANUFACTURER+" "+Build.MODEL);
    line("EGL renderer="+DrnasGpuProfile.renderer);
    line("REQUESTED driver="+Os.getenv("DRNAS_GPU_DRIVER")+" kind="+Os.getenv("DRNAS_GPU_KIND"));
    line("Resolution cap="+Os.getenv("DRNAS_RENDER_WIDTH")+"x"+Os.getenv("DRNAS_RENDER_HEIGHT")+" stretch="+a.getSharedPreferences("drnas_native_gpu_v1",0).getBoolean("stretch_screen",false));
    // Native loader messages only, for our own PID. Stop after startup; no frame tracing.
    try {
      final java.lang.Process process=new ProcessBuilder("logcat","-v","time","-T","1","--pid="+android.os.Process.myPid(),"blender-turnip:I","DRNAS-GPU:I","libc:F","*:S").redirectErrorStream(true).start();
      Thread reader=new Thread(()->{
        try(BufferedReader in=new BufferedReader(new InputStreamReader(process.getInputStream(),StandardCharsets.UTF_8))) {
          String value;int lines=0;while((value=in.readLine())!=null&&lines++<180)line("NATIVE "+value);
        }catch(Exception ignored){} finally{process.destroy();}
      },"DRNAS-init-log");reader.setDaemon(true);reader.start();
      handler.postDelayed(process::destroy,25000);
    }catch(Exception e){line("Native log capture unavailable: "+e.getClass().getSimpleName());}
    final long until=android.os.SystemClock.uptimeMillis()+60000;
    handler.postDelayed(new Runnable(){boolean frame=false;public void run(){
      if(a.isFinishing()||a.isDestroyed())return;
      File ready=new File(a.getFilesDir(),"drnas-gpu-frame-ready");
      if(!frame&&ready.isFile()) {
        frame=true;line("OBSERVED first Vulkan frame PRESENTED");
        try {
          for(String map:Files.readAllLines(Paths.get("/proc/self/maps"),StandardCharsets.UTF_8)) {
            if(map.contains("libdrnas_gpu_")&&map.contains("r-xp"))line("MAPPED (not alone proof of active ICD) "+map.substring(map.lastIndexOf(' ')+1));
          }
        }catch(Exception ignored){}
      }
      publish();if(android.os.SystemClock.uptimeMillis()<until)handler.postDelayed(this,1000);
    }},1000);
  }
  public static synchronized void line(String value) {
    if(local==null||local.length()>128*1024)return;
    try(FileOutputStream out=new FileOutputStream(local,true)){out.write((value+"\n").getBytes(StandardCharsets.UTF_8));}catch(Exception ignored){}
  }
  public static synchronized void publish() {
    if(local==null||!local.isFile()||activity==null)return;
    File folder=new File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS),"DRNAS");
    try {
      if(!folder.isDirectory()&&!folder.mkdirs())return;
      File target=new File(folder,"native-blender-init.log");
      if(shared==null) {
        if(target.isFile())Files.copy(target.toPath(),new File(folder,"native-blender-init.previous.log").toPath(),StandardCopyOption.REPLACE_EXISTING);
        shared=target;
      }
      Files.copy(local.toPath(),target.toPath(),StandardCopyOption.REPLACE_EXISTING);
    }catch(Exception ignored){}
  }
  public static String path(){publish();return shared!=null?shared.getAbsolutePath():local==null?"":local.getAbsolutePath();}
  private DrnasInitLog(){}
}
