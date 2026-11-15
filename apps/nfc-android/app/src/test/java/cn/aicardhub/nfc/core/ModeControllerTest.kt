package cn.aicardhub.nfc.core

import org.junit.Assert.*
import org.junit.Test

class ModeControllerTest {
    private var time = 100L
    private val controller = ModeController { time }
    @Test fun coldStartIsIdleAndForegroundRequired() {
        assertEquals(NfcMode.IDLE, controller.current())
        assertNull(controller.snapshot(true))
        assertThrows(IllegalArgumentException::class.java) { controller.start(NfcMode.READ) }
    }
    @Test fun modesAreExclusiveAndOldTokenCannotWrite() {
        controller.setForeground(true)
        val first = controller.start(NfcMode.EMULATE, byteArrayOf(1))
        val second = controller.start(NfcMode.WRITE)
        assertNull(controller.snapshot(true))
        assertFalse(controller.isCurrent(first, NfcMode.EMULATE))
        assertTrue(controller.verify(second))
        assertEquals(NfcMode.VERIFY, controller.current())
        assertFalse(controller.verify(second))
    }
    @Test fun expiresAtFiveMinutesEvenWithoutUiTick() {
        controller.setForeground(true); controller.start(NfcMode.EMULATE, byteArrayOf(1))
        time += ModeController.MAX_SESSION_MS - 1; assertNotNull(controller.snapshot(true))
        time++; assertNull(controller.snapshot(true)); assertEquals(NfcMode.IDLE, controller.current())
    }
    @Test fun backgroundLockAndStopRevokeSession() {
        controller.setForeground(true); controller.start(NfcMode.EMULATE, byteArrayOf(1))
        assertNull(controller.snapshot(false)); assertEquals(NfcMode.IDLE, controller.current())
        controller.start(NfcMode.READ); controller.setForeground(false); assertEquals(NfcMode.IDLE, controller.current())
        controller.setForeground(true); assertNull(controller.snapshot(true))
    }
    @Test fun payloadCannotMutateAfterStart() {
        controller.setForeground(true)
        val bytes = byteArrayOf(1); controller.start(NfcMode.EMULATE, bytes); bytes[0] = 9
        assertArrayEquals(byteArrayOf(1), controller.snapshot(true)!!.message)
    }
    @Test fun activityDeadlineCanShortenButNeverExtendFiveMinutes() {
        controller.setForeground(true); controller.start(NfcMode.EMULATE, byteArrayOf(1), 1000)
        time += 1000; assertNull(controller.snapshot(true))
        controller.start(NfcMode.READ, maxDurationMs = 600_000)
        time += 300_000; assertEquals(NfcMode.IDLE, controller.current())
    }
}
