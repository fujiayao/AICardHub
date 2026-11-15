package cn.aicardhub.nfc.core

enum class NfcMode { IDLE, EMULATE, READ, WRITE, VERIFY }
data class EmulationSnapshot(val generation: Long, val message: ByteArray)

/** Memory only: a new process always starts idle. All entry points share one exclusive mode. */
class ModeController(private val now: () -> Long) {
    companion object { const val MAX_SESSION_MS = 300_000L }
    private var generation = 0L
    private var deadline = 0L
    private var mode = NfcMode.IDLE
    private var message: ByteArray? = null
    private var foreground = false

    @Synchronized fun setForeground(value: Boolean) { foreground = value; if (!value) stop() }
    @Synchronized fun start(next: NfcMode, ndef: ByteArray? = null, maxDurationMs: Long = MAX_SESSION_MS): Long {
        require(foreground && next != NfcMode.IDLE && next != NfcMode.VERIFY)
        require(maxDurationMs > 0)
        stop()
        if (next == NfcMode.EMULATE) require(ndef != null && ndef.isNotEmpty() && ndef.size <= NdefUri.MAX_MESSAGE_BYTES)
        mode = next; message = ndef?.copyOf(); deadline = now() + minOf(maxDurationMs, MAX_SESSION_MS)
        return generation
    }
    @Synchronized fun stop() { mode = NfcMode.IDLE; message = null; deadline = 0; generation++ }
    @Synchronized fun current(): NfcMode { expire(); return mode }
    @Synchronized fun isCurrent(token: Long, expected: NfcMode): Boolean {
        expire(); return foreground && token == generation && mode == expected
    }
    @Synchronized fun verify(token: Long): Boolean {
        if (!isCurrent(token, NfcMode.WRITE)) return false
        mode = NfcMode.VERIFY; return true
    }
    @Synchronized fun snapshot(deviceReady: Boolean): EmulationSnapshot? {
        expire()
        if (!deviceReady) { stop(); return null }
        return if (foreground && mode == NfcMode.EMULATE) EmulationSnapshot(generation, message!!.copyOf()) else null
    }
    @Synchronized fun remainingMs(): Long { expire(); return (deadline - now()).coerceAtLeast(0) }
    private fun expire() { if (mode != NfcMode.IDLE && now() >= deadline) stop() }
}
