package ro.dj88bid.car;
import android.content.Context;
import java.lang.reflect.Proxy;
import java.util.concurrent.atomic.AtomicIntegerArray;

/** Passive diagnostic only. Never sends MCU commands or changes settings. */
public final class QfMcuPassiveProbe {
    private final AtomicIntegerArray counts = new AtomicIntegerArray(256);
    private volatile boolean active;
    private volatile String status = "idle";
    private Object listener;
    public synchronized String start(Context context) {
        if (listener != null) return status;
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
                            if (data.length > 0) counts.incrementAndGet(data[0] & 255);
                        }
                        return null;
                    default: return null;
                }
            });
            manager.getClass().getMethod("RPC_RequestMcuInfoChangedListener", type).invoke(manager, listener);
            return status = "listener_requested";
        } catch (Exception | LinkageError e) {
            active = false;
            return status = "failed:" + e.getClass().getSimpleName();
        }
    }
    public int count(int command) { return counts.get(command & 255); }
    public String status() { return status; }
    public void stopCapture() { active = false; }
}
