package cn.aicardhub.nfc.core

import org.junit.Assert.*
import org.junit.Test

class Type4TagTest {
    private fun hex(value: String) = value.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
    private val message = NdefUri.encode("https://cards.example.test/c/a?s=nfc")
    private var live: EmulationSnapshot? = EmulationSnapshot(1, message)
    private var reads = 0
    private val tag = Type4Tag({ live }, { reads++ })
    private fun send(value: String) = tag.process(hex(value))
    private fun sw(value: String, response: ByteArray) = assertArrayEquals(hex(value), response.takeLast(2).toByteArray())
    private fun select() { sw("9000", send("00A4040007D276000085010100")); sw("9000", send("00A4000C02E104")) }
    @Test fun selectCcAndNdefExposeStandardLengths() {
        sw("9000", send("00A4040007D2760000850101"))
        sw("9000", send("00A4000C02E103"))
        val cc = send("00B000000F")
        assertEquals(17, cc.size); assertEquals(0x20, cc[2].toInt()); sw("9000", cc)
        sw("9000", send("00A4000C02E104"))
        assertArrayEquals(byteArrayOf(0, message.size.toByte(), 0x90.toByte(), 0), send("00B0000002"))
    }
    @Test fun segmentedReadCountsOnlyCompleteCoverageOnce() {
        select(); send("00B0000002"); assertEquals(0, reads)
        val tail = tag.process(byteArrayOf(0, 0xB0.toByte(), 0, 2, message.size.toByte()))
        sw("9000", tail); assertArrayEquals(message, tail.dropLast(2).toByteArray()); assertEquals(1, reads)
        send("00B0000002"); assertEquals(1, reads)
    }
    @Test fun incompleteAndOutOfOrderReadsDoNotClaimSuccess() {
        select(); send("00B0000404"); assertEquals(0, reads)
        send("00B0000002"); assertEquals(0, reads)
    }
    @Test fun malformedUnsupportedAndUnauthorizedCommandsHaveStatusWords() {
        sw("6985", send("00B0000002")); sw("6700", send("00")); sw("6E00", send("80B0000002"))
        sw("6D00", send("00D6000000")); sw("6A82", send("00A4040007D2760000850102"))
        sw("6700", send("00A4040008D2760000850101")); select()
        sw("6A86", send("00B0800001")); sw("6B00", send("00B07FFF01")); sw("6A82", send("00A4000C02FFFF"))
        sw("6282", send("00B0000000"))
    }
    @Test fun stopExpiryAndPayloadSwitchInvalidateSelectedSession() {
        select(); live = null; sw("6985", send("00B0000002"))
        live = EmulationSnapshot(2, message); select(); live = EmulationSnapshot(3, message + 1)
        sw("6985", send("00B0000002")); sw("6985", send("00B0000002"))
        select(); sw("9000", send("00B0000002"))
    }
    @Test fun longMessagesHaveFourBytePayloadLengthAndAreNeverTruncated() {
        val long = NdefUri.encode("https://example.test/" + "a".repeat(600))
        assertEquals(0xC1, long[0].toInt() and 255)
        assertTrue(long.size > 600)
        assertThrows(IllegalArgumentException::class.java) { NdefUri.encode("https://example.test/" + "a".repeat(9000)) }
        live = EmulationSnapshot(8, long); select()
        val chunk = send("00B0010000"); assertEquals(258, chunk.size); sw("9000", chunk)
    }
}
