package cn.aicardhub.nfc

import android.app.Activity
import android.app.AlertDialog
import android.content.BroadcastReceiver
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.PackageManager
import android.nfc.NdefMessage
import android.nfc.NfcAdapter
import android.nfc.Tag
import android.nfc.TagLostException
import android.nfc.cardemulation.CardEmulation
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Build
import android.net.Uri
import android.provider.Settings
import android.view.WindowManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import cn.aicardhub.nfc.core.ImportMode
import cn.aicardhub.nfc.core.ImportRequest
import cn.aicardhub.nfc.core.NdefUri
import cn.aicardhub.nfc.core.NfcMode
import cn.aicardhub.nfc.core.TrustedLinks
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean
import java.time.Duration
import java.time.Instant

/** Minimal native controls. Importing or previewing never starts RF or writes a tag. */
class MainActivity : Activity(), NfcAdapter.ReaderCallback {
    private val links = TrustedLinks(BuildConfig.PUBLIC_BASE_URL)
    private val client = PublicCardClient(links)
    private val worker = Executors.newSingleThreadExecutor()
    private val handler = Handler(Looper.getMainLooper())
    private val busyTag = AtomicBoolean(false)
    private val controller = SessionStore.controller
    private lateinit var input: EditText
    private lateinit var status: TextView
    private lateinit var previewText: TextView
    private lateinit var modeText: TextView
    private var adapter: NfcAdapter? = null
    private var request: ImportRequest? = null
    private var preview: PublicPreview? = null
    private var resumed = false
    @Volatile private var revision = 0L
    @Volatile private var modeToken = -1L
    private var confirmation: AlertDialog? = null
    private var readUrl: String? = null
    private val service by lazy { ComponentName(this, CardEmulationService::class.java) }
    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) { stop("屏幕已关闭，NFC 操作已结束") }
    }
    private val ticker = object : Runnable {
        override fun run() {
            if (!resumed) return
            val current = controller.current()
            modeText.text = "模式：${current.name.lowercase()} · 剩余 ${controller.remainingMs() / 1000} 秒"
            if (current != NfcMode.IDLE && !SessionStore.deviceReady(this@MainActivity)) stop("请保持亮屏并解锁")
            else if (current == NfcMode.IDLE && modeToken >= 0) stop("本次操作已结束")
            handler.postDelayed(this, 500)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        adapter = NfcAdapter.getDefaultAdapter(this)
        val column = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(24, 32, 24, 24) }
        setContentView(ScrollView(this).apply { addView(column) })
        fun text(value: String) = TextView(this).also { it.text = value; it.setPadding(0, 12, 0, 12); column.addView(it) }
        text("数科 NFC 助手 · 测试候选 ${BuildConfig.VERSION_NAME}")
        text("安卓可模拟名片、读写 NDEF 贴纸；iPhone 可接收。请保持助手前台、亮屏、解锁。每次最多 5 分钟。")
        input = EditText(this).apply { hint = "粘贴 NFC 配置链接或 s=nfc 公开短链"; inputType = 17; maxLines = 4; column.addView(this) }
        fun button(label: String, action: () -> Unit) { column.addView(Button(this).apply { this.text = label; setOnClickListener { action() } }) }
        button("导入并核对公开名片") { import(input.text.toString()) }
        previewText = text("尚未导入。助手不保存员工账号或登录凭据。")
        status = text("准备就绪")
        modeText = text("模式：idle")
        button("开启手机模拟（再次联网核对）") { prepare(NfcMode.EMULATE) }
        button("写入长期贴纸（无活动）") { prepare(NfcMode.WRITE) }
        button("主动读取 NDEF 标签") { beginRead() }
        button("结束当前操作") { stop("已手动结束") }
        button("打开系统 NFC 设置") { startActivity(Intent(Settings.ACTION_NFC_SETTINGS)) }
        button("系统分享公开链接") { request?.let { share(links.normalShareUrl(it)) } ?: show("请先导入名片") }
        button("打开刚读取的受信任名片网址") { readUrl?.let { startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(it))) } ?: show("请先主动读取受信任 NFC 名片") }
        text("贴纸写入前会显示已有内容；请持续贴紧直到回读完成。暂不支持非 NDEF 标签，不提供永久锁卡。NFC 读取成功不代表对方网页已经打开。")
        text("钱包/其他 HCE 应用可能抢占路由；助手仅在前台请求优先，不要求设为默认支付应用。无法使用时请回员工 H5 使用二维码或链接。")
        if (Build.VERSION.SDK_INT >= 33) registerReceiver(screenReceiver, IntentFilter(Intent.ACTION_SCREEN_OFF), RECEIVER_NOT_EXPORTED)
        else registerReceiver(screenReceiver, IntentFilter(Intent.ACTION_SCREEN_OFF))
        intent?.dataString?.let { input.setText(it) }
    }
    override fun onNewIntent(intent: Intent) { super.onNewIntent(intent); setIntent(intent); intent.dataString?.let { input.setText(it); import(it) } }
    override fun onResume() {
        super.onResume(); resumed = true; controller.setForeground(true)
        SessionStore.onRead = { handler.post { if (resumed) show("链接已被读取；是否打开网页取决于接收方") } }
        handler.post(ticker)
        if (request == null && input.text.isNotBlank()) import(input.text.toString())
    }
    override fun onPause() { resumed = false; stop("离开前台，操作已结束"); controller.setForeground(false); SessionStore.onRead = null; handler.removeCallbacks(ticker); super.onPause() }
    override fun onDestroy() { unregisterReceiver(screenReceiver); worker.shutdownNow(); super.onDestroy() }

    private fun import(value: String) {
        stop("正在联网核对…"); readUrl = null; preview = null; request = null; previewText.text = "核对中…"
        val parsed = try { links.parse(value) } catch (error: Exception) { show(error.message ?: "链接无效"); return }
        val version = revision
        background(version, { client.load(parsed) }) { result ->
            request = parsed; preview = result
            previewText.text = "${result.name}\n${result.company}\n${links.shortUrl(parsed)}\n" +
                (result.campaign?.let { "临时活动：$it\n结束时间：${result.expiresAt}" } ?: "固定名片，无活动")
            show(if (parsed.mode == ImportMode.WRITE) "请核对以上公开内容，再选择写入长期贴纸" else "请核对以上公开内容，再选择操作")
        }
    }

    private fun prepare(next: NfcMode) {
        stop("正在重新核对名片状态…"); readUrl = null
        val selected = request ?: return show("请先导入并核对名片")
        if (preview == null) return show("名片尚未完成核对")
        if (next == NfcMode.WRITE && selected.campaignId != null) return show("长期贴纸不能带活动，请导入无活动固定链接")
        if (!hardware(next == NfcMode.EMULATE)) return
        val version = revision
        background(version, { client.load(selected) }) { result ->
            preview = result
            val label = if (next == NfcMode.EMULATE) "开始限时模拟" else "开始等待贴纸"
            confirmation = AlertDialog.Builder(this).setTitle("确认公开名片")
                .setMessage("${result.name}\n${result.company}\n${links.shortUrl(selected)}\n${result.campaign ?: "固定名片"}\n请核对后操作。")
                .setNegativeButton("取消", null).setPositiveButton(label) { _, _ ->
                    if (resumed && version == revision && SessionStore.deviceReady(this)) begin(next, selected)
                }.show()
        }
    }
    private fun hardware(hce: Boolean): Boolean {
        if (adapter == null) { show("设备不支持 NFC，请使用 H5 二维码或链接"); return false }
        if (adapter?.isEnabled != true) { show("请先打开系统 NFC 开关"); return false }
        if (!SessionStore.deviceReady(this)) { show("请保持亮屏并解锁"); return false }
        if (hce && !packageManager.hasSystemFeature(PackageManager.FEATURE_NFC_HOST_CARD_EMULATION)) {
            show("此设备不支持 HCE 手机模拟，仍可读取或写入贴纸"); return false
        }
        return true
    }
    private fun begin(next: NfcMode, selected: ImportRequest? = null) {
        try {
            if (!hardware(next == NfcMode.EMULATE)) return
            val bytes = if (next == NfcMode.EMULATE) NdefUri.encode(links.shortUrl(selected!!)) else null
            val duration = if (next == NfcMode.EMULATE) preview?.expiresAt?.let { Duration.between(Instant.now(), it).toMillis() }
                ?: cn.aicardhub.nfc.core.ModeController.MAX_SESSION_MS else cn.aicardhub.nfc.core.ModeController.MAX_SESSION_MS
            require(duration > 0) { "活动已结束，请重新导入" }
            modeToken = controller.start(next, bytes, duration)
            window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
            if (next == NfcMode.EMULATE) {
                val preferred = CardEmulation.getInstance(adapter).setPreferredService(this, service)
                if (!preferred) { stop("无法取得 HCE 前台优先权，请检查钱包或其他 NFC 应用"); return }
                show("已准备好，请将接收方手机靠近天线。最多 5 分钟")
            } else {
                adapter?.enableReaderMode(this, this, NfcAdapter.FLAG_READER_NFC_A or NfcAdapter.FLAG_READER_NFC_B or NfcAdapter.FLAG_READER_NO_PLATFORM_SOUNDS, null)
                show(if (next == NfcMode.READ) "请靠近标签以读取" else "请贴紧可写 NDEF 贴纸，先读取已有内容")
            }
        } catch (error: Exception) { stop("无法开始：${error.message}") }
    }
    private fun beginRead() { stop("准备读取"); readUrl = null; if (hardware(false)) begin(NfcMode.READ) }
    private fun stop(message: String) {
        revision++; controller.stop(); modeToken = -1; confirmation?.dismiss(); confirmation = null; busyTag.set(false)
        runCatching { adapter?.disableReaderMode(this) }
        if (packageManager.hasSystemFeature(PackageManager.FEATURE_NFC_HOST_CARD_EMULATION)) runCatching { adapter?.let { CardEmulation.getInstance(it).unsetPreferredService(this) } }
        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
        if (::status.isInitialized) show(message)
    }
    override fun onTagDiscovered(tag: Tag) {
        if (!busyTag.compareAndSet(false, true)) return
        val token = modeToken; val mode = controller.current(); val version = revision
        worker.execute {
            try {
                if (!controller.isCurrent(token, mode) || mode !in setOf(NfcMode.READ, NfcMode.WRITE)) return@execute
                val found = StickerIo.inspect(tag)
                handler.post {
                    if (!resumed || version != revision || !controller.isCurrent(token, mode)) { busyTag.set(false); return@post }
                    if (mode == NfcMode.READ) {
                        readUrl = runCatching { links.shortUrl(links.parse(found.display)) }.getOrNull()
                        busyTag.set(false); stop("读取完成（未打开网页）：\n${found.display}\n容量 ${found.capacity} 字节" +
                            if (readUrl != null) "\n可点击“打开刚读取的受信任名片网址”" else "\n不是受信任名片网址，仅供诊断")
                    }
                    else if (!found.writable) { busyTag.set(false); stop("标签为只读，不能写入；已有内容：\n${found.display}") }
                    else confirmWrite(tag, found, token, version)
                }
            } catch (error: Exception) { busyTag.set(false); handler.post { if (version == revision) stop(tagError(error)) } }
        }
    }
    private fun confirmWrite(tag: Tag, found: TagInspection, token: Long, version: Long) {
        val selected = request ?: run { busyTag.set(false); return }
        val uri = links.shortUrl(selected, sticker = true)
        val message = NdefMessage(NdefUri.encode(uri))
        confirmation = AlertDialog.Builder(this).setTitle(if (found.original == null) "确认写入空标签" else "确认覆盖已有内容")
            .setMessage("已有内容：\n${found.display}\n\n目标：${preview?.name} · ${preview?.company}\n$uri\n需要 ${message.toByteArray().size} 字节 / 容量 ${found.capacity} 字节\n保持贴紧，写入后会回读。失败时内容可能已变化。")
            .setNegativeButton("取消") { _, _ -> busyTag.set(false); stop("已取消，未执行写入") }
            .setOnCancelListener { busyTag.set(false); stop("已取消，未执行写入") }
            .setPositiveButton("确认写入") { _, _ -> worker.execute {
                try {
                    StickerIo.writeAndVerify(tag, found, message, uri,
                        { controller.isCurrent(token, NfcMode.WRITE) && SessionStore.deviceReady(this) },
                        { controller.verify(token) && SessionStore.deviceReady(this) })
                    handler.post { if (version == revision) stop("写入完成，实时回读字节与 URI 完全一致") }
                } catch (error: Exception) { handler.post { if (version == revision) stop(tagError(error)) } }
                finally { busyTag.set(false) }
            } }.show()
    }
    private fun tagError(error: Exception) = when (error) {
        is TagLostException -> "标签移开过早，未完成回读；内容可能已变化，请重新读取"
        is java.io.IOException -> "标签通信失败，内容可能已变化，请保持贴紧并重新读取"
        else -> error.message ?: "NFC 操作失败，请重新读取标签"
    }
    private fun <T> background(version: Long, operation: () -> T, success: (T) -> Unit) {
        worker.execute {
            try { val result = operation(); handler.post { if (resumed && version == revision) success(result) } }
            catch (error: Exception) { handler.post { if (resumed && version == revision) show(error.message ?: "网络核对失败，请重试") } }
        }
    }
    private fun show(message: String) { status.text = message }
    private fun share(url: String) = startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).apply { type = "text/plain"; putExtra(Intent.EXTRA_TEXT, url) }, "分享公开名片链接"))
}
