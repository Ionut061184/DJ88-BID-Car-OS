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

    // Stable release signing is enabled only when GitHub Actions injects the secrets.
    // Never put private keystore bytes or passwords in the repository.
    val stableStore = System.getenv("BID_KEYSTORE_PATH")
    val stableAlias = System.getenv("BID_KEY_ALIAS")
    val stableStorePass = System.getenv("BID_KEYSTORE_PASSWORD")
    val stableKeyPass = System.getenv("BID_KEY_PASSWORD")
    if (!stableStore.isNullOrBlank() && !stableAlias.isNullOrBlank() &&
        !stableStorePass.isNullOrBlank() && !stableKeyPass.isNullOrBlank()) {
        signingConfigs {
            create("bidStable") {
                storeFile = file(stableStore)
                storePassword = stableStorePass
                keyAlias = stableAlias
                keyPassword = stableKeyPass
                enableV1Signing = true
                enableV2Signing = true
            }
        }
        buildTypes {
            getByName("release") {
                isMinifyEnabled = false
                signingConfig = signingConfigs.getByName("bidStable")
            }
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
}
