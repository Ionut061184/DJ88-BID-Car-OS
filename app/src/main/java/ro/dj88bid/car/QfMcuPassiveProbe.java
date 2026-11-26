package ro.dj88bid.car;
import android.content.Context;
import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicIntegerArray;

/** Passive diagnostic only. Never sends MCU commands or changes settings. */
public final class QfMcuPassiveProbe {
    private final AtomicIntegerArray counts = new AtomicIntegerArray(256);
    private final java.util.ArrayDeque<String> samples = new java.util.ArrayDeque<>();
    private volatile boolean active;
    private volatile String status = "idle";
    private Object listener;
    public synchronized String start(Context context) {
        for (int i = 0; i < 256; i++) counts.set(i, 0);
        synchronized (samples) { samples.clear(); }
        if (listener != null) { active = true; return status = "listener_reused"; }
        try {
            Object manager = context.getSystemService("mcu_service");
            if (manager == null) return status = "service_unavailable";
            Class<?> type = Class.forName("android.qf.mcu.McuListener");
            active = true;
            listener = Proxy.newProxyInstance(type.getClassLoader(), new Class<?>[]{type}, (p,m,a) -> {
                switch (m.getName()) {
                    case "hashCode": return System.identityHashCode(p);
                    case "equals": return a != null && a.length == 1 && p == a[0];
                    case "toString": return "BID passive MCU listener";
                    case "onMcuInfoChanged":
                        if (active && a != null && a.length == 1 && a[0] instanceof byte[]) {
                            byte[] data = (byte[]) a[0];
                            if (data.length > 0) { int cmd=data[0]&255; counts.incrementAndGet(cmd); if(cmd==65||cmd==41) record(data); }
                        }
                        return null;
                    default: return null;
                }
            });
            manager.getClass().getMethod("RPC_RequestMcuInfoChangedListener", type).invoke(manager, listener);
            return status = "listener_requested";
        } catch (Exception | LinkageError e) {
            active = false;
            listener = null;
            return status = "failed:" + e.getClass().getSimpleName();
        }
    }
    private void record(byte[] data) {
        StringBuilder s = new StringBuilder();
        s.append(android.os.SystemClock.elapsedRealtime()).append(" ms len=").append(data.length).append(": ");
        for (int i=0; i<Math.min(data.length,256); i++) { int b=data[i]&255; if(b<16)s.append('0'); s.append(Integer.toHexString(b)).append(' '); }
        synchronized(samples) { if(samples.size()>=80)samples.removeFirst(); samples.addLast(s.toString()); }
    }
    public String samples() { synchronized(samples) { return android.text.TextUtils.join("\n",samples); } }
    public int count(int command) { return counts.get(command & 255); }
    public String status() { return status; }
    public void stopCapture() { active = false; }
}
