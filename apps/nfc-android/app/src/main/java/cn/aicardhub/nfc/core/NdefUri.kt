package cn.aicardhub.nfc.core

/** Standard NFC Forum URI RTD (https:// prefix 0x04), not a text record. */
object NdefUri {
    const val MAX_MESSAGE_BYTES = 8192
    fun encode(uri: String): ByteArray {
        require(uri.startsWith("https://"))
        val payload = byteArrayOf(0x04) + uri.removePrefix("https://").toByteArray(Charsets.UTF_8)
        val header = if (payload.size <= 255) byteArrayOf(0xD1.toByte(), 1, payload.size.toByte())
        else byteArrayOf(0xC1.toByte(), 1, (payload.size ushr 24).toByte(), (payload.size ushr 16).toByte(),
            (payload.size ushr 8).toByte(), payload.size.toByte())
        val message = header + byteArrayOf(0x55) + payload
        require(message.size <= MAX_MESSAGE_BYTES) { "NDEF 内容超过 8192 字节，不会截断" }
        return message
    }
}
