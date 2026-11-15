package cn.aicardhub.nfc.core

object StickerPolicy {
    fun check(writable: Boolean, capacity: Int, message: ByteArray) {
        require(writable) { "标签为只读，不能写入" }
        require(message.size <= capacity) { "容量不足：需要 ${message.size} 字节，标签可用 $capacity 字节" }
    }
    fun verify(expected: ByteArray, actual: ByteArray?, expectedUri: String, actualUri: String?) {
        require(actual != null && expected.contentEquals(actual) && expectedUri == actualUri) {
            "写后回读不一致，标签内容可能已变化，请重新读取后再试"
        }
    }
}
