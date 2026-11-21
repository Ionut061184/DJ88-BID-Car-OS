plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "ro.dj88bid.car"
    compileSdk = 35
    defaultConfig {
        applicationId = "ro.dj88bid.car"
        minSdk = 23
        targetSdk = 28
        versionCode = 14
        versionName = "1.4-beta"
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
