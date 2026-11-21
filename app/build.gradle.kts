plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
    namespace = "ro.dj88bid.car"
    compileSdk = 35
    defaultConfig {
        applicationId = "ro.dj88bid.car"
        minSdk = 23
        targetSdk = 28
        // GitHub Actions gives each build a monotonically increasing versionCode.
        // This does not solve Android's signing-certificate compatibility requirement.
        val ciBuild = System.getenv("GITHUB_RUN_NUMBER")?.toIntOrNull()
        versionCode = ciBuild?.let { 10000 + it } ?: 15
        versionName = "1.5-beta" + (ciBuild?.let { ".$it" } ?: "")
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
