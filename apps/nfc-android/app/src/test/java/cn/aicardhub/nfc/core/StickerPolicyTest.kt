package cn.aicardhub.nfc.core

import org.junit.Assert.*
import org.junit.Test

class StickerPolicyTest {
    @Test fun capacityUsesEncodedBytesAndReadOnlyFails() {
        val message = NdefUri.encode("https://example.test/c/a?s=nfc")
        StickerPolicy.check(true, message.size, message)
        assertThrows(IllegalArgumentException::class.java) { StickerPolicy.check(true, message.size - 1, message) }
        assertThrows(IllegalArgumentException::class.java) { StickerPolicy.check(false, 888, message) }
    }
    @Test fun readbackMustMatchBytesAndUri() {
        val expected = byteArrayOf(1, 2)
        StickerPolicy.verify(expected, expected.copyOf(), "https://a", "https://a")
        assertThrows(IllegalArgumentException::class.java) { StickerPolicy.verify(expected, byteArrayOf(1), "https://a", "https://a") }
        assertThrows(IllegalArgumentException::class.java) { StickerPolicy.verify(expected, expected, "https://a", "https://b") }
        assertThrows(IllegalArgumentException::class.java) { StickerPolicy.verify(expected, null, "https://a", null) }
    }
}
