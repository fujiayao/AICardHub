package cn.aicardhub.nfc.core

/** Read-only NFC Forum Type 4 mapping 2.0. Every APDU is gated by the live session. */
class Type4Tag(private val current: () -> EmulationSnapshot?, private val onRead: () -> Unit = {}) {
    private var snapshot: EmulationSnapshot? = null
    private var file: Int? = null
    private var covered = BooleanArray(0)
    private var notified = false
    @Synchronized fun reset() { snapshot = null; file = null; covered = BooleanArray(0); notified = false }

    @Synchronized fun process(command: ByteArray): ByteArray {
        val live = current() ?: return fail(0x69, 0x85).also { reset() }
        if (snapshot != null && snapshot!!.generation != live.generation) return fail(0x69, 0x85).also { reset() }
        if (command.size < 4) return fail(0x67, 0x00)
        if (u(command[0]) != 0) return fail(0x6E, 0x00)
        val ins = u(command[1]); val p1 = u(command[2]); val p2 = u(command[3])
        if (ins == 0xA4) {
            if (command.size < 5) return fail(0x67, 0x00)
            val length = u(command[4])
            if (length == 0 || command.size !in setOf(5 + length, 6 + length)) return fail(0x67, 0x00)
            val data = command.copyOfRange(5, 5 + length)
            if (p1 == 4 && p2 in setOf(0, 0x0C)) {
                if (!data.contentEquals(AID)) return fail(0x6A, 0x82)
                snapshot = live; file = null; covered = BooleanArray(live.message.size + 2); notified = false
                return OK
            }
            if (p1 != 0 || p2 !in setOf(0, 0x0C)) return fail(0x6A, 0x86)
            if (snapshot == null) return fail(0x69, 0x85)
            if (data.size != 2) return fail(0x67, 0x00)
            val id = (u(data[0]) shl 8) or u(data[1])
            if (id != 0xE103 && id != 0xE104) return fail(0x6A, 0x82)
            file = id; return OK
        }
        if (ins != 0xB0) return fail(0x6D, 0x00)
        if (command.size != 5) return fail(0x67, 0x00)
        val selected = snapshot ?: return fail(0x69, 0x85)
        if (p1 and 0x80 != 0) return fail(0x6A, 0x86)
        val content = when (file) {
            0xE103 -> CC
            0xE104 -> byteArrayOf((selected.message.size ushr 8).toByte(), selected.message.size.toByte()) + selected.message
            else -> return fail(0x69, 0x85)
        }
        val offset = (p1 shl 8) or p2
        if (offset >= content.size) return fail(0x6B, 0x00)
        val count = if (u(command[4]) == 0) 256 else u(command[4])
        val end = minOf(offset + count, content.size)
        if (file == 0xE104) {
            for (index in offset until end) covered[index] = true
            if (!notified && covered.all { it }) { notified = true; onRead() }
        }
        return content.copyOfRange(offset, end) + if (end - offset < count) fail(0x62, 0x82) else OK
    }
    private fun u(value: Byte) = value.toInt() and 0xFF
    private fun fail(a: Int, b: Int) = byteArrayOf(a.toByte(), b.toByte())
    companion object {
        private val AID = byteArrayOf(0xD2.toByte(), 0x76, 0, 0, 0x85.toByte(), 1, 1)
        private val OK = byteArrayOf(0x90.toByte(), 0)
        // CCLEN=15, mapping2.0, MLe=256, MLc=255, NDEF EF E104, max8194, read only.
        private val CC = byteArrayOf(0, 15, 0x20, 1, 0, 0, 0xFF.toByte(), 4, 6, 0xE1.toByte(), 4, 0x20, 2, 0, 0xFF.toByte())
    }
}
