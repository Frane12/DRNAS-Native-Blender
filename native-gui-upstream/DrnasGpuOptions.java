package org.blender.blender;
import android.app.Activity;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.*;
import android.system.Os;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;

/** Native Vulkan selection; never install a driver system-wide. */
public final class DrnasGpuOptions {
  private static final String PREFS="drnas_native_gpu_v1";
  private static final int[][] CAPS={{0,0},{-1,-1},{960,544},{1280,720},{1600,900},{1920,1080},{2560,1440}};
  private static String renderer="unavailable", launchDriver="system", notice="";
  private static SharedPreferences prefs(Activity a){return a.getSharedPreferences(PREFS,0);}
  private static JSONArray catalog(Activity a) throws Exception {
    try(InputStream in=a.getAssets().open("drnas_gpu_drivers.json")) {
      ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] b=new byte[8192];int n;
      while((n=in.read(b))!=-1)out.write(b,0,n);
      return new JSONObject(out.toString("UTF-8")).getJSONArray("drivers");
    }
  }
  public static void apply(Activity a) {
    renderer=DrnasGpuProfile.renderer;
    SharedPreferences p=prefs(a);
    String wanted=p.getString("driver","system");
    if(p.getBoolean("boot_pending",false)) {
      notice="Prethodni GPU start nije uspio; vraćen sistemski driver.";
      wanted="system";
      p.edit().putString("driver","system").putBoolean("boot_pending",false).commit();
    }
    try {
      Os.unsetenv("DRNAS_GPU_DRIVER");Os.unsetenv("DRNAS_GPU_KIND");
      JSONArray entries=catalog(a);
      for(int i=0;i<entries.length();i++) {
        JSONObject e=entries.getJSONObject(i);
        if(!e.getString("id").equals(wanted) || !DrnasGpuPolicy.supports(e.getString("target"),renderer) || Build.VERSION.SDK_INT<e.getInt("minApi"))continue;
        String lib=e.getString("library");
        if(!lib.matches("libdrnas_gpu_[a-z0-9_]+\\.so"))break;
        if(!new File(a.getApplicationInfo().nativeLibraryDir,lib).isFile())break;
        if (!p.edit().putBoolean("boot_pending",true).commit()) break;
        Os.setenv("DRNAS_GPU_DRIVER",lib,true);Os.setenv("DRNAS_GPU_KIND",e.getString("kind"),true);
        launchDriver=wanted;
        break;
      }
      int res=p.getInt("resolution",0);if(res<0||res>=CAPS.length)res=0;
      Os.setenv("DRNAS_RENDER_OVERRIDE",res==0?"0":"1",true);
      Os.setenv("DRNAS_RENDER_WIDTH",Integer.toString(Math.max(0,CAPS[res][0])),true);
      Os.setenv("DRNAS_RENDER_HEIGHT",Integer.toString(Math.max(0,CAPS[res][1])),true);
      File ready=new File(a.getFilesDir(),"drnas-gpu-frame-ready");ready.delete();
      Os.setenv("DRNAS_GPU_READY_FILE",ready.getAbsolutePath(),true);
    } catch(Exception e) {
      try{Os.unsetenv("DRNAS_GPU_DRIVER");Os.unsetenv("DRNAS_GPU_KIND");}catch(Exception ignored){}
      launchDriver="system";
      p.edit().putBoolean("boot_pending",false).commit();
      notice="GPU paket nije dostupan; koristi se sistemski driver.";
    }
  }
  public static void watch(Activity a) {
    final File ready=new File(a.getFilesDir(),"drnas-gpu-frame-ready");
    final Handler h=new Handler(Looper.getMainLooper());
    h.postDelayed(new Runnable(){public void run(){
      if(a.isFinishing()||a.isDestroyed())return;
      if(ready.isFile()) {prefs(a).edit().putBoolean("boot_pending",false).apply();return;}
      h.postDelayed(this,1000);
    }},1000);
    if(!notice.isEmpty())Toast.makeText(a,notice,Toast.LENGTH_LONG).show();
  }
  private static TextView label(Activity a,String text) {
    TextView v=new TextView(a);v.setText(text);v.setTextColor(Color.WHITE);v.setTextSize(13);v.setPadding(10,12,10,8);return v;
  }
  private static void select(Activity a,LinearLayout rows,List<String> names,int index,java.util.function.IntConsumer change) {
    Spinner spinner=new Spinner(a,Spinner.MODE_DROPDOWN);
    ArrayAdapter<String> adapter=new ArrayAdapter<>(a,android.R.layout.simple_spinner_item,names);
    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
    spinner.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.LTGRAY));
    spinner.setAdapter(adapter);spinner.setSelection(index,false);
    rows.addView(spinner,new LinearLayout.LayoutParams(-1,Math.round(52*a.getResources().getDisplayMetrics().density)));
    final boolean[] armed={false};
    spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
      public void onNothingSelected(AdapterView<?> parent){}
      public void onItemSelected(AdapterView<?> p,View v,int pos,long id){
        if(v instanceof TextView)((TextView)v).setTextColor(Color.WHITE);
        if(armed[0])change.accept(pos);
      }
    });
    spinner.post(()->armed[0]=true);
  }
  public static void install(Activity a,LinearLayout rows) {
    SharedPreferences p=prefs(a);
    rows.addView(label(a,"GPU DRIVER • "+renderer));
    List<String> labels=new ArrayList<>(),ids=new ArrayList<>();
    labels.add("Sistemski Vulkan (zadano)");ids.add("system");
    try {
      JSONArray entries=catalog(a);
      for(int i=0;i<entries.length();i++) {
        JSONObject e=entries.getJSONObject(i);
        if(DrnasGpuPolicy.supports(e.getString("target"),renderer)&&Build.VERSION.SDK_INT>=e.getInt("minApi")) {
          labels.add(e.getString("label"));ids.add(e.getString("id"));
        }
      }
    } catch(Exception ignored){}
    int chosen=Math.max(0,ids.indexOf(p.getString("driver","system")));
    TextView pending=label(a,"Aktivno pri pokretanju: "+launchDriver+"\nPromjene se primjenjuju nakon spremanja rada i ponovnog pokretanja aplikacije.");
    select(a,rows,labels,chosen,i->{p.edit().putString("driver",ids.get(i)).apply();pending.setText("Driver spremljen. Spremi rad i ponovno pokreni aplikaciju za primjenu.");});
    rows.addView(label(a,"REZOLUCIJA • očuvan omjer zaslona"));
    android.graphics.Rect bounds=a.getWindowManager().getCurrentWindowMetrics().getBounds();
    int w=bounds.width(),h=bounds.height();
    List<String> resolutions=new ArrayList<>();
    resolutions.add("Automatski (GPU / memorija)");resolutions.add("Izvorna • "+w+"×"+h);
    for(int i=2;i<CAPS.length;i++) {
      int[] fit=DrnasGpuPolicy.fit(w,h,CAPS[i][0],CAPS[i][1]);
      resolutions.add(CAPS[i][0]+"×"+CAPS[i][1]+" → "+fit[0]+"×"+fit[1]);
    }
    int res=p.getInt("resolution",0);if(res<0||res>=CAPS.length)res=0;
    select(a,rows,resolutions,res,i->{p.edit().putInt("resolution",i).apply();pending.setText("Rezolucija spremljena. Spremi rad i ponovno pokreni aplikaciju za primjenu.");});
    rows.addView(pending);
  }
  private DrnasGpuOptions(){}
}
