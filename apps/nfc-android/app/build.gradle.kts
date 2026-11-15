import java.net.URI

plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }

val publicBase = providers.gradleProperty("publicBaseUrl").orElse(providers.environmentVariable("NFC_PUBLIC_BASE_URL"))
    .orNull?.trimEnd('/') ?: error("Set -PpublicBaseUrl=https://your-approved-host/deployment-prefix")
val base = URI(publicBase)
require(base.scheme == "https" && base.host != null && base.rawUserInfo == null &&
    base.rawQuery == null && base.rawFragment == null && base.port == -1 &&
    (base.rawPath.isEmpty() || base.rawPath.matches(Regex("(/[A-Za-z0-9_-]+)+")))) { "Invalid publicBaseUrl" }

val signingValues = listOf("NFC_SIGNING_STORE_FILE", "NFC_SIGNING_STORE_PASSWORD", "NFC_SIGNING_KEY_ALIAS", "NFC_SIGNING_KEY_PASSWORD")
    .associateWith { providers.environmentVariable(it).orNull }
val signingReady = signingValues.values.all { !it.isNullOrBlank() }

android {
    namespace = "cn.aicardhub.nfc"
    compileSdk = 35
    defaultConfig {
        applicationId = "cn.aicardhub.nfc"
        minSdk = 26
        targetSdk = 35
        versionCode = 2
        versionName = "1.0.0"
        buildConfigField("String", "PUBLIC_BASE_URL", "\"$publicBase\"")
        manifestPlaceholders["publicHost"] = base.host
        manifestPlaceholders["importPath"] = "${base.rawPath}/share/nfc"
    }
    buildFeatures { buildConfig = true }
    compileOptions { sourceCompatibility = JavaVersion.VERSION_17; targetCompatibility = JavaVersion.VERSION_17 }
    kotlinOptions { jvmTarget = "17" }
    signingConfigs {
        if (signingReady) create("distribution") {
            storeFile = file(signingValues.getValue("NFC_SIGNING_STORE_FILE")!!)
            storePassword = signingValues.getValue("NFC_SIGNING_STORE_PASSWORD")
            keyAlias = signingValues.getValue("NFC_SIGNING_KEY_ALIAS")
            keyPassword = signingValues.getValue("NFC_SIGNING_KEY_PASSWORD")
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            if (signingReady) signingConfig = signingConfigs.getByName("distribution")
        }
    }
    testOptions { unitTests.isReturnDefaultValues = false }
}

tasks.configureEach {
    if (name == "preReleaseBuild") doFirst {
        check(signingReady) { "Release signing requires the four NFC_SIGNING_* environment values; no unsigned release is distributed" }
    }
}

dependencies { testImplementation("junit:junit:4.13.2") }
