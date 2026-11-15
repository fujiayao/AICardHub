package cn.aicardhub.nfc

import android.nfc.NdefMessage
import android.nfc.Tag
import android.nfc.tech.Ndef
import cn.aicardhub.nfc.core.StickerPolicy

data class TagInspection(val original: ByteArray?, val display: String, val capacity: Int, val writable: Boolean)

/** Every call is off the main thread. No NdefFormatable, raw-sector access or lock operation. */
object StickerIo {
    private fun ndef(tag: Tag) = Ndef.get(tag) ?: error("非 NDEF 标签暂不支持，请供应商提供已格式化样品")
    private fun display(message: NdefMessage?): String = message?.records?.joinToString("\n") {
        it.toUri()?.toString() ?: "非网址 NDEF 记录（${it.payload.size} 字节）"
    } ?: "空标签"

    fun inspect(tag: Tag): TagInspection {
        val ndef = ndef(tag)
        try {
            ndef.connect()
            val current = ndef.ndefMessage
            return TagInspection(current?.toByteArray(), display(current), ndef.maxSize, ndef.isWritable)
        } finally { ndef.close() }
    }

    fun writeAndVerify(tag: Tag, inspection: TagInspection, expected: NdefMessage, uri: String,
        beforeWrite: () -> Boolean, beforeVerify: () -> Boolean) {
        val ndef = ndef(tag)
        var attemptedWrite = false
        try {
            ndef.connect()
            StickerPolicy.check(ndef.isWritable, ndef.maxSize, expected.toByteArray())
            val actualBefore = ndef.ndefMessage?.toByteArray()
            require(equal(inspection.original, actualBefore)) { "标签内容已变化，请重新读取并确认覆盖" }
            check(beforeWrite()) { "本次写入已结束，请重新开始" }
            attemptedWrite = true
            ndef.writeNdefMessage(expected)
            check(beforeVerify()) { "写入后操作已结束，尚未回读；标签内容可能已变化" }
            // getNdefMessage issues a live read; cachedNdefMessage is intentionally never used.
            val readback = ndef.ndefMessage
            StickerPolicy.verify(expected.toByteArray(), readback?.toByteArray(), uri,
                readback?.records?.singleOrNull()?.toUri()?.toString())
        } catch (error: Exception) {
            if (attemptedWrite) throw IllegalStateException("${error.message}；已尝试写入，标签内容可能已变化，请重新读取", error)
            throw error
        } finally { ndef.close() }
    }
    private fun equal(a: ByteArray?, b: ByteArray?) = if (a == null) b == null else b != null && a.contentEquals(b)
}
