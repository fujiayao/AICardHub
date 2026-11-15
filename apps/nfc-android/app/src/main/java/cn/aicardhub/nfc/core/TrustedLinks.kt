package cn.aicardhub.nfc.core

import java.net.URI
import java.net.URLDecoder
import java.net.URLEncoder
import java.nio.charset.StandardCharsets.UTF_8

enum class ImportMode { EMULATE, WRITE }
data class ImportRequest(val code: String, val mode: ImportMode, val campaignId: Long?)

/** A single parse/decode boundary. Input never selects an origin or deployment prefix. */
class TrustedLinks(publicBase: String) {
    private val base = URI(publicBase.trimEnd('/'))
    private val prefix = base.rawPath.orEmpty()
    init {
        require(base.scheme == "https" && base.host != null && base.rawUserInfo == null &&
            base.port == -1 && base.rawQuery == null && base.rawFragment == null)
        require(prefix.isEmpty() || prefix.matches(Regex("(/[A-Za-z0-9_-]+)+")))
    }

    fun parse(input: String): ImportRequest {
        require(input.length <= 8192) { "链接过长" }
        val uri = URI(input.trim())
        require(sameOrigin(uri) && uri.rawFragment == null) { "只接受受信任站点的 HTTPS 链接" }
        val query = query(uri.rawQuery)
        val path = uri.rawPath
        val result = when {
            path == "$prefix/share/nfc" -> {
                require(query.keys.all { it in setOf("code", "mode", "e") }) { "不支持的导入参数" }
                val mode = when (query["mode"] ?: "emulate") {
                    "emulate" -> ImportMode.EMULATE
                    "write" -> ImportMode.WRITE
                    else -> throw IllegalArgumentException("未知操作模式")
                }
                ImportRequest(validCode(query["code"] ?: error("缺少名片 code")), mode, campaign(query["e"]))
            }
            path?.startsWith("$prefix/c/") == true -> {
                require(query.keys.all { it in setOf("s", "e") } && query["s"] == "nfc") { "请导入 s=nfc 的公开短链" }
                ImportRequest(validCode(decode(path.removePrefix("$prefix/c/"))), ImportMode.EMULATE, campaign(query["e"]))
            }
            else -> throw IllegalArgumentException("只支持 NFC 配置链接或公开 NFC 短链")
        }
        require(result.mode != ImportMode.WRITE || result.campaignId == null) { "长期贴纸不支持活动参数，请导入无活动的固定名片" }
        return result
    }

    fun shortUrl(request: ImportRequest, sticker: Boolean = false): String {
        validCode(request.code)
        require(!sticker || request.campaignId == null) { "长期贴纸不能包含活动" }
        return "$base/c/${encode(request.code)}?s=nfc" + (request.campaignId?.let { "&e=$it" } ?: "")
    }

    fun normalShareUrl(request: ImportRequest): String {
        validCode(request.code)
        return "$base/c/${encode(request.code)}?s=link" + (request.campaignId?.let { "&e=$it" } ?: "")
    }

    fun previewUrl(request: ImportRequest): URI = URI("$base/api/v1/public/cards/${encode(validCode(request.code))}" +
        (request.campaignId?.let { "?e=$it" } ?: ""))

    fun sameOrigin(uri: URI): Boolean = uri.scheme == "https" && uri.host.equals(base.host, true) &&
        uri.port == -1 && uri.rawUserInfo == null

    fun isAllowedPreviewRedirect(uri: URI, request: ImportRequest): Boolean =
        sameOrigin(uri) && uri.rawPath == previewUrl(request).rawPath && uri.rawQuery == previewUrl(request).rawQuery && uri.rawFragment == null

    private fun validCode(code: String): String {
        require(code.matches(Regex("[A-Za-z0-9_-]{1,32}"))) { "名片 code 不合法" }
        return code
    }
    private fun campaign(value: String?): Long? = value?.let {
        require(it.matches(Regex("[1-9][0-9]{0,18}"))) { "活动参数不合法" }
        it.toLongOrNull()?.also { id -> require(id > 0) } ?: throw IllegalArgumentException("活动参数超出范围")
    }
    private fun query(raw: String?): Map<String, String> {
        if (raw == null) return emptyMap()
        require(raw.isNotEmpty()) { "查询参数为空" }
        val values = linkedMapOf<String, String>()
        raw.split('&').forEach { pair ->
            val parts = pair.split('=', limit = 2)
            require(parts.size == 2 && parts[0].isNotEmpty()) { "查询参数不合法" }
            val key = decode(parts[0])
            require(!values.containsKey(key)) { "不允许重复参数" }
            values[key] = decode(parts[1])
        }
        return values
    }
    private fun decode(value: String) = URLDecoder.decode(value, UTF_8.name())
    private fun encode(value: String) = URLEncoder.encode(value, UTF_8.name()).replace("+", "%20")
}
