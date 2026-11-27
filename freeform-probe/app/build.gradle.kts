plugins { id("com.android.application") }
android { namespace = "ro.dj88bid.freeform"; compileSdk = 35
 defaultConfig { applicationId = "ro.dj88bid.freeform"; minSdk = 24; targetSdk = 32; versionCode = 1; versionName = "1.0" }
 compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
}