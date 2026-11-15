package cn.aicardhub.nfc

import android.app.KeyguardManager
import android.content.Context
import android.os.PowerManager
import android.os.SystemClock
import cn.aicardhub.nfc.core.ModeController

object SessionStore {
    val controller = ModeController { SystemClock.elapsedRealtime() }
    @Volatile var onRead: (() -> Unit)? = null
    fun deviceReady(context: Context): Boolean =
        context.getSystemService(PowerManager::class.java).isInteractive &&
            !context.getSystemService(KeyguardManager::class.java).isKeyguardLocked
}
