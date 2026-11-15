package cn.aicardhub.nfc

import cn.aicardhub.nfc.core.ImportRequest
import cn.aicardhub.nfc.core.TrustedLinks
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URI
import java.time.Instant
import java.io.ByteArrayOutputStream

data class PublicPreview(val name: String, val company: String, val campaign: String?, val expiresAt: Instant?)

/** Called only on the dedicated background executor. No auth, cookies, visits or arbitrary destinations. */
class PublicCardClient(private val links: TrustedLinks) {
    fun load(request: ImportRequest): PublicPreview {
        var target = links.previewUrl(request)
        repeat(3) {
            val connection = target.toURL().openConnection() as HttpURLConnection
            try {
                connection.instanceFollowRedirects = false
                connection.connectTimeout = 10_000; connection.readTimeout = 10_000
                connection.setRequestProperty("Accept", "application/json")
                connection.setRequestProperty("Cache-Control", "no-cache")
                val code = connection.responseCode
                if (code in 300..399) {
                    val location = connection.getHeaderField("Location") ?: error("服务器返回无效跳转")
                    val redirect = target.resolve(URI(location))
                    require(links.isAllowedPreviewRedirect(redirect, request)) { "已拒绝跳转到其他站点或路径" }
                    target = redirect
                } else {
                    require(code == 200) { "无法核对名片或活动（HTTP $code），请重试或导入无活动链接" }
                    val body = connection.inputStream.use { stream ->
                        val output = ByteArrayOutputStream()
                        val chunk = ByteArray(4096)
                        while (true) {
                            val count = stream.read(chunk)
                            if (count < 0) break
                            require(output.size() + count <= 262_144) { "名片响应过大" }
                            output.write(chunk, 0, count)
                        }
                        output.toString(Charsets.UTF_8.name())
                    }
                    val json = JSONObject(body)
                    require(json.getString("code") == request.code && json.getString("status") == "active") { "名片已停用或不匹配，不能操作" }
                    val campaign = json.optJSONObject("campaign")
                    val expiry = if (request.campaignId != null) {
                        require(campaign != null && campaign.getLong("id") == request.campaignId) { "活动无效，不能操作" }
                        val start = Instant.parse(campaign.getString("start_at"))
                        val end = Instant.parse(campaign.getString("end_at"))
                        require(!Instant.now().isBefore(start) && Instant.now().isBefore(end)) { "活动未开始或已结束" }
                        end
                    } else null
                    return PublicPreview(json.getString("name"), json.getJSONObject("company").getString("name"),
                        campaign?.optString("name"), expiry)
                }
            } finally { connection.disconnect() }
        }
        error("名片服务跳转过多")
    }
}
