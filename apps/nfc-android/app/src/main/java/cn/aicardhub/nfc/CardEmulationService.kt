package cn.aicardhub.nfc

import android.nfc.NfcAdapter
import android.nfc.cardemulation.HostApduService
import android.os.Bundle
import cn.aicardhub.nfc.core.Type4Tag

class CardEmulationService : HostApduService() {
    private val tag = Type4Tag(
        { SessionStore.controller.snapshot(SessionStore.deviceReady(this) && NfcAdapter.getDefaultAdapter(this)?.isEnabled == true) },
        { SessionStore.onRead?.invoke() },
    )
    override fun processCommandApdu(commandApdu: ByteArray?, extras: Bundle?): ByteArray =
        commandApdu?.let(tag::process) ?: byteArrayOf(0x67, 0)
    override fun onDeactivated(reason: Int) = tag.reset()
    override fun onDestroy() { tag.reset(); SessionStore.controller.stop(); super.onDestroy() }
}
