import java.net.URI

plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }

val publicBase = providers.gradleProperty("publicBaseUrl").orElse(providers.environmentVariable("NFC_PUBLIC_BASE_URL"))
    .orNull?.trimEnd('/') ?: error("Set -PpublicBaseUrl=https://your-approved-host/deployment-prefix")
val base = URI(publicBase)
require(base.scheme == "https" && base.host != null && base.rawUserInfo == null &&
    base.rawQuery == null && base.rawFragment == null && base.port == -1 &&
    (base.rawPath.isEmpty() || base.rawPath.matches(Regex("(/[A-Za-z0-9_-]+)+")))) { "Invalid publicBaseUrl" }

android {
    namespace = "cn.aicardhub.nfc"
    compileSdk = 35
    defaultConfig {
        applicationId = "cn.aicardhub.nfc"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-candidate"
        buildConfigField("String", "PUBLIC_BASE_URL", "\"$publicBase\"")
        manifestPlaceholders["publicHost"] = base.host
        manifestPlaceholders["importPath"] = "${base.rawPath}/share/nfc"
    }
    buildFeatures { buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    buildTypes { release { isMinifyEnabled = false } }
    testOptions { unitTests.isReturnDefaultValues = false }
}

dependencies { testImplementation("junit:junit:4.13.2") }
