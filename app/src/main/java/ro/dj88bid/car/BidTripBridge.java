package ro.dj88bid.car;

import android.Manifest;
import android.app.Activity;
import android.content.Context;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.os.SystemClock;
import android.webkit.JavascriptInterface;
import org.json.JSONObject;

/** GPS-only trip bridge. No additional permission requests or persistent route storage. */
public final class BidTripBridge implements LocationListener {
    private final Activity activity;
    private final LocationManager manager;
    private volatile Location fix;
    private volatile boolean active;
    private volatile boolean foreground;
    public BidTripBridge(Activity activity) {
        this.activity = activity;
        manager = (LocationManager) activity.getSystemService(Context.LOCATION_SERVICE);
    }
    public void setForeground(boolean value) {
        foreground = value;
        if (!value) stopNow();
    }
    @JavascriptInterface public void start() {
        activity.runOnUiThread(() -> {
            stopNow();
            if (!foreground || manager == null || activity.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) return;
            try {
                if (!manager.isProviderEnabled(LocationManager.GPS_PROVIDER)) return;
                active = true;
                manager.requestLocationUpdates(LocationManager.GPS_PROVIDER, 1000L, 0f, this);
            } catch (RuntimeException e) { stopNow(); }
        });
    }
    @JavascriptInterface public void stop() { activity.runOnUiThread(this::stopNow); }
    public void stopNow() {
        active = false; fix = null;
        if (manager != null) try { manager.removeUpdates(this); } catch (RuntimeException ignored) {}
    }
    @Override public void onLocationChanged(Location loc) {
        if (foreground && active && LocationManager.GPS_PROVIDER.equals(loc.getProvider()) && !loc.isFromMockProvider()) fix = new Location(loc);
    }
    @Override public void onProviderDisabled(String provider) { if (LocationManager.GPS_PROVIDER.equals(provider)) fix = null; }
    @Override public void onProviderEnabled(String provider) {}
    @Override public void onStatusChanged(String provider, int status, Bundle extras) {}
    @JavascriptInterface public String snapshot() {
        try {
            Location l = fix;
            if (!foreground || !active || l == null || !l.hasAccuracy() || activity.checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) return "{\"available\":false}";
            long age = (SystemClock.elapsedRealtimeNanos() - l.getElapsedRealtimeNanos()) / 1000000L;
            if (age < 0 || age > 5000) return "{\"available\":false}";
            JSONObject j = new JSONObject();
            j.put("available", true).put("provider", "gps").put("ageMs", age).put("fixId", l.getElapsedRealtimeNanos()/1000000L).put("accuracy", l.getAccuracy()).put("lat", l.getLatitude()).put("lon", l.getLongitude());
            if (l.hasSpeed()) j.put("speedMps", l.getSpeed());
            if (l.hasBearing()) j.put("bearing", l.getBearing());
            if (l.hasAltitude()) j.put("altitude", l.getAltitude());
            return j.toString();
        } catch (Exception e) { return "{\"available\":false}"; }
    }
}
